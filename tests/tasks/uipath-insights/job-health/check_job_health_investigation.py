#!/usr/bin/env python3
"""Validator for job_health_investigation_e2e.yaml artifacts.

The four saved envelopes must pass the shared structural checks (Result,
exact Code, Data present) and the report must be non-trivial AND tied to the
data the CLI actually returned: when `top-failures.json` names failing
processes, the report has to name one of them. That is the check that stops
the report from being graded on its own prose — a plausible-looking summary
the agent invented cannot name a process the tenant reported.

Data-agnostic both ways: an empty window is a structural pass, and both the
numbers and process-name requirements apply only when the window has data —
an honest "no job history" report carries neither.

Also issues one live read of its own (`probe_live_cli`) so an unentitled or
misconfigured tenant fails with the CLI's own message instead of looking like a
run that saved bad files.

Exit 0 on pass, 1 on fail. Reads from the task sandbox cwd (coder_eval
invokes run_command criteria with cwd set to the sandbox root).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_shared = (Path(os.environ["SKILLS_REPO_PATH"]) / "tests" / "tasks" / "uipath-insights" / "_shared"
           if os.environ.get("SKILLS_REPO_PATH")
           else Path(__file__).resolve().parent.parent / "_shared")
sys.path.insert(0, str(_shared))
from envelope_check import (
    CODES,
    check_envelope,
    has_signal,
    load_envelope,
    probe_live_cli,
    process_names,
)

# The envelope whose Data names the failing processes the report is checked
# against.
TOP_FAILURES = "top-failures.json"

EXPECTED = {
    name: CODES[name]
    for name in (
        "summary.json",
        TOP_FAILURES,
        "failures-by-reason.json",
        "failure-details.json",
    )
}

# 120 keeps a compact empty-window report passing (the shared tenant is often
# empty) while still rejecting placeholder output.
REPORT = "job-health-report.md"
REPORT_MIN_CHARS = 120


def _check_report(empty_window: bool, failing_processes: list) -> bool:
    path = Path(REPORT)
    if not path.exists():
        print(f"FAIL: {REPORT} does not exist", file=sys.stderr)
        return False
    text = path.read_text(encoding="utf-8")
    if len(text.strip()) < REPORT_MIN_CHARS:
        print(
            f"FAIL: {REPORT} is trivial ({len(text.strip())} chars, need >= {REPORT_MIN_CHARS})",
            file=sys.stderr,
        )
        return False
    if empty_window:
        return True
    if not any(ch.isdigit() for ch in text):
        print(
            f"FAIL: {REPORT} contains no numbers — the window has data, expected counts or rates",
            file=sys.stderr,
        )
        return False
    if failing_processes:
        haystack = text.lower()
        if not any(name.lower() in haystack for name in failing_processes):
            print(
                f"FAIL: {REPORT} names none of the failing processes {TOP_FAILURES} reported "
                f"({', '.join(failing_processes)}) — the report is not grounded in the query results",
                file=sys.stderr,
            )
            return False
    return True


def main() -> int:
    errors = 0
    empty_window = True
    failing_processes: list = []

    # First, so a tenant that cannot answer Insights queries names itself before
    # the per-file diagnostics, which would otherwise read as bad artifacts.
    if not probe_live_cli():
        errors += 1

    for fname, code in EXPECTED.items():
        data = load_envelope(fname)
        if data is None or not check_envelope(fname, data, code):
            errors += 1
            continue
        if has_signal(data.get("Data")):
            empty_window = False
        if fname == TOP_FAILURES:
            failing_processes = process_names(data.get("Data"))

    if not _check_report(empty_window, failing_processes):
        errors += 1

    if errors:
        return 1
    if empty_window:
        print("OK: structural pass, empty window — all envelopes valid, no job history in range")
    elif failing_processes:
        print(
            "OK: all envelopes valid, report present and names a failing process the CLI "
            f"reported ({', '.join(failing_processes)})"
        )
    else:
        print("OK: all envelopes valid, report present (no failing processes to cross-check)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
