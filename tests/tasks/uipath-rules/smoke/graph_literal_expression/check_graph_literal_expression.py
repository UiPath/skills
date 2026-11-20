#!/usr/bin/env python3
"""Grades FeeRules, whose fee decision is a literal expression rather than a table.

Structure only: the formula is FEEL the offline evaluator does not run, so its
arithmetic is graded by the engine in the e2e task. The band decision beside it
is a table, so its values are graded here.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from graph_check import check_chain, check_graph_cases, check_no_overlap  # noqa: E402
from rules_check import NS, fail, find_project, load_graph  # noqa: E402

PROJECT = "FeeRules"
BANDS = [({"loanAmount": amount}, {"band": band})
         for amount, band in ((0, "Small"), (49999, "Small"), (50000, "Large"), (250000, "Large"))]


def main() -> None:
    _, root = load_graph(find_project(PROJECT))

    literal_decisions = [d for d in root.findall("dmn:decision", NS)
                         if d.find("dmn:literalExpression", NS) is not None]
    if not literal_decisions:
        fail("no decision's logic is a literalExpression; the fee was asked for as a formula")

    for decision in literal_decisions:
        name = decision.get("name")
        expression = decision.find("dmn:literalExpression", NS)
        if not (expression.get("typeRef") or "").strip():
            fail(f"the literal expression of {name!r} declares no typeRef; validate reports DMN_LITERAL_EXPRESSION_TYPE_MISSING")
        if not (expression.findtext("dmn:text", default="", namespaces=NS) or "").strip():
            fail(f"the literal expression of {name!r} is empty")
        variable = decision.find("dmn:variable", NS)
        if variable is None or variable.get("name") != name:
            fail(f"decision {name!r} has no <variable> of its own name")
        if decision.find("dmn:decisionTable", NS) is not None:
            fail(f"decision {name!r} carries both a table and a literal expression")
        if decision.findall("dmn:decisionTable/dmn:annotation", NS):
            fail(f"decision {name!r} carries an annotation column but has no rules")
        if not decision.findall("dmn:informationRequirement/*", NS):
            fail(f"decision {name!r} reads nothing; a formula over no input is a constant")

    check_chain(root, "fee", "band")
    check_graph_cases(root, BANDS)
    check_no_overlap(root)
    print(f"OK: the fee is a typed literal expression over the band, and all {len(BANDS)} band cases match")


if __name__ == "__main__":
    main()
