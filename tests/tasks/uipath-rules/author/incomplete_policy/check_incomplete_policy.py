#!/usr/bin/env python3
"""Grades SupplierRatings, whose policy leaves on-time rates from 80 up to 90 undefined.

Only the simulated user knows that range: Red below 85, Amber from 85. An agent that fills
the gap with a guess, Amber for the whole range being the obvious one, fails these cases.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from rules_check import check_cases, check_input_data, find_project, load_rule, table_of  # noqa: E402

CASES = [({"onTimeRate": rate}, "Red" if rate < 85 else "Amber" if rate < 90 else "Green")
         for rate in (0, 79.9, 80, 82, 84.9, 85, 87, 89.9, 90, 100)]


def main() -> None:
    _, root = load_rule(find_project("SupplierRatings"))
    check_input_data(root, {"onTimeRate": "number"})
    check_cases(table_of(root), "rating", CASES)
    print(f"OK: all {len(CASES)} cases match, including the range the user defined")


if __name__ == "__main__":
    main()
