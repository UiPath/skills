#!/usr/bin/env python3
"""ExpenseReimbursementRunnable — end-to-end runtime check.

Confirms the generated caseplan actually EXECUTES: the automated task types must
resolve to real bindings (not skeletons), then ``uip solution resources refresh``
+ ``uip maestro case debug`` must reach ``finalStatus == Completed`` across the
automated happy path (Submission -> Manager Approval -> Finance Approval ->
Payment -> Approved). Debug is fully headless — the runnable variant contains no
HITL/wait-for-user tasks, so nothing blocks on human input.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import (  # noqa: E402
    iter_tasks,
    read_caseplan,
    run_debug,
    task_is_skeleton,
)

# Task types whose resources must resolve for the case to run end-to-end.
EXECUTABLE_TYPES = {"api-workflow", "agent", "process", "rpa"}


def main():
    plan = read_caseplan()
    skeletons = [
        (t.get("type"), (t.get("data") or {}).get("label"))
        for t in iter_tasks(plan)
        if t.get("type") in EXECUTABLE_TYPES and task_is_skeleton(t)
    ]
    if skeletons:
        listing = ", ".join(f"{typ}:{label!r}" for typ, label in skeletons)
        sys.exit(
            "FAIL: executable task(s) resolved as skeletons (no real binding) — "
            f"debug cannot run them: {listing}"
        )

    # run_debug() asserts finalStatus is Completed/Successful internally (raises otherwise),
    # so reaching here means the case ran to completion. No raw payload-key read needed.
    run_debug(timeout=720)
    print("OK: ExpenseReimbursementRunnable executed end-to-end; debug finalStatus=Completed")


if __name__ == "__main__":
    main()
