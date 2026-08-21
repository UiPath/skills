#!/usr/bin/env python3
"""Shared envelope validation helpers for the uipath-insights e2e checkers.

`uip insights` success envelopes are PascalCased by the CLI formatter, so
callers assert `Result`/`Code`/`Data`, not `result`/`code`. Code strings come
from cli/packages/insights-tool/src/commands/jobs.ts. No envelope check asserts
Data content: the shared tenant's job history grows over time, so both empty and
populated windows must pass structurally. `has_signal` and `process_names` read
Data only so callers can tell an empty window from a populated one and can
cross-check an agent-written report against what the CLI actually returned.

Checkers import this module via a sys.path insert relative to their own file
(coder_eval runs them as `python3 $TASK_DIR/<checker>.py` with the sandbox as
cwd, so a plain relative import would not resolve).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Ceiling for the live probe's own subprocess, kept under the run_command
# timeouts in the task YAMLs so a hung CLI reports through our diagnostic
# instead of being killed by the criterion. Cold first calls have been observed
# at ~21s against a live tenant.
LIVE_PROBE_TIMEOUT = 45

# Envelope Code string per subcommand, from jobs.ts.
CODES = {
    "summary.json": "InsightsJobsSummary",
    "completed-timeline.json": "InsightsJobsCompletedTimeline",
    "uncompleted-timeline.json": "InsightsJobsUncompletedTimeline",
    "top-failures.json": "InsightsJobsTopFailures",
    "failures-by-reason.json": "InsightsJobsFailuresByReason",
    "process-details.json": "InsightsJobsProcessDetails",
    "failure-details.json": "InsightsJobsFailureDetails",
}


def load_envelope(name: str):
    """Load a saved envelope file; print a FAIL diagnostic and return None on
    any problem so every failure names the file and the reason."""
    path = Path(name)
    if not path.exists():
        print(f"FAIL: {name} does not exist", file=sys.stderr)
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"FAIL: {name} is not valid JSON: {e}", file=sys.stderr)
        return None
    if data is None:
        print(
            f"FAIL: {name} parses to JSON null — expected a response envelope object",
            file=sys.stderr,
        )
        return None
    return data


def _error_context(data: dict) -> str:
    """CLI-supplied failure text, trimmed, as a suffix for a FAIL line."""
    parts = []
    for field in ("Message", "Instructions"):
        value = data.get(field)
        if isinstance(value, str) and value.strip():
            parts.append(f"{field}: {value.strip()[:300]}")
    return f" — {' | '.join(parts)}" if parts else ""


def check_envelope(name: str, data, code: str) -> bool:
    if not isinstance(data, dict):
        print(f"FAIL: {name} is not a JSON object (got {type(data).__name__})", file=sys.stderr)
        return False
    ok = True
    if data.get("Result") != "Success":
        # Error envelopes carry Message + Instructions and no Code (jobs.ts
        # executeJobsEndpoint), so echo both: it separates "tenant has no
        # Insights entitlement / bad auth" from a genuine test regression
        # without opening the artifact.
        print(
            f"FAIL: {name} Result != 'Success' (got {data.get('Result')!r})"
            f"{_error_context(data)}",
            file=sys.stderr,
        )
        ok = False
    if data.get("Code") != code:
        print(f"FAIL: {name} Code != {code!r} (got {data.get('Code')!r})", file=sys.stderr)
        ok = False
    if "Data" not in data:
        print(f"FAIL: {name} missing 'Data' field", file=sys.stderr)
        ok = False
    return ok


def has_signal(value) -> bool:
    """True when Data carries any non-empty, non-zero content."""
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(has_signal(v) for v in value)
    if isinstance(value, dict):
        return any(has_signal(v) for v in value.values())
    return True


def probe_live_cli(timeout: int = LIVE_PROBE_TIMEOUT) -> bool:
    """Issue one real read so a tenant that cannot answer Insights queries fails
    with the CLI's own message rather than looking like a bad artifact.

    A read-only command surface leaves no tenant state behind, so unlike the
    platform tasks there is nothing to re-query for what the agent did. This
    probe answers the narrower question the saved files cannot: does this tenant
    answer `uip insights jobs` at all. Envelope shape only — Data is never read,
    so the assertion holds on an empty window.

    One minute of history keeps the call cheap; the window is irrelevant to the
    shape being asserted.
    """
    argv = ["uip", "insights", "jobs", "summary", "--time-range", "60", "--output", "json"]
    printable = " ".join(argv)
    label = f"live probe ({printable})"
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        print(f"FAIL: {label} could not run — no `uip` on PATH", file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        print(f"FAIL: {label} timed out after {timeout}s", file=sys.stderr)
        return False

    if not proc.stdout.strip():
        # stderr is where auth and connectivity failures land; trimmed because a
        # stack trace or token-bearing URL would otherwise reach the CI log.
        detail = proc.stderr.strip()[:200] or "no output on either stream"
        print(
            f"FAIL: {label} wrote nothing to stdout (exit {proc.returncode}): {detail}",
            file=sys.stderr,
        )
        return False

    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        print(f"FAIL: {label} did not return JSON: {e}", file=sys.stderr)
        return False

    # A rejected read is the expected shape of "this tenant can't answer", and
    # its envelope carries no Code or Data, so report the cause once instead of
    # letting check_envelope add two lines of noise about the missing fields.
    if isinstance(envelope, dict) and envelope.get("Result") != "Success":
        print(
            f"FAIL: {label} was rejected by the tenant (Result "
            f"{envelope.get('Result')!r}){_error_context(envelope)}",
            file=sys.stderr,
        )
        return False

    if not check_envelope(label, envelope, CODES["summary.json"]):
        return False
    print(f"OK: {label} returned {CODES['summary.json']}")
    return True


def _get_ci(mapping, *candidate_keys: str, default=None):
    """Case-insensitively read the first present candidate key from ``mapping``.

    The envelope wrapper's ``Result``/``Code``/``Data`` casing IS the shipped
    contract and stays literally asserted in `check_envelope`. The keys INSIDE
    ``Data`` are not what these checkers grade, so runtime-payload reads go
    through this accessor (same pattern as `_get_ci` in
    uipath-maestro-flow/_shared/flow_check.py): a camelCase ``processName``
    would otherwise return nothing silently and skip the report-grounding
    branch while the task still passes.
    """
    if not isinstance(mapping, dict):
        return default
    lowered = {k.lower(): k for k in mapping.keys() if isinstance(k, str)}
    for candidate in candidate_keys:
        actual = lowered.get(candidate.lower())
        if actual is not None:
            return mapping[actual]
    return default


def process_names(data) -> list:
    """Process names carried by a jobs envelope's `Data.ProcessName`.

    The row columns come back as arrays that are sometimes nested one level per
    grouping bucket (`JobCountByTime` is `[[1]]` on the same response), so
    collect strings at any depth and drop blanks. Empty list when the column is
    absent or null, which is what an empty window returns. The column is read
    case-insensitively so a serialization change to camelCase can't silently
    turn a populated window into an empty-looking one.
    """
    names: list = []

    def walk(value) -> None:
        if isinstance(value, str):
            if value.strip():
                names.append(value.strip())
        elif isinstance(value, list):
            for item in value:
                walk(item)

    if isinstance(data, dict):
        walk(_get_ci(data, "ProcessName"))
    return names
