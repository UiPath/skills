#!/usr/bin/env python3
"""Shared grading for the uipath-rules decision-graph tasks.

A graph is one `.dmn` whose decisions are linked by `informationRequirement`.
`evaluate_graph` runs every decision table in dependency order, so the tasks
grade what each decision returns instead of how the agent named or shaped it.
The diagram checks compare `DMNShape` positions with the fixture the task
started from. `graph_check.py chain` grades a freshly authored LoanRules
project; `graph_check.py names` checks every table's rule annotations.
"""

from __future__ import annotations

import json
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
# The size the designer draws each card, whatever width and height the file holds.
DRAWN_SIZE = {"decision": (288, 96), "inputData": (216, 96)}

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


def required(decision: ET.Element, kind: str) -> list[str]:
    """Ids the decision requires; `kind` is `requiredInput` or `requiredDecision`."""
    return [(e.get("href") or "").lstrip("#")
            for e in decision.findall(f"dmn:informationRequirement/dmn:{kind}", NS)]


def decision_for_output(root: ET.Element, output: str) -> ET.Element:
    found = [d for d in decisions(root) if output in output_names(d.find("dmn:decisionTable", NS))]
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
        values = {}
        for column in input_columns(table):
            found, value = resolve(context, column)
            if not found:
                fail(f"decision {decision.get('name')!r} reads {column!r}, which is not an input or decision it requires")
            values[column] = value
        hits[decision_id] = evaluate(table, values, context)

    for decision_id in by_id:
        run(decision_id, ())
    outputs: dict = {}
    for decision_id, decision in by_id.items():
        for name in output_names(decision.find("dmn:decisionTable", NS)):
            outputs[name] = (hits[decision_id] or {}).get(name)
    return outputs


def check_graph_cases(root: ET.Element, cases: list) -> None:
    for inputs, expected in cases:
        actual = evaluate_graph(root, inputs)
        for name, value in expected.items():
            if name not in actual:
                fail(f"no decision returns an output named {name}")
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
    """No two placed cards overlap at the size the designer draws them."""
    kinds = {e.get("id"): e.tag.replace(f"{{{DMN_NS}}}", "") for e in root}
    boxes = [(element, x, y, *DRAWN_SIZE[kinds[element]]) for element, (x, y) in shapes(root).items()
             if kinds.get(element) in DRAWN_SIZE]
    for index, (first, ax, ay, aw, ah) in enumerate(boxes):
        for second, bx, by, bw, bh in boxes[index + 1:]:
            if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
                fail(f"the shapes of {first} and {second} overlap on the canvas")


def check_all_named(root: ET.Element) -> None:
    for decision in decisions(root):
        check_named_rules(decision.find("dmn:decisionTable", NS))


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
    elif mode == "names":
        check_all_named(load_graph(find_project(name))[1])
        print("OK: every rule of every decision carries an annotation")
    else:
        fail("mode: chain | names [project]")
