#!/usr/bin/env python3
"""Grades SupplierRules, requested with a knowledge source the skill still does not author.

Knowledge models and literal expressions are in the profile; a knowledge source,
a decision service and an import are not. `load_graph` fails on the first two,
and an import is checked here.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from graph_check import check_graph_cases  # noqa: E402
from rules_check import UNSUPPORTED_ELEMENTS, fail, find_project, load_graph  # noqa: E402

PROJECT = "SupplierRules"
CASES = [({"onboarded": onboarded, "spend": spend},
          {"approved": onboarded and spend <= 25000})
         for onboarded in (True, False)
         for spend in (0, 25000, 25001, 90000)]


def main() -> None:
    # `load_graph` refuses every element in `UNSUPPORTED_ELEMENTS`, which is the whole of the set
    # this task is about. Re-listing a subset here is what let the three lists drift: this grader
    # named `import` and `group`, `load_graph` named `knowledgeSource`, and `decisionService` was
    # asserted in both. Named rather than silently relied on, so the task still says what it grades.
    _, root = load_graph(find_project(PROJECT))
    if not UNSUPPORTED_ELEMENTS:
        fail("the unsupported-element set is empty; this task grades that each one is refused")
    check_graph_cases(root, CASES)
    print(f"OK: none of {list(UNSUPPORTED_ELEMENTS)} is declared, and all {len(CASES)} cases "
          f"return the expected decision")


if __name__ == "__main__":
    main()
