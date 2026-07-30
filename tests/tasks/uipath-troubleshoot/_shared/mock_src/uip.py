#!/usr/bin/env python3
"""Generic uip mock dispatcher.

Reads <script_dir>/r/manifest.json and dispatches each invocation to
the first matching rule's response file. All canned data lives in per-scenario
files under r/ (short dir names keep Windows paths under MAX_PATH); this
script is shared across scenarios and never
needs editing when a new scenario is added.

Every invocation is appended to <script_dir>/.log so post-run analysis can
compare expected vs performed commands and surface exploration the agent did
beyond the manifest's `expected_calls`. On sealed runs each record is written
zlib+base64-encoded (decode with `coverage_report.py --dump`) so the agent
cannot read its own call history and infer the CLI is mocked; unsealed local
runs keep plain JSONL for easy debugging.

Manifest schema (v2):
    {
      "version": 2,
      "rules": [
        { "match": "or jobs list", "file": "jobs_list.json" },
        { "match": "auth status",  "file": "auth_status.json", "exit_code": 0 },
        { "match": "docsai ask",   "passthrough": true }
      ],
      "expected_calls": [
        { "pattern": "or jobs get <key>", "min": 1, "description": "..." }
      ],
      "unmocked_default": {
        "response": "[]\n",
        "exit_code": 0
      }
    }

Each rule has one of:
    - `file: <path>` — return the canned response under r/<file>.
    - `passthrough: true` — proxy to the real `uip` CLI installed on the
      host. Responses are cached under r/_cache/<key>.json on
      first run; subsequent runs replay the cache. Cache files are
      committed alongside fixtures so tests stay reproducible offline.

Dispatch precedence:
    1. First matching rule (first match wins).
    2. `unmocked_default` — if set, return its `response` + `exit_code`.
    3. Otherwise, error on stderr (legacy behavior).

Matching (see `_rule_matches`) is token-aware, with a plain-substring
fallback. A rule matches an invocation when EITHER:

    a. every whitespace token of `match` is present among the invocation's
       tokens (order-independent), OR
    b. `match` is a literal substring of `" ".join(argv[1:])` (legacy).

Tokens are normalized before comparison: surrounding quotes are stripped
(`"<uuid>"` == `<uuid>`) and `--flag=value` is split into `--flag value`.
This makes rules robust to:
    - flag reordering  (`--folder-key K --state Faulted`
                         matches `--state Faulted --folder-key K`)
    - extra trailing flags (a `--output json` the rule omits)
    - shell-quoted job keys recorded into a manifest match string
      (a historical generate_scenario.py quirk).

List specific patterns before generic ones — first match still wins, and a
generic rule with fewer tokens will match a superset of invocations. A
passthrough rule with `match: "docsai ask"` is the typical way to proxy
open-ended natural-language commands.
"""

import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zlib
from pathlib import Path

# Sandboxes execute this file as a compressed docstring-stripped blob
# (`m/.uip.bin`, decoded and exec'd by the `m/uip` stub with __file__ set to
# the blob's path in the mock dir), so every data path (store, log, cache)
# anchors correctly both there and when running this source directly.
SCRIPT_DIR = Path(__file__).resolve().parent
RESPONSES_DIR = SCRIPT_DIR / "r"
MANIFEST_PATH = RESPONSES_DIR / "manifest.json"
CALL_LOG_PATH = SCRIPT_DIR / ".log"
# Passthrough (docsai) cache. Canonical location is beside the shim so it
# survives `m/seal` removing `r/`; fall back to the legacy `r/_cache` for
# unsealed local runs that shipped committed caches under `r/`.
CACHE_DIR = SCRIPT_DIR / "_cache"
LEGACY_CACHE_DIR = RESPONSES_DIR / "_cache"

# Sealed fixture store (written by `m/seal`). When present, the manifest and
# every response fixture are read from here — decoded in memory — and the
# readable `r/` directory no longer exists. Opaque on disk (zlib+base64), so
# `cat`-ing it reveals no evidence. `None` until first access; then either the
# decoded dict `{"manifest": ..., "files": {name: rawbytes}}` or the sentinel
# `_NO_STORE` (unsealed run → fall back to `r/`).
STORE_PATH = SCRIPT_DIR / ".store"
_NO_STORE = object()
_STORE: object = None


def _get_store():
    """Load and cache the sealed store, or ``_NO_STORE`` if unsealed.

    Decoded once per process. Returns a dict with ``manifest`` (dict) and
    ``files`` (name → raw ``bytes``), or ``_NO_STORE`` when there is no
    ``.store`` (the shim then reads ``r/`` as before).
    """
    global _STORE
    if _STORE is not None:
        return _STORE
    if not STORE_PATH.is_file():
        _STORE = _NO_STORE
        return _STORE
    blob = json.loads(zlib.decompress(base64.b64decode(STORE_PATH.read_bytes())).decode("utf-8"))
    _STORE = {
        "manifest": blob["manifest"],
        "files": {name: base64.b64decode(b64) for name, b64 in blob.get("files", {}).items()},
    }
    return _STORE


def _log_call(args: str, rule: dict | None, exit_code: int, error: str | None = None) -> None:
    """Append a structured record of this invocation to the call log.

    Best-effort: any logging error is swallowed so a broken log file never
    breaks an agent's command. The file is the source of truth for
    expected-vs-performed coverage analysis after the run.

    On sealed runs the record is zlib+base64-encoded: the log lives in the
    agent's working directory, and plain records (`matched_rule`, `fixture`)
    would reveal the CLI is mocked. Unsealed local runs keep plain JSONL.
    Decode with `coverage_report.py --dump`.
    """
    record = {
        "ts": time.time(),
        "args": args,
        "matched_rule": rule.get("match") if rule else None,
        "fixture": rule.get("file") if rule else None,
        "exit_code": exit_code,
    }
    if error:
        record["error"] = error
    line = json.dumps(record)
    if _get_store() is not _NO_STORE:
        line = base64.b64encode(zlib.compress(line.encode("utf-8"), 9)).decode("ascii")
    try:
        with CALL_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


# Pure-formatting flags that never change WHICH resource an invocation
# addresses. Dropped from both the match string and the invocation before
# token comparison, so a rule and an invocation that differ only by an
# `--output json` (present on one side, absent on the other) still match.
# `--output` takes a value (`--output json`), so its following token is
# dropped too.
_NOISE_VALUE_FLAGS = {"--output"}


def _tokenize(s: str) -> list[str]:
    """Split a command string into normalized tokens.

    Normalization:
        - surrounding single/double quotes stripped from each token, so a
          manifest match of `or jobs get "<uuid>"` tokenizes identically to
          the shell-stripped invocation `or jobs get <uuid>`.
        - `--flag=value` split into two tokens (`--flag`, `value`) so the
          equals-form and space-form of a flag compare equal.
        - pure-formatting flags in `_NOISE_VALUE_FLAGS` (and their values)
          dropped, so `--output json` never affects matching.
    """
    tokens: list[str] = []
    for raw in s.split():
        if raw.startswith("-") and "=" in raw:
            flag, _, val = raw.partition("=")
            tokens.append(flag.strip("\"'"))
            if val:
                tokens.append(val.strip("\"'"))
        else:
            tokens.append(raw.strip("\"'"))

    # Drop noise value-flags and the value token that follows each.
    cleaned: list[str] = []
    skip_next = False
    for tok in tokens:
        if skip_next:
            skip_next = False
            continue
        if tok in _NOISE_VALUE_FLAGS:
            skip_next = True
            continue
        cleaned.append(tok)
    return cleaned


def _rule_matches(match: str, args: str, arg_tokens: set[str]) -> bool:
    """Return True when `match` matches the invocation `args`.

    Token-subset first (order-independent, quote/flag-normalized), then a
    plain-substring fallback so any rule that matched under the old
    substring dispatcher keeps matching. Additive by construction: this
    never matches fewer invocations than the legacy substring test.
    """
    if not match:
        return False
    match_tokens = _tokenize(match)
    if match_tokens and all(t in arg_tokens for t in match_tokens):
        return True
    return match in args


def _err(payload: dict, code: int) -> int:
    sys.stderr.write(json.dumps(payload) + "\n")
    return code


def _has_doc_key(node: object) -> bool:
    """True when any dict anywhere in `node` carries an `_`-prefixed key."""
    if isinstance(node, dict):
        if any(isinstance(k, str) and k.startswith("_") for k in node):
            return True
        return any(_has_doc_key(v) for v in node.values())
    if isinstance(node, list):
        return any(_has_doc_key(v) for v in node)
    return False


def _prune_doc_keys(node: object) -> object:
    """Return `node` with every `_`-prefixed dict key removed, at any depth."""
    if isinstance(node, dict):
        return {
            k: _prune_doc_keys(v)
            for k, v in node.items()
            if not (isinstance(k, str) and k.startswith("_"))
        }
    if isinstance(node, list):
        return [_prune_doc_keys(v) for v in node]
    return node


def _strip_doc_keys(text: str) -> str:
    """Drop `_`-prefixed annotation keys (e.g. `_doc`, `_comment`, `_meta`) from a
    JSON fixture before it is emitted as `uip` stdout.

    Fixtures carry maintainer annotations that often state the scenario's root
    cause. The real CLI never emits such keys, and returning them verbatim would
    leak the answer into the agent's evidence. Strip them so the mocked stdout
    matches the shape of a real response.

    Recursive on purpose: annotations also appear nested inside the payload (a
    `_meta` block hung off `Data`, for instance), which a top-level-only pass
    would emit verbatim.

    Only re-serialize when such a key is actually present, so every other fixture
    (and any non-JSON body) passes through byte-for-byte unchanged.
    """
    try:
        doc = json.loads(text)
    except (ValueError, TypeError):
        return text
    if not _has_doc_key(doc):
        return text
    trailing = "\n" if text.endswith("\n") else ""
    return json.dumps(_prune_doc_keys(doc), indent=2, ensure_ascii=False) + trailing


def _cache_key(args: str) -> str:
    return hashlib.md5(args.encode("utf-8")).hexdigest()[:16]


def _load_cache(args: str) -> dict | None:
    """Return cached `{stdout, exit_code, args, cached_at}` or None."""
    key = f"{_cache_key(args)}.json"
    for path in (CACHE_DIR / key, LEGACY_CACHE_DIR / key):
        if not path.is_file():
            continue
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
    return None


def _save_cache(args: str, stdout: str, exit_code: int) -> None:
    """Persist a passthrough response so subsequent runs replay offline."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{_cache_key(args)}.json"
    payload = {
        "args": args,
        "stdout": stdout,
        "exit_code": exit_code,
        "cached_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    try:
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass


def _find_real_uip() -> str | None:
    """Locate the real `uip` CLI on PATH, excluding the mock's own dir."""
    self_dir = str(SCRIPT_DIR.resolve())
    parts = []
    for d in os.environ.get("PATH", "").split(os.pathsep):
        if not d:
            continue
        try:
            if Path(d).resolve() == SCRIPT_DIR.resolve():
                continue
        except (OSError, ValueError):
            pass
        parts.append(d)
    return shutil.which("uip", path=os.pathsep.join(parts))


def _passthrough(args: str, original_argv: list[str], rule: dict) -> int:
    """Proxy to the real `uip` CLI; cache the response for subsequent runs."""
    cached = _load_cache(args)
    if cached is not None:
        sys.stdout.write(cached.get("stdout", ""))
        exit_code = int(cached.get("exit_code", 0))
        _log_call(args, rule, exit_code, error="passthrough_cached")
        return exit_code

    real_uip = _find_real_uip()
    if real_uip is None:
        _log_call(args, rule, 2, error="passthrough_no_real_uip")
        return _err(
            {"error": "passthrough requested but real uip not on PATH", "args": args},
            2,
        )

    proc = subprocess.run(
        [real_uip] + original_argv[1:],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    _save_cache(args, proc.stdout, proc.returncode)
    _log_call(args, rule, proc.returncode, error="passthrough_live")
    return proc.returncode


def main(argv: list[str]) -> int:
    # Force stdout/stderr to UTF-8 so non-ASCII fixture content (e.g. Romanian,
    # Cyrillic) doesn't crash on Windows where the default console encoding is
    # cp1252. The agent reads stdout via a file redirect, so encoding it as
    # UTF-8 is always correct.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    args = " ".join(argv[1:])

    # Prefer the sealed store (fixtures decoded in memory, `r/` removed); fall
    # back to the readable `r/` directory for unsealed local runs.
    store = _get_store()
    if store is not _NO_STORE:
        manifest = store["manifest"]
    elif MANIFEST_PATH.is_file():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    else:
        _log_call(args, None, 2, error="manifest_missing")
        return _err({"error": "manifest.json missing", "path": str(MANIFEST_PATH)}, 2)

    # 1. First matching rule wins.
    arg_tokens = set(_tokenize(args))
    for rule in manifest.get("rules", []):
        if not _rule_matches(rule.get("match", ""), args, arg_tokens):
            continue
        if rule.get("passthrough"):
            return _passthrough(args, argv, rule)
        # Fetch the fixture bytes from the sealed store or the `r/` directory.
        if store is not _NO_STORE:
            raw = store["files"].get(rule["file"])
            if raw is None:
                _log_call(args, rule, 2, error="fixture_missing")
                return _err({"error": "response file missing", "path": rule["file"]}, 2)
        else:
            response_file = RESPONSES_DIR / rule["file"]
            if not response_file.is_file():
                _log_call(args, rule, 2, error="fixture_missing")
                return _err({"error": "response file missing", "path": str(response_file)}, 2)
            raw = response_file.read_bytes()
        # Tolerate fixtures written by PowerShell (UTF-16 LE BOM) or UTF-8.
        if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
            text = raw.decode("utf-16")
        else:
            text = raw.decode("utf-8-sig", errors="replace")
        text = _strip_doc_keys(text)
        sys.stdout.write(text)
        exit_code = int(rule.get("exit_code", 0))
        _log_call(args, rule, exit_code)
        return exit_code

    # 2. Unmocked default.
    default = manifest.get("unmocked_default")
    if isinstance(default, dict):
        body = _strip_doc_keys(default.get("response", ""))
        exit_code = int(default.get("exit_code", 0))
        sys.stdout.write(body)
        _log_call(args, None, exit_code, error="unmocked_default")
        return exit_code

    # 3. Legacy error.
    _log_call(args, None, 1, error="unmocked")
    return _err({"error": "unmocked command", "args": args}, 1)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
