#!/usr/bin/env python3
"""Grades FeeRules through the rules engine: a literal expression and a knowledge model call.

The offline evaluator reads decision-table cells only, so arithmetic and a call
to a knowledge model are graded here, by the engine that actually runs them.
Few cases on purpose: each `uip rules debug` uploads the whole solution.

Three cases for the values, then one more with the model's rates doubled. The
static checks say the file carries a call; only varying what the model answers
says the fee is computed by it.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from graph_check import (  # noqa: E402
    check_knowledge_models,
    check_model_called,
    decision_for_output,
    engine_outputs,
    knowledge_models,
    same_value,
)
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

    # Declared and wired is not called, and the engine returns the right fee either way — so the
    # engine grade alone would pass a rule whose model never runs. Graded on the decision the
    # prompt names, through the FEEL it actually evaluates: a rule may inline the rates and put
    # the model's name in an annotation beside them, which reads as a call to a text search.
    fee = decision_for_output(root, "fee")
    if fee.find("dmn:literalExpression", NS) is None:
        fail("the fee decision's logic is not a literalExpression; the fee was asked for as a formula")
    for model in knowledge_models(root):
        check_model_called(root, fee, model.get("name") or "")
    for inputs, expected in CASES:
        actual = engine_outputs(project, inputs)
        for name, value in expected.items():
            if not same_value(actual.get(name), value):
                fail(f"the engine returned {name}={actual.get(name)!r} for {inputs}, "
                     f"expected {value!r}; it returned {actual}")
    _fee_follows_the_model(project)
    print(f"OK: the engine returns the expected band and fee for all {len(CASES)} cases, "
          f"and the fee follows the model's rates")


def _fee_follows_the_model(project: Path) -> None:
    """Change the model's rates and the fee has to change with them.

    A call in a branch the inputs never reach, with the correct rates inlined in the branch they
    do, satisfies both the call check above and all three cases — the model is declared, wired,
    called somewhere, and the fee is still right. Nothing static distinguishes that from a fee
    the model actually computes.

    Doubling every number in the model's body doubles the rate it answers with, so a fee that
    comes from the model doubles too and one that does not stays where it was. The body holds
    nothing but the rates: the model takes the band and answers a rate, and the band is a
    separate decision this never touches. Restored in `finally`, so a failure here leaves the
    agent's file as it was.
    """
    dmn_file = load_graph(project)[0]
    before = dmn_file.read_text(encoding="utf-8")
    body = re.search(r"<(\w+:)?businessKnowledgeModel\b.*?</(\w+:)?businessKnowledgeModel>", before, re.S)
    if body is None:
        fail("the rule declares no businessKnowledgeModel to vary; check_knowledge_models should have said so")
    # Only inside `<text>`, which is where FEEL lives: an id, a label or a typeRef is not a rate,
    # and rewriting a numeric id would break the references to it.
    def double(cell: re.Match[str]) -> str:
        return re.sub(r"(?<![\w.])\d+(\.\d+)?(?![\w.])",
                      lambda number: repr(float(number.group(0)) * 2), cell.group(0))

    doubled = re.sub(r"<(\w+:)?text>.*?</(\w+:)?text>", double, body.group(0), flags=re.S)
    if doubled == body.group(0):
        fail("the knowledge model's body holds no number to vary, so its rates are not in it")
    # One case, not all three: each `rules debug` uploads the whole solution, and one band is
    # enough to show the fee tracks the model.
    inputs, expected = CASES[-1]
    try:
        dmn_file.write_text(before.replace(body.group(0), doubled, 1), encoding="utf-8")
        actual = engine_outputs(project, inputs)
        if not same_value(actual.get("fee"), expected["fee"] * 2):
            fail(f"with the model's rates doubled the engine returned fee={actual.get('fee')!r} for "
                 f"{inputs}, expected {expected['fee'] * 2}; the fee does not come from the model, so "
                 f"the call the file carries is not what computes it")
    finally:
        dmn_file.write_text(before, encoding="utf-8")


if __name__ == "__main__":
    main()
