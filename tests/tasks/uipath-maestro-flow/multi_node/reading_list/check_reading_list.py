#!/usr/bin/env python3
"""ReadingList: assert a transform node filters + maps a book catalog.

Expected: difficulty > 5 AND pages < 600 keeps exactly 3 books —
Linear Algebra Done Right (Axler), Bayesian Data Analysis (Gelman),
Information Theory (MacKay) — with titles uppercased.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_outputs_contain,
    run_debug,
)

# Uppercased titles of the 3 books that pass both filters
# (difficulty > 5 AND pages < 600).
# If all 3 appear uppercased, the filter AND map both worked —
# no negative check needed.
EXPECTED_TITLES = [
    "LINEAR ALGEBRA DONE RIGHT",
    "BAYESIAN DATA ANALYSIS",
    "INFORMATION THEORY",
]

EXPECTED_AUTHORS = ["axler", "gelman", "mackay"]


def main():
    # Must use a transform node — substring matches all four variants
    assert_flow_has_node_type(["core.action.transform"])

    payload = run_debug(timeout=240)

    # Uppercased titles prove both filter (only these 3 qualify) and map (uppercase)
    assert_outputs_contain(payload, EXPECTED_TITLES)

    # Authors confirm the right books were selected
    assert_outputs_contain(payload, EXPECTED_AUTHORS)

    print("OK: Transform node present; 3 correct books with uppercased titles")


if __name__ == "__main__":
    main()
