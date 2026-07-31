#!/usr/bin/env python3
"""Shared helpers for the outcome-graded `uip admin audit` checks.

Two hard rules every audit check in this directory follows:

1. **Never emit audit-record field VALUES.** Audit events carry PII — actor
   emails, actor names, client IP addresses, and free-form `EventDetails`.
   These checks print to CI logs that are readable far beyond the test author,
   so failure messages report *counts*, *key names*, and *truncated GUID
   prefixes* only. Use `keys_of()` and `gid()` instead of interpolating a
   record.
2. **Never build a shell string.** Every CLI call goes through
   `admin_helpers.run_cli`, which uses an explicit argv list with
   `shell=False`, so no value can be reinterpreted as a shell command.

Casing tolerance: the CLI host's `OutputFormatter.success` recursively
PascalCases every key under `Data`, so `--output json` returns `AuditEvents` /
`CreatedOn` / `EventTargets` even though the tool source emits camelCase. Every
lookup here goes through `field()`, which is case- and underscore-insensitive,
so a change on either side does not silently break a check.

Two distinct record schemas exist and must not be confused:
  * live `events`  -> Id, CreatedOn, ActorId, EventType, EventSource, Status(0|1)
  * `export` (LTS) -> Identifier, DateCreatedUtc, ActorId, Action, Source, Category
"""

import datetime
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from admin_helpers import poll, run_cli  # noqa: E402  (path set above)

# Signature keys that identify a record as a live `events` row vs an LTS export
# row. Matched case-insensitively via `field()`.
EVENT_SIGNATURE = ("eventtype", "eventsource", "createdon")
LTS_SIGNATURE = ("identifier", "datecreatedutc", "action")
# A source row is a top-level audit category (Identity, Tenant, Governance, ...).
SOURCE_SIGNATURE = ("eventtargets",)


def _norm(key):
    """Canonical form of a JSON key: lowercase, underscores stripped."""
    return str(key).lower().replace("_", "")


def field(record, *names):
    """Case/underscore-insensitive field lookup. Returns None when absent.

    `field(ev, "CreatedOn", "DateCreatedUtc")` returns the first name present,
    so one call handles both the live-events and LTS-export schemas.
    """
    if not isinstance(record, dict):
        return None
    normalized = {_norm(k): v for k, v in record.items()}
    for name in names:
        if _norm(name) in normalized:
            return normalized[_norm(name)]
    return None


def has_fields(record, names):
    """True when the record carries every one of `names` (case-insensitive)."""
    if not isinstance(record, dict):
        return False
    normalized = {_norm(k) for k in record}
    return all(_norm(n) in normalized for n in names)


def keys_of(record, limit=12):
    """Key NAMES only — safe to log. Never returns any field value."""
    if not isinstance(record, dict):
        return f"<{type(record).__name__}>"
    return sorted(record)[:limit]


def gid(value, keep=8):
    """Truncate an identifier for logging.

    A full ActorId/OrganizationId is an identifier for a real person or org, so
    only a short prefix is ever logged — enough to correlate two sides of a
    comparison, not enough to identify the subject.
    """
    if value is None:
        return "<none>"
    text = str(value)
    return text[:keep] + "..." if len(text) > keep else text


def fail(message):
    """Print FAIL and exit 1 so a run_command criterion registers a failure."""
    print(f"FAIL: {message}")
    sys.exit(1)


def ok(message):
    print(f"OK: {message}")


def wait_for(predicate, timeout=90, interval=3):
    """Poll `predicate` until it returns a truthy value, or give up after `timeout`.

    Some agents run a long CLI call through a background runner and end their turn
    before it finishes, so an artifact can still be materializing when grading
    starts. These checks assert that the command produced the right result, not
    that it did so before the turn ended, so a bounded wait is the honest
    behavior — it removes a race without excusing an agent that never ran it.
    """
    deadline = time.time() + timeout
    while True:
        value = predicate()
        if value:
            return value
        if time.time() >= deadline:
            return None
        time.sleep(interval)


def load_saved(path, timeout=90):
    """Load a JSON file the agent was asked to save. Fails the check if unusable.

    `utf-8-sig` because a PowerShell-redirected or BOM-prefixed save is a
    save-shape variance, not a real failure.

    Retries both the existence and the parse: a multi-megabyte redirect that is
    still flushing parses as truncated JSON, which is a race, not a wrong answer.
    Only the final attempt's error is reported.
    """
    last_error = None

    def readable():
        nonlocal last_error
        if not os.path.exists(path):
            last_error = "file not found"
            return None
        try:
            with open(path, encoding="utf-8-sig") as handle:
                # Wrap in a 1-tuple so a legitimately falsy payload (`[]`, `{}`)
                # is not mistaken for "not ready yet".
                return (json.load(handle),)
        except json.JSONDecodeError as exc:
            last_error = f"invalid JSON ({exc.msg} at line {exc.lineno} col {exc.colno})"
            return None
        except OSError as exc:
            last_error = f"unreadable ({exc.__class__.__name__})"
            return None

    result = wait_for(readable, timeout=timeout)
    if result is None:
        size = os.path.getsize(path) if os.path.exists(path) else 0
        fail(
            f"expected the agent to save valid JSON at {path!r} — {last_error} after waiting "
            f"{timeout}s (size={size} bytes, cwd={os.getcwd()})"
        )
    return result[0]


def _find_failure(node):
    """Locate a CLI non-success envelope at ANY depth, or None.

    Checking only the top level would let a saved error through whenever the
    agent wrapped it (`{"output": {"Result": "Failure", ...}}`), and the nested
    `Data: []` would then read as "the window is legitimately empty".

    Matches anything that is not `Success` rather than only `Failure`: the CLI
    also emits `ValidationError` (seen in a real run when an agent passed an
    out-of-range `--limit`), and an allowlist of known error spellings would
    silently pass the next one.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            if _norm(key) == "result" and isinstance(value, str) \
                    and value.strip().lower() != "success":
                return node
        for value in node.values():
            found = _find_failure(value)
            if found is not None:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_failure(item)
            if found is not None:
                return found
    return None


def unwrap(saved):
    """Return the payload inside a `{Result, Data}` envelope, tolerating wrapping.

    Accepts the raw CLI envelope, a bare `Data`, or an agent-authored wrapper
    around either. A `Result` of `Failure` at any depth is a hard failure — a
    saved error must never read as a successful retrieval.
    """
    envelope = _find_failure(saved)
    if envelope is not None:
        # Report the enum-ish fields and the static remediation text. `Message` is
        # deliberately omitted: it echoes the request, which for audit can include
        # a `--search` term containing someone's email. The agent's full command
        # is in the run transcript anyway.
        result = field(envelope, "Result")
        code = field(envelope, "ErrorCode") or field(envelope, "Code") or "no code"
        hint = field(envelope, "Instructions") or "no instructions given"
        fail(f"saved payload is a CLI error envelope (Result={result!r}, ErrorCode={code!r}; "
             f"{hint}) — the retrieval did not succeed")
    data = field(saved, "Data") if isinstance(saved, dict) else None
    return data if data is not None else saved


# Keys whose value may legitimately be an EMPTY collection of records, per schema.
# An empty list under any other key is unrelated data, not "zero records" — see
# find_records. Deliberately schema-specific: `sources: []` is a plausible empty
# sources catalog but says nothing about events, so it must not satisfy an events
# check.
_GENERIC_CONTAINERS = {"data", "value", "items", "results"}
EMPTY_CONTAINER_KEYS = {
    EVENT_SIGNATURE: _GENERIC_CONTAINERS | {"auditevents", "events"},
    LTS_SIGNATURE: _GENERIC_CONTAINERS | {"events", "auditevents"},
    SOURCE_SIGNATURE: _GENERIC_CONTAINERS | {"sources"},
}


def _walk_lists(node, key=None):
    """Yield (list, containing-key) for every list nested anywhere, outermost first."""
    if isinstance(node, list):
        yield node, key
        for item in node:
            yield from _walk_lists(item, key)
    elif isinstance(node, dict):
        for child_key, value in node.items():
            yield from _walk_lists(value, child_key)


def find_records(payload, signature):
    """Find the collection of records matching `signature`, however it is wrapped.

    Save-shape tolerant by design: an agent may hand back a bare array, the
    `{Result, Data}` envelope, `{AuditEvents, Next, Previous}`, or its own
    wrapper object. Rather than guessing at the container, locate the list whose
    dict elements carry the schema's signature keys.

    Returns `[]` when a well-formed but empty collection exists, and `None` when
    no collection of that schema is present at all — the caller must treat those
    differently: empty is a legitimate outcome on a quiet tenant, missing is not.

    An empty list only counts as "zero records" when it is the whole payload or
    sits under a key that plausibly holds THIS schema's collection. Accepting any
    empty list found anywhere previously let a summary object like
    `{"summary": "none found", "sources": []}` satisfy an events check.
    """
    allowed = EMPTY_CONTAINER_KEYS.get(tuple(signature), _GENERIC_CONTAINERS)
    empty_candidate = None
    for candidate, key in _walk_lists(payload):
        if not candidate:
            if empty_candidate is None and (key is None or _norm(key) in allowed):
                empty_candidate = candidate
            continue
        dicts = [item for item in candidate if isinstance(item, dict)]
        if dicts and any(has_fields(item, signature) for item in dicts):
            return dicts
    return empty_candidate


def parse_ts(value):
    """Parse an ISO-8601 audit timestamp into a naive UTC datetime, or None.

    Hand-rolled rather than `datetime.fromisoformat` so the check behaves the
    same on any Python the agent sandbox ships: older versions reject a trailing
    `Z` and choke on 7-digit fractional seconds from the LTS.
    """
    if not value:
        return None
    text = str(value).strip().replace("z", "Z")
    if text.endswith("Z"):
        text = text[:-1]
    # Drop an explicit numeric offset; audit timestamps are UTC in practice and
    # a mixed-offset comparison would be worse than ignoring it.
    for sep in ("+", "-"):
        marker = text.rfind(sep)
        if marker > 10:
            text = text[:marker]
            break
    if "." in text:
        head, _, frac = text.partition(".")
        text = f"{head}.{frac[:6]}"
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def event_timestamp(record):
    """Timestamp of a record from either schema (live events or LTS export)."""
    return parse_ts(field(record, "CreatedOn", "DateCreatedUtc", "CreatedOnUtc"))


def status_of(record):
    """Normalize an audit status to 'success' / 'failure' / None.

    `Status` is the numeric `AuditEventStatus` enum (0=Success, 1=Failure) on
    both surfaces, but a formatter or CSV round-trip can surface it as a label
    or a numeric string, so all three forms are accepted.
    """
    raw = field(record, "Status")
    if raw is None:
        return None
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return {0: "success", 1: "failure"}.get(int(raw))
    text = str(raw).strip().lower()
    if text in ("0", "success"):
        return "success"
    if text in ("1", "failure"):
        return "failure"
    return None


def live_query(scope, verb, extra_args=(), attempts=3):
    """Re-query the tenant directly so a check never trusts the agent's file.

    This is the anti-forgery lever for read-only audit: the agent's saved output
    is compared against what the harness itself reads back, so a fabricated or
    stale file cannot pass. `run_cli` builds argv explicitly (no shell), and
    `extra_args` is always author-supplied — never agent-controlled text.

    Retried, because these checks gate the task: tasks run concurrently against a
    shared tenant over a shared token cache, so a single 429 or token-refresh
    blip must not read as "the data isn't there". The per-call timeout is kept
    well under the criteria's own timeouts so a slow call still yields a readable
    failure rather than being killed mid-run.
    """
    if scope not in ("org", "tenant"):
        fail(f"internal: bad scope {scope!r}")
    if verb not in ("sources", "events"):
        fail(f"internal: bad verb {verb!r}")
    args = ["admin", "audit", scope, verb, *extra_args]
    return poll(lambda: run_cli(args, timeout=60), max_attempts=attempts, delay=5)


def env_flag(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def env_int(name, default=None):
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value.strip())
    except ValueError:
        fail(f"internal: {name}={value!r} is not an integer")


def env_str(name, default=None):
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    return value.strip()
