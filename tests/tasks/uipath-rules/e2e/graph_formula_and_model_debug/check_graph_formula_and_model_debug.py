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
from rules_check import DMN_NS, NS, fail, find_project, load_graph  # noqa: E402

# A defect in this probe is not a defect in the agent's rule. The probe rewrites the model's body
# and re-runs the engine, so a rewrite that produces a file the engine will not read looks exactly
# like a fee that ignores the model -- and the harness scores a non-zero exit the same either way.
# Everything the probe does to the file exits here instead, with its own code and a prefix no
# grading message carries, so a run that trips it is read as "the probe broke", not "the fee is
# hardcoded".
PROBE_DEFECT_EXIT = 3
# The temp directory's prefix, named once: the copy skips anything matching it, so the probe
# cannot copy its own working directory into the copy it is making.
PROBE_PREFIX = ".mutation-probe-"


def probe_defect(message: str) -> None:
    print(f"PROBE DEFECT: {message}")
    print("This is a defect in the grader's mutation probe, not in the rule under test; "
          "the fee was neither confirmed nor refuted.")
    sys.exit(PROBE_DEFECT_EXIT)


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
    # The model the fee requires, by name -- `check_model_called` matches on the name, while
    # `_the_model_the_fee_calls` answers with the id. Looping over every model in the file instead
    # demanded the fee call a helper declared beside the rate model, which failed correct work.
    check_model_called(root, fee, _model_name(root, _the_model_the_fee_calls(root)))
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
    # The temp root in its own variable, and the copy under a name of this grader's choosing.
    # Deriving the copy's name from `project.parent.name` left it empty for the root-level layout
    # `uip solution init .` produces (the solution *is* the sandbox, so the project's parent has
    # no name) -- which made the copy the temp root itself, `probe.parent` the sandbox, and the
    # `finally` below delete the grader's whole working directory.
    temp_root = Path(tempfile.mkdtemp(prefix=PROBE_PREFIX, dir=project.parent.parent))
    try:
        probe = temp_root / "solution"
        # The temp root sits inside the tree being copied under that same layout, so it would
        # otherwise be copied into itself.
        shutil.copytree(project.parent, probe, ignore=shutil.ignore_patterns(f"{PROBE_PREFIX}*"))
        copied = probe / project.name
        dmn_file, copied_root = load_graph(copied)
        _model_answers(copied_root, _the_model_the_fee_calls(copied_root), PROBE_RATE)
        _write(dmn_file, copied_root)
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
        shutil.rmtree(temp_root, ignore_errors=True)


def _model_name(root: ET.Element, model_id: str) -> str:
    """The name of the knowledge model with `model_id`."""
    for model in knowledge_models(root):
        if model.get("id") == model_id:
            return model.get("name") or ""
    fail(f"the file holds no businessKnowledgeModel with id {model_id!r}")
    raise AssertionError


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


def _model_answers(root: ET.Element, model_id: str, rate: float) -> None:
    """Replace that knowledge model's body with a constant, in place, its parameters untouched.

    Built on the parsed tree rather than by rewriting the file's text. A regex rewrite wrote the
    constant as a bare `<literalExpression>`, which lands in no namespace at all in a file whose
    DMN elements carry a prefix -- and `uip rules format` preserves it and `validate` passes it
    clean, so the probe silently measured a model the engine never saw. Keeping the parameter
    *elements* rather than re-emitting the text that matched a self-closing-tag regex also keeps
    the signature intact when a parameter carries a `<description>` child; re-emitting dropped
    those parameters and changed the model's arity.
    """
    model = next((m for m in knowledge_models(root) if m.get("id") == model_id), None)
    if model is None:
        probe_defect(f"the copied file holds no businessKnowledgeModel with id {model_id!r}")
    logic = model.find("dmn:encapsulatedLogic", NS)
    if logic is None:
        probe_defect(f"knowledge model {model.get('name')!r} declares no <encapsulatedLogic>; "
                     f"check_knowledge_models should have refused it before the probe ran")
    parameters = logic.findall("dmn:formalParameter", NS)
    if not parameters:
        probe_defect(f"knowledge model {model.get('name')!r} declares no <formalParameter>, so its "
                     f"callers pass nothing and varying what it answers proves nothing")
    for child in list(logic):
        logic.remove(child)
    for parameter in parameters:
        logic.append(parameter)
    constant = ET.SubElement(logic, f"{{{DMN_NS}}}literalExpression")
    constant.set("id", "literalExpression_probe")
    constant.set("typeRef", "number")
    ET.SubElement(constant, f"{{{DMN_NS}}}text").text = str(rate)


def _write(dmn_file: Path, root: ET.Element) -> None:
    """The mutated tree back to disk, every prefix the file declared still bound.

    ElementTree renames the prefixes it keeps to `ns0`, `ns1`... and drops the declarations it
    reads as unused. A DMN file addresses its own elements through the `tns:` prefix it declares
    for its target namespace, and an `href` is an attribute value ElementTree copies verbatim --
    so a dropped declaration leaves the engine a reference to a prefix the file no longer binds.
    Re-registering what the file itself declared keeps the serialised copy readable by whatever
    read the original.
    """
    parser = ET.XMLPullParser(events=["start-ns"])
    parser.feed(dmn_file.read_bytes())
    declared = [pair for _, pair in parser.read_events()]
    parser.close()
    # Re-declared literally rather than only registered. `register_namespace` sets the prefix
    # ElementTree *prefers* for a namespace it is already emitting; it does not make it emit a
    # declaration nothing in the tree uses. A prefix used only inside an attribute value is
    # exactly that case, so writing them back as attributes is what keeps the reference bound.
    for prefix, uri in declared:
        ET.register_namespace(prefix, uri)
        if prefix:
            root.set(f"xmlns:{prefix}", uri)
    # The DMN namespace unprefixed, so the constant the probe injected -- which carries the
    # namespace and no prefix of its own -- serialises as a plain `<literalExpression>`.
    ET.register_namespace("", DMN_NS)
    ET.ElementTree(root).write(dmn_file, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    main()
