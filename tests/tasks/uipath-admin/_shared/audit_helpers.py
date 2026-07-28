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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from admin_helpers import run_cli  # noqa: E402  (path set above)

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


def load_saved(path):
    """Load a JSON file the agent was asked to save. Fails the check if unusable.

    `utf-8-sig` because a PowerShell-redirected or BOM-prefixed save is a
    save-shape variance, not a real failure.
    """
    if not os.path.exists(path):
        fail(f"expected the agent to save {path!r} — file not found (cwd={os.getcwd()})")
    try:
        with open(path, encoding="utf-8-sig") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        fail(f"{path!r} is not valid JSON ({exc.__class__.__name__}: line {exc.lineno})")
    except OSError as exc:
        fail(f"{path!r} could not be read ({exc.__class__.__name__})")


def unwrap(saved):
    """Return the payload inside a `{Result, Data}` envelope, tolerating wrapping.

    Accepts the raw CLI envelope, a bare `Data`, or an agent-authored wrapper
    around either. A `Result` of `Failure` anywhere is a hard failure — a saved
    error envelope must never read as a successful retrieval.
    """
    result = field(saved, "Result") if isinstance(saved, dict) else None
    if result is not None and str(result).lower() != "success":
        message = field(saved, "Code") or field(saved, "Result")
        fail(f"saved payload is a CLI failure envelope (Result={message!r})")
    data = field(saved, "Data") if isinstance(saved, dict) else None
    return data if data is not None else saved


def _walk_lists(node):
    """Yield every list nested anywhere inside dicts/lists, outermost first."""
    if isinstance(node, list):
        yield node
        for item in node:
            yield from _walk_lists(item)
    elif isinstance(node, dict):
        for value in node.values():
            yield from _walk_lists(value)


def find_records(payload, signature):
    """Find the collection of records matching `signature`, however it is wrapped.

    Save-shape tolerant by design: an agent may hand back a bare array, the
    `{Result, Data}` envelope, `{AuditEvents, Next, Previous}`, or its own
    wrapper object. Rather than guessing at the container, locate the list whose
    dict elements carry the schema's signature keys.

    Returns `[]` when a well-formed but empty collection exists, and `None` when
    no collection of that schema is present at all — the caller must treat those
    differently: empty is a legitimate outcome on a quiet tenant, missing is not.
    """
    empty_candidate = None
    for candidate in _walk_lists(payload):
        if not candidate:
            # Remember an empty list, but keep looking for a populated one whose
            # signature we can actually confirm.
            if empty_candidate is None:
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


def live_query(scope, verb, extra_args=()):
    """Re-query the tenant directly so a check never trusts the agent's file.

    This is the anti-forgery lever for read-only audit: the agent's saved output
    is compared against what the harness itself reads back, so a fabricated or
    stale file cannot pass. `run_cli` builds argv explicitly (no shell), and
    `extra_args` is always author-supplied — never agent-controlled text.
    """
    if scope not in ("org", "tenant"):
        fail(f"internal: bad scope {scope!r}")
    if verb not in ("sources", "events"):
        fail(f"internal: bad verb {verb!r}")
    return run_cli(["admin", "audit", scope, verb, *extra_args], timeout=90)


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
