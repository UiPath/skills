#!/usr/bin/env python3
"""Grades SupplierRules, requested with an element the skill still does not author.

Each dataset row asks for one: a decision service, an import, or a boxed context.
Knowledge models and literal expressions are in the profile; those three are not.
`load_graph` fails on a decision service and on a decision whose logic is a context;
an import, and a context nested anywhere else, are checked here. A knowledge source
and a group are not graded: the designer draws and keeps both.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from graph_check import check_graph_cases  # noqa: E402
from rules_check import NS, fail, find_project, load_graph  # noqa: E402

PROJECT = "SupplierRules"
CASES = [({"onboarded": onboarded, "spend": spend},
          {"approved": onboarded and spend <= 25000})
         for onboarded in (True, False)
         for spend in (0, 25000, 25001, 90000)]


def main() -> None:
    _, root = load_graph(find_project(PROJECT))
    for unsupported in ("import", "decisionService", "context"):
        if root.findall(f".//dmn:{unsupported}", NS):
            fail(f"the rule holds a <{unsupported}> element, which the skill does not author")
    check_graph_cases(root, CASES)
    print(f"OK: no unsupported element, and all {len(CASES)} cases return the expected decision")


if __name__ == "__main__":
    main()
