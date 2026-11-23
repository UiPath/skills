#!/usr/bin/env python3
"""Grades DiscountRules, whose tier lookup sits in a business knowledge model the decision calls.

Structure only, and the discount values are graded nowhere. A call is FEEL the
offline evaluator does not run, and no engine task covers DiscountRules —
`graph_check.py engine` is wired to LoanRules and graph_formula_and_model_debug
covers FeeRules. The prompt does not pin the model's signature either, so there
are no fixed parameters to evaluate its table against. A model with the tiers
swapped passes this task; what it grades is the structural contract.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from graph_check import (  # noqa: E402
    check_annotations_attached,
    check_knowledge_models,
    check_no_overlap,
    knowledge_models,
)
from rules_check import NS, fail, find_project, load_graph  # noqa: E402

PROJECT = "DiscountRules"


def main() -> None:
    _, root = load_graph(find_project(PROJECT))
    check_knowledge_models(root)

    # The decision has to call the model, not inline the lookup it was asked to extract.
    models = {m.get("name") for m in knowledge_models(root)}
    callers = [d for d in root.findall("dmn:decision", NS)
               if d.findall("dmn:knowledgeRequirement/dmn:requiredKnowledge", NS)]
    if not callers:
        fail(f"no decision calls {sorted(models)}; the lookup was asked for as a knowledge model")

    called = {text for d in callers for text in d.itertext() if text}
    for name in models:
        if not any(f"{name}(" in text for text in called):
            fail(f"no decision's logic calls {name}(...), so the model is wired but never used")

    check_annotations_attached(root)
    check_no_overlap(root)
    print(f"OK: {sorted(models)} declared, called, annotated, and the diagram is whole")


if __name__ == "__main__":
    main()
