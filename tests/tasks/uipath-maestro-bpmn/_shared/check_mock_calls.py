#!/usr/bin/env python3
"""Assert the mocked ``uip`` served a call, from the mock's own call log.

Usage (from a task's run_command, cwd = sandbox root):

    python3 $REFERENCE_DIR/_shared/check_mock_calls.py '<regex>' ['<regex>' ...]

Each regex must match the ``args`` of at least one call in
``mocks/.calls.jsonl`` that a manifest rule answered with exit code 0. The
args are the space-joined argv after ``uip`` (``maestro bpmn instance cursors
inst-1 -f folder --output json``), exactly as the dispatcher in
``mock_template/mocks/uip`` logs them.

Why the log and not the transcript: a ``command_executed`` regex reads one
literal command line, so it failed a correct read issued from a shell loop
(``for c in element-executions cursors; do uip maestro bpmn instance $c inst-1
-f folder; done``) or through a variable (``F=folder; uip ... -f $F``) — R14 v2
diagnose-stuck-gateway and operate-diagnose-minimal-fault-triage
(builder-sdk#1882). The dispatcher records each invocation after the shell has
expanded it, so the log grades what actually reached the CLI, in whatever
shell form the agent wrote it. An unmocked or failed call does not count: the
agent must have received the canned response.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CALL_LOG = Path("mocks") / ".calls.jsonl"


def served_calls(log: Path = CALL_LOG) -> list[str]:
    """The args of every call a manifest rule answered successfully."""
    if not log.is_file():
        return []
    calls: list[str] = []
    for line in log.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if not isinstance(record, dict):
            continue
        if record.get("matched_rule") and record.get("exit_code") == 0:
            calls.append(str(record.get("args", "")))
    return calls


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: check_mock_calls.py <regex> [<regex> ...]", file=sys.stderr)
        return 2
    calls = served_calls()
    if not calls:
        print(f"FAIL: no served call recorded in {CALL_LOG}", file=sys.stderr)
        return 1
    rc = 0
    for pattern in argv:
        regex = re.compile(pattern)
        hit = next((c for c in calls if regex.search(c)), None)
        if hit is None:
            print(f"FAIL: no served mock call matches /{pattern}/", file=sys.stderr)
            rc = 1
        else:
            print(f"OK: /{pattern}/ <- uip {hit}")
    if rc:
        print("served calls:\n  " + "\n  ".join(calls), file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
