#!/usr/bin/env python3
"""The case executed to completion.

This is the vehicle, not the outcome — it carries a modest weight. What the test
actually grades is whether the business effects landed in the third-party systems
(check_outcome_email.py / check_outcome_jira.py).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from outcome_probe import ensure_debug_ran, fail, final_status  # noqa: E402

TERMINAL_OK = {"Completed", "Successful"}


def main() -> int:
    result = ensure_debug_ran()
    status = final_status(result)
    if status not in TERMINAL_OK:
        fail(f"case did not complete (finalStatus={status}); "
             f"envelope={result.get('envelope')}")
    print(f"OK: case executed to finalStatus={status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
