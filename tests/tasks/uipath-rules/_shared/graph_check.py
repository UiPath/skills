#!/usr/bin/env python3
"""Shared grading for the uipath-rules decision-graph tasks.

A graph is one `.dmn` whose decisions are linked by `informationRequirement`.
`evaluate_graph` runs every decision table in dependency order, so the tasks
grade what each decision returns instead of how the agent named or shaped it.
The diagram checks compare `DMNShape` positions with the fixture the task
started from. `graph_check.py chain` grades a freshly authored LoanRules
project; `graph_check.py names` checks every table's rule annotations;
`graph_check.py engine` asks the rules engine for the LoanRules values.
"""

from __future__ import annotations

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from rules_check import (
    DMN_NS,
    NS,
    POLICY,
    check_named_rules,
    evaluate,
    fail,
    find_project,
    input_columns,
    load_graph,
    output_names,
    output_properties,
    read_entry_points,
)

DMNDI_NS = "https://www.omg.org/spec/DMN/20230324/DMNDI/"
DC_NS = "http://www.omg.org/spec/DMN/20180521/DC/"
# The size the designer draws each card, whatever width and height the file holds, from
# PO.Frontend DrdLayout.ts on main.
#
# These are deliberately ahead of the CLI. `uip rules format` lays a diagram out with the
# @uipath/dmn-editor-utils the CLI pins, and 0.1272.1 predates PO.Frontend#8458 by two hours:
# it draws inputData at nodeWidth * 0.75 = 216 and has no knowledge-model width at all, so a
# model gets the full 288. A file `format` wrote therefore carries 216 and 288, and is correct
# for the layout it was written by.
#
# Grading against the designer's numbers is the stricter read, and the one that matters: a user
# sees the designer. A diagram clear at 216 but colliding at 240 is a collision they would see.
# Nothing `format` produces today is packed tightly enough for the two to disagree — its stride
# is 336 — and the gap closes when the CLI next bumps the library.
DRAWN_SIZE = {"decision": (288, 96), "inputData": (240, 96),
              "businessKnowledgeModel": (224, 96), "textAnnotation": (224, 64)}

LOAN_PROJECT = "LoanRules"
LOAN_INPUTS = {"creditScore": "number", "income": "number", "loanAmount": "number"}
LOAN_OUTPUTS = {"riskBand": "string", "interestRate": "number"}


def interest_rate(band: str, loan_amount: float) -> float:
    if band == "High":
        return 12.5
    large = loan_amount >= 100000
    return (9 if large else 8) if band == "Medium" else (6 if large else 5.5)


LOAN_CASES = [
    ({**inputs, "loanAmount": amount}, {"riskBand": band, "interestRate": interest_rate(band, amount)})
    for inputs, band in POLICY
    for amount in (20000, 99999, 100000)
]


def decisions(root: ET.Element) -> list[ET.Element]:
    return root.findall("dmn:decision", NS)


def reference_name(decision: ET.Element) -> str:
    """The name a downstream expression reads the decision's result by."""
    variable = decision.find("dmn:variable", NS)
    return (variable.get("name") if variable is not None else None) or decision.get("name") or ""


# Each reference sits inside the requirement element of its own kind, so the holder is not
# always `informationRequirement`: a call to a knowledge model is a `knowledgeRequirement`.
REQUIREMENT_HOLDER = {
    "requiredInput": "informationRequirement",
    "requiredDecision": "informationRequirement",
    "requiredKnowledge": "knowledgeRequirement",
}


def required(element: ET.Element, kind: str) -> list[str]:
    """Ids the element requires; `kind` is `requiredInput`, `requiredDecision` or `requiredKnowledge`."""
    holder = REQUIREMENT_HOLDER[kind]
    return [(e.get("href") or "").lstrip("#")
            for e in element.findall(f"dmn:{holder}/dmn:{kind}", NS)]


def decision_for_output(root: ET.Element, output: str) -> ET.Element:
    """The decision that answers under `output`.

    A decision table answers under its output column names. A decision whose logic is a literal
    expression has no columns and answers under its own name, which is also what a reader of it
    addresses — so it is matched on that. Without this a tableless decision reached
    `output_names(None)` and raised, which failed a correct submission rather than grading it.
    """
    found = []
    for decision in decisions(root):
        table = decision.find("dmn:decisionTable", NS)
        answers = output_names(table) if table is not None else [decision.get("name") or ""]
        if output in answers:
            found.append(decision)
    if len(found) != 1:
        fail(f"{len(found)} decisions return an output named {output}, expected exactly one")
    return found[0]


def resolve(context: dict, path: str) -> tuple[bool, object]:
    """`path` in `context`, where `a.b` reads member `b` of a multi-output decision `a`."""
    value: object = context
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return False, None
        value = value[part]
    return True, value


def evaluate_graph(root: ET.Element, inputs: dict) -> dict:
    """Every decision's outputs by output name, each table reading only what its decision requires."""
    by_id = {d.get("id"): d for d in decisions(root)}
    input_names = {e.get("id"): e.get("name") for e in root.findall("dmn:inputData", NS)}
    hits: dict[str, dict | None] = {}

    def run(decision_id: str, path: tuple[str, ...]) -> None:
        if decision_id in hits:
            return
        if decision_id in path:
            fail(f"the decisions require each other in a cycle: {' -> '.join(path + (decision_id,))}")
        decision = by_id.get(decision_id)
        if decision is None:
            fail(f"a requirement names decision {decision_id}, which the file does not hold")
        context: dict = {}
        for input_id in required(decision, "requiredInput"):
            if input_id not in input_names:
                fail(f"decision {decision.get('name')!r} requires input {input_id}, which the file does not hold")
            context[input_names[input_id]] = inputs.get(input_names[input_id])
        for upstream_id in required(decision, "requiredDecision"):
            run(upstream_id, path + (decision_id,))
            hit = hits[upstream_id]
            single = hit is not None and len(hit) == 1
            context[reference_name(by_id[upstream_id])] = next(iter(hit.values())) if single else hit
        table = decision.find("dmn:decisionTable", NS)
        if table is None:
            hits[decision_id] = None
            return
        values = {}
        for column in input_columns(table):
            found, value = resolve(context, column)
            if not found:
                fail(f"decision {decision.get('name')!r} reads {column!r}, which is not an input or decision it requires")
            values[column] = value
        hits[decision_id] = evaluate(table, values, context)

    for decision_id in by_id:
        run(decision_id, ())
    # Flat, keyed by column name, so two decisions sharing one would overwrite each other and the
    # last in file order would win — a correct graph could fail or a wrong one pass depending on
    # declaration order. `decision_for_output` refuses a duplicate; this path has to as well.
    outputs: dict = {}
    owner: dict[str, str] = {}
    for decision_id, decision in by_id.items():
        table = decision.find("dmn:decisionTable", NS)
        if table is None:
            continue
        for name in output_names(table):
            if name in owner:
                fail(f"decisions {owner[name]!r} and {decision.get('name')!r} both answer with an output "
                     f"named {name!r}; a reader cannot tell them apart")
            owner[name] = decision.get("name") or decision_id
            outputs[name] = (hits[decision_id] or {}).get(name)
    return outputs


def check_graph_cases(root: ET.Element, cases: list) -> None:
    for inputs, expected in cases:
        actual = evaluate_graph(root, inputs)
        for name, value in expected.items():
            if name not in actual:
                fail(f"no decision table returns an output named {name}; a literal expression or a "
                     f"knowledge model is graded by the engine (graph_check.py engine), not here")
            if actual[name] != value:
                fail(f"{inputs} returned {name}={actual[name]!r}, expected {value!r}")


def requires(root: ET.Element, decision: ET.Element, upstream: ET.Element) -> bool:
    """Whether `decision` requires `upstream`, directly or through other decisions."""
    by_id = {d.get("id"): d for d in decisions(root)}
    seen, pending = set(), required(decision, "requiredDecision")
    while pending:
        current = pending.pop()
        if current == upstream.get("id"):
            return True
        if current in seen or current not in by_id:
            continue
        seen.add(current)
        pending += required(by_id[current], "requiredDecision")
    return False


def check_chain(root: ET.Element, downstream_output: str, upstream_output: str) -> None:
    downstream, upstream = decision_for_output(root, downstream_output), decision_for_output(root, upstream_output)
    if downstream is upstream:
        fail(f"{downstream_output} and {upstream_output} come from one decision, expected two")
    if not requires(root, downstream, upstream):
        fail(f"the decision returning {downstream_output} does not require the one returning {upstream_output}")


def check_whole_file_contract(project: Path, dmn_file: Path, inputs: dict, outputs: dict) -> None:
    """The whole-file entry point `uip rules refresh` writes for a graph, carrying every input and output."""
    entry = next((e for e in read_entry_points(project) if e.get("filePath") == f"/{dmn_file.name}"), None)
    if entry is None:
        fail(f"no entry point addresses /{dmn_file.name}; run `uip rules refresh`")
    declared_inputs = (entry.get("input") or {}).get("properties") or {}
    declared_outputs = output_properties(entry.get("output") or {})
    for kind, declared, wanted in (("input", declared_inputs, inputs), ("output", declared_outputs, outputs)):
        for name, json_type in wanted.items():
            if (declared.get(name) or {}).get("type") != json_type:
                fail(f"entry-points.json has no {json_type} {kind} {name}; run `uip rules refresh`")


def check_entry_points_kept(project: Path, fixture: Path) -> None:
    """Every entry point the fixture published keeps its filePath and uniqueId, so bound consumers still resolve."""
    before = json.loads((fixture / "entry-points.json").read_text(encoding="utf-8"))["entryPoints"]
    after = {e.get("filePath"): e.get("uniqueId") for e in read_entry_points(project)}
    for entry in before:
        if after.get(entry["filePath"]) != entry["uniqueId"]:
            fail(f"entry point {entry['filePath']} is gone or has a new uniqueId; consumers bound to it would break")


def shapes(root: ET.Element) -> dict[str, tuple[float, float]]:
    """Where the diagram places each element, by element id."""
    placed = {}
    for shape in root.iter(f"{{{DMNDI_NS}}}DMNShape"):
        bounds = shape.find(f"{{{DC_NS}}}Bounds")
        reference = (shape.get("dmnElementRef") or "").lstrip("#").split(":")[-1]
        if bounds is not None and reference:
            placed[reference] = (float(bounds.get("x", 0)), float(bounds.get("y", 0)))
    return placed


def check_shapes_kept(before: ET.Element, after: ET.Element) -> None:
    """Every shape the fixture placed, for an element the edit kept, is where the user left it."""
    kept = {e.get("id") for e in after}
    now = shapes(after)
    moved = [f"{element} {position} -> {now.get(element)}" for element, position in shapes(before).items()
             if element in kept and now.get(element) != position]
    if moved:
        fail(f"the edit moved or dropped shapes the user had placed: {moved}")


def check_no_overlap(root: ET.Element) -> None:
    """Every drawable element is placed, or none is, and no two cards overlap at the drawn size."""
    kinds = {e.get("id"): e.tag.replace(f"{{{DMN_NS}}}", "") for e in root}
    placed = shapes(root)
    drawable = {element for element, kind in kinds.items() if element and kind in DRAWN_SIZE}
    # No diagram at all is fine: the editor lays one out when it opens a file with no shapes. A
    # partial diagram is not, because it leaves the unplaced elements off the canvas — which is
    # what `uip rules format` prevents. Without this, an element with no shape never enters
    # `boxes` below, so an edit that adds a decision and skips `format` grades as clean.
    missing = sorted(drawable - set(placed))
    if placed and missing:
        fail(f"the diagram places some elements but not {missing}; run 'uip rules format'")
    boxes = [(element, x, y, *DRAWN_SIZE[kinds[element]]) for element, (x, y) in placed.items()
             if kinds.get(element) in DRAWN_SIZE]
    for index, (first, ax, ay, aw, ah) in enumerate(boxes):
        for second, bx, by, bw, bh in boxes[index + 1:]:
            if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
                fail(f"the shapes of {first} and {second} overlap on the canvas")


def knowledge_models(root: ET.Element) -> list[ET.Element]:
    return root.findall("dmn:businessKnowledgeModel", NS)


def check_knowledge_models(root: ET.Element) -> None:
    """Every knowledge model is callable, wired to a caller, and part of no cycle."""
    models = {m.get("id"): m for m in knowledge_models(root)}
    if not models:
        fail("the rule declares no businessKnowledgeModel")
    for model_id, model in models.items():
        name = model.get("name")
        variable = model.find("dmn:variable", NS)
        # The engine rejects a model with no variable and `validate` does not catch it, so the
        # rule would pass every offline check and fail at run time.
        if variable is None or not variable.get("name"):
            fail(f"knowledge model {name or model_id!r} declares no named <variable>; the engine rejects it")
        if variable.get("name") != name:
            fail(f"knowledge model {name!r} has a variable named {variable.get('name')!r}; they must match")
        if model.find("dmn:encapsulatedLogic", NS) is None:
            fail(f"knowledge model {name!r} has no <encapsulatedLogic>, so nothing to call")

    callers = {e.get("id"): required(e, "requiredKnowledge") for e in root
               if e.tag in (f"{{{DMN_NS}}}decision", f"{{{DMN_NS}}}businessKnowledgeModel")}
    for caller_id, needed in callers.items():
        for model_id in needed:
            if model_id not in models:
                fail(f"{caller_id} requires knowledge {model_id}, which the file does not hold")
    wired = {model_id for needed in callers.values() for model_id in needed}
    orphans = sorted(set(models) - wired)
    if orphans:
        fail(f"no decision or knowledge model calls {orphans}; a model nothing requires is dead")

    def walk(model_id: str, path: tuple[str, ...]) -> None:
        if model_id in path:
            fail(f"the knowledge models call each other in a cycle: {' -> '.join(path + (model_id,))}")
        for nxt in callers.get(model_id, []):
            walk(nxt, path + (model_id,))
    for model_id in models:
        walk(model_id, ())


def check_annotations_attached(root: ET.Element) -> None:
    """Every text annotation says something and is tied to an element that is there."""
    notes = {n.get("id"): n for n in root.findall("dmn:textAnnotation", NS)}
    if not notes:
        fail("the rule declares no textAnnotation")
    ids = {e.get("id") for e in root if e.get("id")}
    for note_id, note in notes.items():
        if not (note.findtext("dmn:text", default="", namespaces=NS) or "").strip():
            fail(f"text annotation {note_id} is empty")
    tied = set()
    for association in root.findall("dmn:association", NS):
        # tDMNElementReference: each end is a child element carrying `href`, not an attribute on
        # `<association>`. The attribute spelling parses and validates but the designer reads no
        # ends and drops the connector (PO.Frontend DrdProjection.ts), so it is not accepted here.
        ends = []
        for end in ("sourceRef", "targetRef"):
            child = association.find(f"dmn:{end}", NS)
            if child is None:
                fail(f"association {association.get('id')} has no <{end} href=\"#...\" /> child element"
                     f"; {end} is never an attribute")
            ends.append((child.get("href") or "").lstrip("#"))
        for end in ends:
            if end not in ids:
                fail(f"association {association.get('id')} points at {end}, which the file does not hold")
        tied |= {end for end in ends if end in notes}
    loose = sorted(set(notes) - tied)
    if loose:
        fail(f"text annotations {loose} are tied to nothing; add an <association>")


def check_all_named(root: ET.Element) -> None:
    for decision in decisions(root):
        check_named_rules(decision.find("dmn:decisionTable", NS))


# One case per rate row. Each `rules debug` uploads the solution, so the engine grade keeps to these.
ENGINE_CASES = [case for case in LOAN_CASES if case[0]["loanAmount"] != 99999
                and (case[0]["creditScore"], case[0]["income"]) in ((550, 90000), (580, 50000), (700, 0))]


def engine_outputs(project: Path, inputs: dict) -> dict:
    """What `uip rules debug` returns for `inputs`: every decision's outputs by output name."""
    completed = subprocess.run(
        ["uip", "rules", "debug", str(project), "--inputs", json.dumps(inputs), "--output", "json"],
        capture_output=True, text=True, timeout=180,
    )
    if completed.returncode != 0:
        fail(f"rules debug exited {completed.returncode} for {inputs}: {(completed.stdout or completed.stderr)[-1500:]}")
    result = (json.loads(completed.stdout).get("Data") or {}).get("result") or {}
    outputs: dict = {}
    for decision in result.get("decisions") or []:
        value = decision.get("outputs")
        outputs.update(value if isinstance(value, dict) else {decision.get("decisionName"): value})
    return outputs


def grade_engine() -> None:
    project = find_project(LOAN_PROJECT)
    for inputs, expected in ENGINE_CASES:
        actual = engine_outputs(project, inputs)
        for name, value in expected.items():
            if actual.get(name) != value:
                fail(f"the engine returned {name}={actual.get(name)!r} for {inputs}, expected {value!r}; it returned {actual}")
    print(f"OK: the engine returns the expected risk band and interest rate for all {len(ENGINE_CASES)} cases")


def grade_chain() -> None:
    project = find_project(LOAN_PROJECT)
    dmn_file, root = load_graph(project)
    check_chain(root, "interestRate", "riskBand")
    check_graph_cases(root, LOAN_CASES)
    check_whole_file_contract(project, dmn_file, LOAN_INPUTS, LOAN_OUTPUTS)
    check_no_overlap(root)
    print(f"OK: two chained decisions, the contract is current, no cards overlap, and all {len(LOAN_CASES)} cases match")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    name = sys.argv[2] if len(sys.argv) > 2 else LOAN_PROJECT
    if mode == "chain":
        grade_chain()
    elif mode == "engine":
        grade_engine()
    elif mode == "names":
        check_all_named(load_graph(find_project(name))[1])
        print("OK: every rule of every decision carries an annotation")
    else:
        fail("mode: chain | engine | names [project]")
