#!/usr/bin/env python3
"""Grades FeeRules through the rules engine: a literal expression and a knowledge model call.

The offline evaluator reads decision-table cells only, so arithmetic and a call
to a knowledge model are graded here, by the engine that actually runs them.
Few cases on purpose: each `uip rules debug` uploads the whole solution.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from graph_check import check_knowledge_models, engine_outputs, knowledge_models  # noqa: E402
from rules_check import NS, fail, find_project, load_graph  # noqa: E402

PROJECT = "FeeRules"
# Either side of the 50000 band edge, and one large loan.
CASES = [
    ({"loanAmount": 20000}, {"band": "Small", "fee": 400.0}),
    ({"loanAmount": 50000}, {"band": "Large", "fee": 750.0}),
    ({"loanAmount": 200000}, {"band": "Large", "fee": 3000.0}),
]


def main() -> None:
    project = find_project(PROJECT)
    root = load_graph(project)[1]
    check_knowledge_models(root)

    # Declared and wired is not called. An agent can carry the knowledgeRequirement and still
    # inline the arithmetic, and the engine returns the right fee either way — so the engine
    # grade alone would pass a rule in which the model never runs.
    called = {text for decision in root.findall("dmn:decision", NS) for text in decision.itertext() if text}
    for model in knowledge_models(root):
        name = model.get("name")
        if not any(f"{name}(" in text for text in called):
            fail(f"no decision's logic calls {name}(...), so the model is wired but never runs")
    for inputs, expected in CASES:
        actual = engine_outputs(project, inputs)
        for name, value in expected.items():
            if actual.get(name) != value:
                fail(f"the engine returned {name}={actual.get(name)!r} for {inputs}, "
                     f"expected {value!r}; it returned {actual}")
    print(f"OK: the engine returns the expected band and fee for all {len(CASES)} cases")


if __name__ == "__main__":
    main()
