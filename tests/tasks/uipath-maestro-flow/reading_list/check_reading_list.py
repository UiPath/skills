#!/usr/bin/env python3
"""ReadingList: assert a transform node filters + maps a book catalog.

Expected: difficulty > 5 AND pages < 600 keeps exactly 3 books —
Linear Algebra Done Right (Axler), Bayesian Data Analysis (Gelman),
Information Theory (MacKay) — with titles uppercased.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_outputs_contain,
    collect_outputs,
    run_debug,
)

# Authors whose books pass both filters (difficulty > 5 AND pages < 600):
#   Axler  — difficulty 6, 340 pages
#   Gelman — difficulty 8, 580 pages
#   MacKay — difficulty 7, 540 pages
EXPECTED_AUTHORS = ["axler", "gelman", "mackay"]

# Uppercased titles — verifies the map transformation worked
EXPECTED_UPPERCASE = [
    "LINEAR ALGEBRA DONE RIGHT",
    "BAYESIAN DATA ANALYSIS",
    "INFORMATION THEORY",
]

# Author unique to a book that must be filtered out
# (Python for Data Analysis, difficulty 3)
FILTERED_AUTHOR = "mckinney"


def main():
    # Must use a transform node — substring matches all four variants:
    # core.action.transform, core.action.transform.filter,
    # core.action.transform.map, core.action.transform.group-by
    assert_flow_has_node_type(["core.action.transform"])

    payload = run_debug(timeout=240)

    # All 3 expected authors must appear in declared outputs
    assert_outputs_contain(payload, EXPECTED_AUTHORS)

    outputs = collect_outputs(payload)
    output_str = json.dumps(outputs, default=str)

    # Verify uppercase titles — confirms map transformation worked
    for title in EXPECTED_UPPERCASE:
        if title not in output_str:
            sys.exit(
                f"FAIL: Expected uppercased title '{title}' not found in outputs — "
                f"map transformation may not have applied uppercase\n"
                f"Outputs: {output_str[:1000]}"
            )

    # McKinney's book (difficulty 3) should NOT appear — verifies filter worked
    output_lower = output_str.lower()
    if FILTERED_AUTHOR in output_lower:
        sys.exit(
            f"FAIL: '{FILTERED_AUTHOR}' found in outputs — "
            f"filter did not exclude low-difficulty books\n"
            f"Outputs: {output_lower[:1000]}"
        )

    print(
        "OK: Transform node present; reading list contains uppercased titles and correct authors"
    )


if __name__ == "__main__":
    main()
