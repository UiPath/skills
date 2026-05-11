#!/bin/bash
# Verify every `uip` command referenced in this skill's markdown actually exists.
# Usage: bash .maintenance/check-uip-commands.sh [--strict] [file1.md ...]
# Output: BAD lines per unknown command, then "commands_checked=N unknown=M" summary.
#
# Scans fenced code blocks (```bash, ```sh, ```shell, ```zsh, ```console, or
# unlabelled ```) under this skill for lines that begin with `uip `, extracts
# the command path (tokens before the first flag, placeholder, or shell
# metachar), and verifies it against `uip <path> --help`. Help output only —
# no command is ever executed for real.
#
# How verification works: `uip <bogus> --help` silently falls back to the
# parent's help, so exit code is not a reliable signal. Instead, we walk the
# path level by level and confirm each next segment appears in the parent's
# `Subcommands[].Name` list. Help responses are cached per prefix.
#
# Skips:
# - Inline backtick references like `uip ...` (only fenced blocks are scanned)
# - Files matching --skip-glob
#
# --strict: exit 2 if `uip` is not on PATH (CI mode). Default: warn and exit 0.
#
# Exits non-zero if any unknown command is referenced.

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

STRICT=0
FILES=()
for arg in "$@"; do
  case "$arg" in
    --strict) STRICT=1 ;;
    *) FILES+=("$arg") ;;
  esac
done

if ! command -v uip >/dev/null 2>&1; then
  if [ "$STRICT" -eq 1 ]; then
    echo "uip not found on PATH (--strict)" >&2
    exit 2
  fi
  echo "uip not found on PATH; skipping (use --strict to fail)" >&2
  echo ""
  echo "commands_checked=0 unknown=0"
  exit 0
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found on PATH" >&2
  exit 2
fi

if [ "${#FILES[@]}" -eq 0 ]; then
  # Scan the skill's published surface only: SKILL.md + references/.
  # Skips .maintenance/, scratch files at the skill root (PLAN.md, PR_BODY.md),
  # and anything else that isn't part of what agents load.
  while IFS= read -r f; do
    FILES+=("$f")
  done < <({ [ -f SKILL.md ] && echo "./SKILL.md"; /usr/bin/find ./references -type f -name '*.md' 2>/dev/null; } | /usr/bin/sort)
fi

if [ "${#FILES[@]}" -eq 0 ]; then
  echo ""
  echo "commands_checked=0 unknown=0"
  exit 0
fi

export UIP_BIN="$(command -v uip)"
export SKILL_ROOT="$ROOT"

python3 - "${FILES[@]}" <<'PYEOF'
import json
import os
import re
import subprocess
import sys
from pathlib import Path

UIP = os.environ["UIP_BIN"]
SKILL_ROOT = Path(os.environ["SKILL_ROOT"])
files = [Path(p) for p in sys.argv[1:]]

# Cache value: (subcommands_set, takes_positional_args) or None for invalid prefix
_help_cache: dict[tuple, tuple[set, bool] | None] = {}


def get_help(prefix):
    if prefix in _help_cache:
        return _help_cache[prefix]
    # `--output json` is required: top-level `uip --help` defaults to plain
    # text; other levels default to JSON but accept the flag too. Forcing it
    # makes parsing deterministic.
    cmd = [UIP, *prefix, "--help", "--output", "json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except Exception:
        _help_cache[prefix] = None
        return None
    # uip prints non-JSON noise around the help payload — sometimes a banner
    # before (e.g. `Tool factory already registered ...`), sometimes a human
    # usage block after. Use raw_decode to grab the first complete JSON object.
    out = proc.stdout
    brace = out.find("{")
    if brace < 0:
        _help_cache[prefix] = None
        return None
    try:
        data, _ = json.JSONDecoder().raw_decode(out[brace:])
    except json.JSONDecodeError:
        _help_cache[prefix] = None
        return None
    inner = data.get("Data", {})
    resolved = inner.get("Command", "")
    expected = prefix[-1] if prefix else "uip"
    if resolved != expected:
        _help_cache[prefix] = None
        return None
    subs = set()
    for entry in inner.get("Subcommands", []) or []:
        name = entry.get("Name", "")
        leaf = name.split(None, 1)[0]
        if leaf:
            subs.add(leaf)
    takes_args = bool(inner.get("Arguments"))
    _help_cache[prefix] = (subs, takes_args)
    return _help_cache[prefix]


def verify_path(path):
    prefix = ()
    for seg in path:
        info = get_help(prefix)
        if info is None:
            return False, prefix[-1] if prefix else seg, []
        subs, takes_args = info
        if seg not in subs:
            # If the parent is a leaf (no subcommands) and accepts positional
            # args, this token is an arg — path is valid up to here.
            if not subs and takes_args:
                return True, "", []
            import difflib
            return False, seg, difflib.get_close_matches(seg, sorted(subs), n=3, cutoff=0.5)
        prefix = prefix + (seg,)
    return True, "", []


FENCE_RE = re.compile(r"^```([a-zA-Z0-9_+-]*)\s*$")
ACCEPTED_LANGS = {"", "bash", "sh", "shell", "zsh", "console"}
# Inline single-backtick spans. Greedy is fine: ` cannot appear inside a
# single-backtick span by definition (use double-backtick spans for that, which
# we deliberately don't scan — they're rare and usually contain code samples).
INLINE_RE = re.compile(r"`([^`\n]+)`")
# Per-line opt-out marker: `<!-- uip-check-skip -->` anywhere on the line
# suppresses checking for that line. Used for intentional historical references
# (e.g. CLI version-comparison tables that document a removed prefix). For
# table rows, place the marker inside a cell (e.g. `| ... | ... <!-- uip-check-skip --> |`)
# so it doesn't break table structure — HTML comments render as nothing.
SKIP_MARKER = "<!-- uip-check-skip -->"


SUBCOMMAND_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def is_terminator(tok):
    # A real uip subcommand is a lowercase kebab-case identifier. Anything else
    # (flags, placeholders, paths, comments, quoted strings, shell metachars,
    # positional args) ends the path.
    if not tok:
        return True
    if tok.startswith("#"):
        return True
    if tok in {"|", ">", ">>", "<", "&&", "||", ";", "&", "$(", "`"}:
        return True
    return not SUBCOMMAND_RE.match(tok)


def extract_path_from_uip_line(content):
    """Tokenize a uip line and walk to extract the command path.

    Returns the path list (possibly empty for bare `uip`).
    Returns None if the line doesn't start with `uip`.
    """
    if content.startswith("$ "):
        content = content[2:]
    if not (content.startswith("uip ") or content.rstrip() == "uip"):
        return None
    tokens = content.split()
    path = []
    for tok in tokens[1:]:
        if is_terminator(tok):
            break
        path.append(tok)
    return path


def extract_uip_commands(md_path):
    try:
        text = md_path.read_text(encoding="utf-8")
    except Exception:
        return
    lines = text.splitlines()
    in_fence = False
    fence_lang = ""
    i = 0
    while i < len(lines):
        line = lines[i]
        m = FENCE_RE.match(line.strip())
        if m:
            if not in_fence:
                in_fence = True
                fence_lang = m.group(1).lower()
            else:
                in_fence = False
                fence_lang = ""
            i += 1
            continue
        if SKIP_MARKER in line:
            i += 1
            continue
        if in_fence:
            if fence_lang in ACCEPTED_LANGS:
                start = i
                joined = line
                while joined.rstrip().endswith("\\") and i + 1 < len(lines):
                    joined = joined.rstrip()[:-1] + " " + lines[i + 1]
                    i += 1
                path = extract_path_from_uip_line(joined.lstrip())
                if path:
                    yield (start + 1, path)
        else:
            # Inline backtick spans outside fenced blocks.
            for match in INLINE_RE.finditer(line):
                path = extract_path_from_uip_line(match.group(1).strip())
                if path:
                    yield (i + 1, path)
        i += 1


references = {}
for md in files:
    for line_no, path in extract_uip_commands(md):
        references.setdefault(tuple(path), []).append((md, line_no))

unknown = 0
for path_tuple, locs in sorted(references.items()):
    ok, bad, suggestions = verify_path(list(path_tuple))
    if ok:
        continue
    idx = list(path_tuple).index(bad) if bad in path_tuple else 0
    parent = "uip" + ("" if idx == 0 else " " + " ".join(path_tuple[:idx]))
    cmd_str = "uip " + " ".join(path_tuple)
    sug = f" (did you mean: {', '.join(suggestions)}?)" if suggestions else ""
    for f, ln in locs:
        try:
            rel = f.relative_to(SKILL_ROOT).as_posix()
        except ValueError:
            rel = str(f)
        print(f'BAD  {rel}:{ln}  {cmd_str} — "{bad}" not a subcommand of "{parent}"{sug}')
        unknown += 1

print()
print(f"commands_checked={len(references)} unknown={unknown}")
sys.exit(1 if unknown else 0)
PYEOF
