#!/usr/bin/env python3
"""The case executed to completion.

This is the vehicle, not the outcome — it carries a modest weight. What the test
actually grades is whether the business effects landed in the third-party systems
(check_outcome_email.py / check_outcome_jira.py).

On any other status it prints WHY: the incident(s) and the failed element(s),
read from ``debug_result.json`` (the debug ``Data`` plus the CLI's stderr tail).
The harness deletes the debug solution afterwards, so this line is the only
record of the fault.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "_setup"))
sys.path.insert(0, os.path.dirname(HERE))
from outcome_probe import ensure_debug_ran, fail, final_status  # noqa: E402
from _shared.case_check import format_debug_failure  # noqa: E402

TERMINAL_OK = {"Completed", "Successful"}


def main() -> int:
    result = ensure_debug_ran()
    status = final_status(result)
    if status not in TERMINAL_OK:
        why = format_debug_failure(result.get("data") or {}, result.get("stderr_tail") or "")
        fail(f"case did not complete (finalStatus={status}); "
             f"envelope={result.get('envelope')}\n{why}")
    print(f"OK: case executed to finalStatus={status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
