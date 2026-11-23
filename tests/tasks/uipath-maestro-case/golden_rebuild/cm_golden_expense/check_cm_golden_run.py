#!/usr/bin/env python3
"""CMGoldenExpense: run the case once on the live tenant and check what it did.

The case starts by having the expense agent analyze the request, the process
orchestration process it and the robot record it, then waits for the manager.
So one debug run must show, from its element executions:

  - the stage the case starts in was entered;
  - each required automated task that stage starts (the agent, the process
    and the RPA job, all bound to the deployed CM-Golden resources) completed;
  - the case moved on to the stage that follows it (the manager approval);
  - no required task or stage failed.

The stages and tasks are read from the built plan (case-entered stage, its
required automated tasks, the stage entered after it), not matched by name.
The run parks at the manager's approval, so the instance is cancelled after.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CASE_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, CASE_ROOT)
from _shared.case_run_path import path_failures, run_opening_path  # noqa: E402
from _shared.case_check import existing_caseplan, read_caseplan  # noqa: E402

EXPECTED_CASEPLAN = os.path.join("CMGoldenExpense", "CMGoldenExpense", "caseplan.json")


def main() -> None:
    plan = read_caseplan(existing_caseplan(EXPECTED_CASEPLAN))
    path, run = run_opening_path(plan)
    problems = path_failures(path, run)
    if problems:
        sys.exit(
            f"FAIL: the debug run (instance {run['instance_id']}, status "
            f"{run['status'] or 'unknown'}) did not take the opening path:\n  - "
            + "\n  - ".join(problems)
        )
    tasks = ", ".join(f"{t.get('type')}:{t.get('displayName')!r}" for _, t in path["automated"])
    print(
        f"OK: the run completed {tasks} and moved on to "
        + " / ".join(repr((s.get("data") or {}).get("label")) for s in path["next"])
        + f" (instance status {run['status'] or 'unknown'})"
    )


if __name__ == "__main__":
    main()
