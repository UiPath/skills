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
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from graph_check import (  # noqa: E402
    check_knowledge_models,
    check_model_called,
    decision_for_output,
    engine_outputs,
    knowledge_models,
    required,
    same_value,
)
from rules_check import NS, fail, find_project, load_graph  # noqa: E402

PROJECT = "FeeRules"
# Either side of the 50000 band edge, and one large loan.
# What the model is made to answer while probing. Not a rate any band uses, so a hardcoded rate
# cannot match it by accident.
PROBE_RATE = 0.5

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
    """The fee has to follow what the model answers, not merely call it somewhere.

    The model's body becomes a constant while its signature stays, so a fee the model computes
    becomes `loanAmount * PROBE_RATE` for every band and a fee with the rates inlined does not
    move. Run in a copy of the solution, so a grader killed mid-run leaves the agent's project
    as it was.
    """
    probe = Path(tempfile.mkdtemp(prefix=".mutation-probe-", dir=project.parent.parent)) / project.parent.name
    try:
        shutil.copytree(project.parent, probe)
        copied = probe / project.name
        dmn_file = load_graph(copied)[0]
        before = dmn_file.read_text(encoding="utf-8")
        mutated = _model_answers(before, _the_model_the_fee_calls(load_graph(copied)[1]), PROBE_RATE)
        dmn_file.write_text(mutated, encoding="utf-8")
        # One input from each band: a fee that calls the model for Large and hardcodes Small's
        # rate passes every case above and a probe that only exercises Large.
        for inputs in ({"loanAmount": 20000}, {"loanAmount": 200000}):
            actual = engine_outputs(copied, inputs)
            expected = inputs["loanAmount"] * PROBE_RATE
            if not same_value(actual.get("fee"), expected):
                fail(f"with the model answering a flat {PROBE_RATE} the engine returned "
                     f"fee={actual.get('fee')!r} for {inputs}, expected {expected}; the fee for that "
                     f"band does not come from the model, so the call the file carries is not what "
                     f"computes it")
    finally:
        shutil.rmtree(probe.parent, ignore_errors=True)


def _the_model_the_fee_calls(root: ET.Element) -> str:
    """The id of the one knowledge model the fee requires.

    Not the first model in the file: a rule may declare a helper beside the rate model, and
    replacing the helper's body would leave the fee unchanged and fail work that is correct.
    """
    needed = required(decision_for_output(root, "fee"), "requiredKnowledge")
    if len(needed) != 1:
        fail(f"the fee requires {len(needed)} knowledge models ({needed}); this probe varies the one "
             f"the fee calls, and with several the fee it should answer is not determined")
    return needed[0]


def _model_answers(xml: str, model_id: str, rate: float) -> str:
    """`xml` with that knowledge model's body replaced by a constant, its parameters untouched."""
    model = re.search(rf"<(\w+:)?businessKnowledgeModel\b[^>]*\bid=\"{re.escape(model_id)}\".*?"
                      rf"</(\w+:)?businessKnowledgeModel>", xml, re.S)
    if model is None:
        fail(f"the file holds no businessKnowledgeModel with id {model_id!r}")
    body = re.search(r"(<(\w+:)?encapsulatedLogic\b[^>]*>)(.*?)(</(\w+:)?encapsulatedLogic>)",
                     model.group(0), re.S)
    if body is None:
        fail("the knowledge model declares no <encapsulatedLogic>; check_knowledge_models should have said so")
    parameters = "".join(re.findall(r"<(?:\w+:)?formalParameter\b[^>]*/>", body.group(3)))
    if not parameters:
        fail("the knowledge model declares no <formalParameter>, so its callers pass nothing")
    constant = (f'<literalExpression id="literalExpression_probe" typeRef="number">'
                f"<text>{rate}</text></literalExpression>")
    return xml.replace(model.group(0),
                       model.group(0).replace(body.group(0),
                                              body.group(1) + parameters + constant + body.group(4), 1), 1)
