#!/usr/bin/env python3
"""
Scan skill markdown files for `uip <verb>` references and verify each one
against the CLI catalog at assets/uip-catalog-snapshot.json.

How it works:
  1. For each .md file under skills/, find every line containing `uip ` and
     extract the token sequence that follows.
  2. Walk tokens until hitting a flag (`-x`, `--xxx`), shell operator, or
     end-of-line. Placeholder tokens (`<arg>`, `[arg]`, `$VAR`, `...`) are
     treated as wildcards — they break the verb path but don't disqualify
     the prefix before them.
  3. Match the leading literal-token prefix against the catalog. The longest
     prefix that is a real verb wins. If no literal token matches, the
     reference is reported as a finding.

Outputs:
  - Default: one finding per line, human-readable.
  - --json : newline-delimited JSON for downstream tooling.

Usage:
    python3 scripts/check-skill-verbs.py skills/
    python3 scripts/check-skill-verbs.py --json skills/uipath-rpa/SKILL.md ...
"""

import argparse
import collections
import datetime as dt
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "assets" / "uip-catalog-snapshot.json"

# `uip` followed by at least one space, then the rest of the line up to a
# code-block end backtick or newline.
UIP_LINE = re.compile(r"\buip(\s+[^\n`]*)?")

# Tokens that look like placeholders or non-verb content.
PLACEHOLDER = re.compile(r"^(<.+?>|\[.+?\]|\$\{?[A-Za-z_]\w*\}?|\.\.\.|\*+)$")
# Tokens that start a flag — stop verb extraction here.
FLAG = re.compile(r"^-{1,2}[A-Za-z]")
# Shell operators / control characters that end a command segment.
SHELL_STOP = {"|", "||", "&&", ";", ">", ">>", "<", "2>", "2>&1"}
# Strip trailing punctuation that markdown formatting can leave behind.
TRAILING_PUNCT = re.compile(r"[`,.;:)\]\"'\\]+$")
LEADING_PUNCT = re.compile(r"^[`(\[\"']+")
# Common prose tokens that follow `uip` in English sentences ("the uip CLI ...",
# "uip is great", "uip a tool"). A reference whose first token is one of these
# cannot be a verb regardless of what comes after.
PROSE_NOISE = {"CLI", "is", "a", "the", "an", "and", "or", "to", "for", "with"}


def load_catalog():
    if not CATALOG_PATH.exists():
        sys.exit(f"Catalog not found at {CATALOG_PATH}. "
                 "Run scripts/build-uip-catalog.py first.")
    data = json.loads(CATALOG_PATH.read_text())
    return (
        set(data["verbs"]),
        set(data.get("unwalkable_groups", [])),
        data.get("cli_version", "unknown"),
    )


def clean_token(tok):
    tok = TRAILING_PUNCT.sub("", tok)
    tok = LEADING_PUNCT.sub("", tok)
    return tok


def extract_verb_tokens(tail):
    """
    Given the text after `uip`, return the list of literal verb tokens
    leading up to the first flag/placeholder/shell-stop, or [] if the line
    has no usable verb path.
    """
    tail = tail.strip()
    if not tail:
        return []
    # Cut at obvious end-of-statement markers.
    for stop in ["\\\n", "\n"]:
        if stop in tail:
            tail = tail.split(stop, 1)[0]
    raw_tokens = tail.split()
    verb = []
    for raw in raw_tokens:
        tok = clean_token(raw)
        if not tok:
            break
        if FLAG.match(tok):
            break
        if tok in SHELL_STOP:
            break
        if PLACEHOLDER.match(tok):
            # Placeholder — stop here. Whatever came before is the verb.
            break
        # Reject things that clearly aren't verbs: paths, JSON snippets,
        # filenames, quoted strings.
        if any(ch in tok for ch in "/={}\"'"):
            break
        # Stop if the token starts looking like a value (digits-only).
        if tok.replace("-", "").replace("_", "").isdigit():
            break
        verb.append(tok)
    return verb


def best_prefix(tokens, catalog):
    """Return the longest token prefix that exists in the catalog, or None."""
    for n in range(len(tokens), 0, -1):
        prefix = " ".join(tokens[:n])
        if prefix in catalog:
            return prefix
    return None


def scan_file(path, catalog, unwalkable):
    """Yield findings with severity (Stale|Uncertain)."""
    findings = []
    try:
        text = path.read_text()
    except (UnicodeDecodeError, OSError) as exc:
        print(f"warning: cannot read {path}: {exc}", file=sys.stderr)
        return findings
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in UIP_LINE.finditer(line):
            tail = match.group(1) or ""
            tokens = extract_verb_tokens(tail)
            if not tokens:
                continue
            verb_path = " ".join(tokens)
            match_str = best_prefix(tokens, catalog)
            if match_str == verb_path:
                continue  # exact catalog hit
            # Prose noise: `the uip CLI ...`, `uip is a tool`, etc. The first
            # token after `uip` is an English word that can't possibly be a
            # verb. Filter regardless of how many tokens follow — the bug
            # this guards against was only firing on single-token tails.
            if match_str is None and tokens[0] in PROSE_NOISE:
                continue
            # Severity: if any catalog prefix sits under an unwalkable group,
            # we cannot verify the rest of the path — call it Uncertain.
            severity = "Stale"
            for n in range(len(tokens), 0, -1):
                if " ".join(tokens[:n]) in unwalkable:
                    severity = "Uncertain"
                    break
            findings.append({
                "line": lineno,
                "verb_path": verb_path,
                "matched_prefix": match_str,
                "severity": severity,
                "context": line.strip(),
            })
    return findings


def iter_markdown(roots):
    for root in roots:
        root = Path(root)
        if root.is_file() and root.suffix == ".md":
            yield root
            continue
        if root.is_dir():
            for p in sorted(root.rglob("*.md")):
                yield p


def _aggregate(findings):
    """Split findings by severity and compute Counter rollups."""
    stale = [f for f in findings if f["severity"] == "Stale"]
    uncertain = [f for f in findings if f["severity"] == "Uncertain"]
    by_verb = collections.Counter(f["verb_path"] for f in stale)
    by_file = collections.Counter(f["path"] for f in stale)
    by_skill = collections.Counter()
    for f in stale:
        parts = Path(f["path"]).parts
        if len(parts) >= 2 and parts[0] == "skills":
            by_skill[parts[1]] += 1
    return stale, uncertain, by_verb, by_file, by_skill


def write_report(findings, catalog, unwalkable, version, output_path):
    """Render Stale/Uncertain findings to a markdown audit report."""
    stale, uncertain, by_verb, by_file, by_skill = _aggregate(findings)

    verbs_set = set(catalog)

    def suggest(verb):
        parts = verb.split()
        if len(parts) < 2:
            return None
        root = " ".join(parts[:-1])
        siblings = sorted(v for v in verbs_set if v.startswith(root + " "))
        if siblings:
            return siblings
        if len(parts) >= 3:
            root2 = " ".join(parts[:-2])
            siblings = sorted(v for v in verbs_set
                              if v.startswith(root2 + " "))
            if siblings:
                return siblings[:4]
        return None

    now = dt.datetime.now(dt.timezone.utc).isoformat(
        timespec="seconds").replace("+00:00", "Z")
    out = [
        "# Skill CLI Verb Audit\n",
        f"*Generated: {now}*  ",
        f"*Catalog: uip {version} — {len(catalog)} verbs, "
        f"{len(unwalkable)} unwalkable groups "
        f"({', '.join(sorted(unwalkable))})*\n",
        "Generated by `scripts/check-skill-verbs.py --report` against `.md` "
        "files under `skills/`.\n",
        "- **Stale** — verb path does not match any catalog entry, and no "
        "part of the path falls under an unwalkable group. Agents "
        "copy-pasting from the skill will hit `unknown command`.",
        "- **Uncertain** — verb path starts with an unwalkable-group prefix. "
        "Cannot be verified statically.\n",
        "## Summary\n",
        "| Severity | Findings | Unique verbs | Files affected |",
        "|---|---|---|---|",
        f"| **Stale** | {len(stale)} | {len(by_verb)} | {len(by_file)} |",
        f"| **Uncertain** | {len(uncertain)} | "
        f"{len({f['verb_path'] for f in uncertain})} | "
        f"{len({f['path'] for f in uncertain})} |\n",
        "## Top stale verb paths\n",
        "| Count | Verb path | Likely replacement |",
        "|---|---|---|",
    ]
    for verb, n in by_verb.most_common(40):
        s = suggest(verb)
        rep = " or ".join(f"`{x}`" for x in s[:3]) if s else "—"
        out.append(f"| {n} | `{verb}` | {rep} |")
    out.append("")
    out.append("## Stale findings by skill\n")
    out.append("| Skill | Stale findings |\n|---|---|")
    for skill, n in sorted(by_skill.items(), key=lambda x: -x[1]):
        out.append(f"| `{skill}` | {n} |")
    out.append("")
    out.append("## Files with the most stale findings\n")
    out.append("| Count | File |\n|---|---|")
    for path, n in by_file.most_common(20):
        out.append(f"| {n} | `{path}` |")
    out.append("")
    out.append("## All stale findings\n")
    out.append("Grouped by file, ordered by line number.\n")
    by_path = collections.defaultdict(list)
    for f in stale:
        by_path[f["path"]].append(f)
    for path in sorted(by_path):
        out.append(f"### `{path}`\n")
        for f in sorted(by_path[path], key=lambda x: x["line"]):
            ctx = f["context"][:120].replace("|", "\\|")
            matched = f["matched_prefix"] or "(none)"
            out.append(f"- L{f['line']} — verb: `{f['verb_path']}`  ")
            out.append(f"  context: `{ctx}`  ")
            out.append(f"  longest catalog prefix: `{matched}`")
        out.append("")
    if uncertain:
        out.append("## Uncertain findings\n")
        unc_by_verb = collections.Counter(f["verb_path"] for f in uncertain)
        out.append(f"{len(uncertain)} references under unwalkable groups "
                   f"({', '.join(sorted(unwalkable))}). Cannot be verified "
                   "until the tool exposes JSON help.\n")
        out.append("Top verb paths:\n")
        out.append("| Count | Verb path |\n|---|---|")
        for verb, n in unc_by_verb.most_common(20):
            out.append(f"| {n} | `{verb}` |")
        out.append("")
    out.append("## Reproducing\n")
    out.append(f"```bash\npython3 scripts/check-skill-verbs.py "
               f"--report {output_path} skills/\n```\n")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(out))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path,
                        help="Files or directories to scan (e.g. skills/)")
    parser.add_argument("--json", action="store_true",
                        help="Emit newline-delimited JSON instead of text")
    parser.add_argument("--report", type=Path, metavar="PATH",
                        help="Write a markdown audit report to PATH "
                             "(suppresses stdout text output)")
    args = parser.parse_args()

    catalog, unwalkable, version = load_catalog()

    all_findings = []
    for path in iter_markdown(args.paths):
        for f in scan_file(path, catalog, unwalkable):
            f["path"] = str(path)
            all_findings.append(f)

    if args.report:
        write_report(all_findings, catalog, unwalkable, version, args.report)
        stale_n = sum(1 for f in all_findings if f["severity"] == "Stale")
        unc_n = sum(1 for f in all_findings if f["severity"] == "Uncertain")
        print(f"wrote {args.report} ({stale_n} Stale, {unc_n} Uncertain)")
        return 1 if stale_n else 0

    if args.json:
        for f in all_findings:
            print(json.dumps(f))
        return 0

    stale, uncertain, by_verb, by_file, _ = _aggregate(all_findings)

    if not stale and not uncertain:
        print(f"OK — no stale uip verbs found (catalog: uip {version}, "
              f"{len(catalog)} verbs).")
        return 0

    print(f"{len(stale)} Stale, {len(uncertain)} Uncertain findings "
          f"(catalog: uip {version}, {len(catalog)} verbs, "
          f"{len(unwalkable)} unwalkable groups)\n")
    if stale:
        print("Top stale verb paths:")
        for verb, n in by_verb.most_common(20):
            print(f"  {n:3d}  {verb}")
        print("\nFiles with most stale findings:")
        for path, n in by_file.most_common(15):
            print(f"  {n:3d}  {path}")
    if uncertain:
        print(f"\n{len(uncertain)} Uncertain findings under unwalkable groups "
              f"({', '.join(sorted(unwalkable))}) — not counted as stale.")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
