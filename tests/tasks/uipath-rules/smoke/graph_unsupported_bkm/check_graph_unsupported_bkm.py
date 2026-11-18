#!/usr/bin/env python3
"""Grades DiscountRules, requested with a business knowledge model the skill does not author.

`load_graph` fails on a businessKnowledgeModel or on logic that is not a
decision table; the discount must still come out right for every case.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from graph_check import check_graph_cases  # noqa: E402
from rules_check import find_project, load_graph  # noqa: E402

PROJECT = "DiscountRules"
BASE = {"Gold": 10, "Silver": 5, "Standard": 0}
LARGE = {"Gold": 15, "Silver": 7.5, "Standard": 2}
CASES = [
    ({"customerTier": tier, "orderTotal": total}, {"discount": (LARGE if total >= 1000 else BASE)[tier]})
    for tier in BASE
    for total in (0, 999, 1000, 5000)
]

if __name__ == "__main__":
    _, root = load_graph(find_project(PROJECT))
    check_graph_cases(root, CASES)
    print(f"OK: no unsupported element, and all {len(CASES)} cases return the expected discount")
