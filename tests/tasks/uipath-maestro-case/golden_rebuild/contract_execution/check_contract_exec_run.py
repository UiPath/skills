#!/usr/bin/env python3
"""ContractExecution: run the case once on the live tenant and check what it did.

A new contract request starts in the checking stage: the API workflow pulls
the counterparty's records and Legal Operations gets the task to check the
request, where the case then waits. So one debug run must show, from its
element executions:

  - the stage the case starts in was entered;
  - each required automated task that stage starts (the ContractOperationsApi
    counterparty pull) completed;
  - each required human task that stage starts (the request check) was opened;
  - no required task or stage failed. The optional clause-analysis agent may
    fail without failing this check: the debug run starts with no draft attached.

The stages and tasks are read from the built plan (case-entered stage and its
required tasks), not matched by name. The instance is cancelled afterwards.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CASE_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, CASE_ROOT)
from _shared.case_run_path import path_failures, run_opening_path  # noqa: E402
from _shared.case_check import existing_caseplan, read_caseplan  # noqa: E402

EXPECTED_CASEPLAN = os.path.join("ContractExecution", "ContractExecution", "caseplan.json")


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
    automated = ", ".join(f"{t.get('type')}:{t.get('displayName')!r}" for _, t in path["automated"])
    human = ", ".join(repr(t.get("displayName")) for _, t in path["human"])
    print(
        f"OK: the run completed {automated} and opened {human} "
        f"(instance status {run['status'] or 'unknown'})"
    )


if __name__ == "__main__":
    main()
