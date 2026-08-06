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
    - `passthrough: true` — replay a pre-recorded response from the cache
      (`_cache/<key>.json`, written by the operator-only
      `_shared/scripts/record_passthrough.py`). This dispatcher NEVER
      invokes the real `uip` CLI: a query without a valid recorded entry
      falls through to `unmocked_default` (or the unmocked error). Cache
      entries are schema- and signature-checked before use, so a file the
      agent plants in the sandbox is rejected.

Dispatch precedence:
    1. First matching rule (first match wins).
    2. `unmocked_default` — if set, return its `response` + `exit_code`.
       Also the fallback for a passthrough rule with no recorded response.
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
passthrough rule with `match: "docsai ask"` is the typical way to serve
recorded responses for open-ended natural-language commands.
"""

import base64
import hashlib
import hmac
import json
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
# Passthrough (docsai) cache of operator-recorded responses. Committed under
# `r/_cache` (written by `record_passthrough.py`); `m/seal` moves it beside
# the shim so replay survives `r/` being removed. Check both locations so
# sealed and unsealed runs behave identically.
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

    Fail-closed: the file is the source of truth for expected-vs-performed
    coverage analysis after the run, so a write failure aborts the whole
    invocation (exit 3) BEFORE any response is emitted. Swallowing the error
    would let a broken log (e.g. `m/.log` replaced with a directory) look
    identical to "no calls made" while `uip` keeps answering normally.

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
    except OSError as exc:
        sys.stderr.write(json.dumps({"error": "uip: internal error", "detail": str(exc)}) + "\n")
        raise SystemExit(3) from exc


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


# Provenance key for recorded passthrough responses, shared with the
# operator-only recorder (`_shared/scripts/record_passthrough.py`, which
# imports `_cache_sig` from this module). The sandbox copy of the cache is
# agent-writable, so entries are accepted on a valid signature, not on
# their path. Forging one requires unpacking `.uip.bin` first — the same
# barrier that protects the sealed store; this is tamper-evidence against
# an agent planting responses, not cryptographic secrecy.
_CACHE_SIG_KEY = b"uip-mock-cache-v1:9d41c7a2f06b58e3"


def _cache_sig(entry: dict) -> str:
    """HMAC over the response fields of a recorded cache entry."""
    body = json.dumps(
        [entry.get("args"), entry.get("stdout"), entry.get("exit_code"), entry.get("cached_at")],
        ensure_ascii=False,
    ).encode("utf-8")
    return hmac.new(_CACHE_SIG_KEY, body, hashlib.sha256).hexdigest()


def _cache_entry_valid(entry: object, args: str) -> bool:
    """True when `entry` is a well-formed recorded response for `args`.

    Schema plus provenance: field types must match what the recorder writes,
    `args` must equal the invocation (rejects an entry copied from another
    query's file), and the signature must verify.
    """
    if not isinstance(entry, dict):
        return False
    if entry.get("args") != args:
        return False
    if not isinstance(entry.get("stdout"), str):
        return False
    if not isinstance(entry.get("exit_code"), int) or isinstance(entry.get("exit_code"), bool):
        return False
    if not isinstance(entry.get("cached_at"), str):
        return False
    sig = entry.get("sig")
    return isinstance(sig, str) and hmac.compare_digest(sig, _cache_sig(entry))


def _load_cache(args: str) -> tuple[dict | None, bool]:
    """Return `(entry, tampered)` for the recorded response to `args`.

    `entry` is the first cache file that passes `_cache_entry_valid`, else
    None. `tampered` is True when a candidate file existed but failed
    validation (unreadable, wrong schema, args mismatch, bad signature) —
    surfaced in the call log so a planted or corrupted entry is visible.
    """
    key = f"{_cache_key(args)}.json"
    tampered = False
    for path in (CACHE_DIR / key, LEGACY_CACHE_DIR / key):
        if not path.is_file():
            continue
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            tampered = True
            continue
        if _cache_entry_valid(entry, args):
            return entry, False
        tampered = True
    return None, tampered


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
    passthrough_miss: str | None = None
    for rule in manifest.get("rules", []):
        if not _rule_matches(rule.get("match", ""), args, arg_tokens):
            continue
        if rule.get("passthrough"):
            # Replay the recorded response, if the operator committed one.
            # This dispatcher NEVER starts the real CLI: without a valid
            # recorded entry the invocation falls through to the manifest's
            # `unmocked_default` below, like any other unmocked command.
            cached, tampered = _load_cache(args)
            if cached is not None:
                exit_code = int(cached["exit_code"])
                _log_call(args, rule, exit_code, error="passthrough_cached")
                sys.stdout.write(cached["stdout"])
                return exit_code
            passthrough_miss = "passthrough_cache_invalid" if tampered else "passthrough_cache_miss"
            break
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
        exit_code = int(rule.get("exit_code", 0))
        _log_call(args, rule, exit_code)
        sys.stdout.write(text)
        return exit_code

    # 2. Unmocked default (also the passthrough cache-miss fallback).
    default = manifest.get("unmocked_default")
    if isinstance(default, dict):
        body = _strip_doc_keys(default.get("response", ""))
        exit_code = int(default.get("exit_code", 0))
        _log_call(args, None, exit_code, error=passthrough_miss or "unmocked_default")
        sys.stdout.write(body)
        return exit_code

    # 3. Legacy error.
    _log_call(args, None, 1, error=passthrough_miss or "unmocked")
    return _err({"error": "unmocked command", "args": args}, 1)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
