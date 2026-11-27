#!/usr/bin/env python3
"""Shared grading for the uipath-rules tasks.

`rules_check.py validate` passes when `uip rules validate` passes on the
RiskRules project. `rules_check.py format` passes when `uip rules format`, run
on a copy, changes no file. `rules_check.py policy` grades a freshly authored RiskRules
rule: the authoring profile `validate` does not enforce, the entry-point
contract `uip rules refresh` writes, and the table's risk band for each POLICY
case. `rules_check.py names` passes when every rule carries a non-empty
annotation. DMN files are authored by the agent under test and parsed with stdlib
ElementTree.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_NAME = "RiskRules"
DMN_NS = "https://www.omg.org/spec/DMN/20230324/MODEL/"
NS = {"dmn": DMN_NS}
POLICY_INPUTS = {"creditScore": "number", "income": "number"}
POLICY_OUTPUTS = {"riskBand": "string"}
POLICY = [
    ({"creditScore": 550, "income": 90000}, "High"),
    ({"creditScore": 579, "income": 50000}, "High"),
    ({"creditScore": 580, "income": 50000}, "Medium"),
    ({"creditScore": 650, "income": 49999}, "High"),
    ({"creditScore": 699, "income": 75000}, "Medium"),
    ({"creditScore": 700, "income": 0}, "Low"),
    ({"creditScore": 820, "income": 20000}, "Low"),
]
NUMBER = r"-?\d+(?:\.\d+)?"
UIPATH_NS = "http://uipath.com/schema/1.0/dmn/authoring"
# Which editor the designer opens the file in. `uip rules init` scaffolds `decision-table`, and
# that is right for a rule that is one decision table: `decision-graph` opens it on the canvas
# instead, a worse editor for the thing the user asked for. `validate` reports neither.
TABLE_SURFACE, GRAPH_SURFACE = "decision-table", "decision-graph"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def business_rules_projects() -> list[Path]:
    projects = []
    for uiproj in sorted(Path(".").rglob("project.uiproj")):
        try:
            manifest = json.loads(uiproj.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if manifest.get("ProjectType") == "BusinessRules":
            projects.append(uiproj.parent)
    return projects


def find_project(name: str | None = None) -> Path:
    name = name or PROJECT_NAME
    for project in business_rules_projects():
        if json.loads((project / "project.uiproj").read_text(encoding="utf-8")).get("Name") == name:
            return project
    fail(f"no BusinessRules project named {name} found")
    raise AssertionError


def run_validate(project: Path) -> None:
    completed = subprocess.run(
        ["uip", "rules", "validate", str(project), "--output", "json"],
        capture_output=True, text=True, timeout=120,
    )
    if completed.returncode != 0:
        fail(f"`uip rules validate {project}` failed: {(completed.stdout or completed.stderr)[-1500:]}")


def run_format_check(project: Path) -> None:
    """Fails when `uip rules format`, run on a copy, would change a file: the diagram lags the model."""
    with tempfile.TemporaryDirectory() as scratch:
        copy = Path(scratch) / project.name
        shutil.copytree(project, copy)
        completed = subprocess.run(["uip", "rules", "format", str(copy), "--output", "json"],
                                   capture_output=True, text=True, timeout=120)
    if completed.returncode != 0:
        fail(f"`uip rules format {project}` failed: {(completed.stdout or completed.stderr)[-1500:]}")
    try:
        changed = [f.get("File") for f in json.loads(completed.stdout)["Data"]["Files"] if f.get("Changed")]
    except (ValueError, KeyError, TypeError):
        fail(f"`uip rules format` printed no Data.Files: {completed.stdout[-1500:]}")
    if changed:
        fail(f"`uip rules format` still changes {changed}; run it after adding or removing an element")


def load_graph(project: Path) -> tuple[Path, ET.Element]:
    """The project's one `.dmn`, once it holds the profile the skill authors: every decision's logic a decision table or a literal expression, knowledge models, knowledge sources and text annotations allowed, no decision service."""
    dmn_files = list(project.glob("*.dmn"))
    if len(dmn_files) != 1:
        fail(f"expected exactly one .dmn in {project}/, found {len(dmn_files)}")
    text = dmn_files[0].read_text(encoding="utf-8")
    if "<!DOCTYPE" in text or "<!--" in text:
        fail(f"{dmn_files[0]} carries a DOCTYPE or an XML comment")
    if re.search(r"<\?(?!xml\s)", text):
        fail(f"{dmn_files[0]} carries a processing instruction")
    root = ET.fromstring(text)
    if root.tag != f"{{{DMN_NS}}}definitions":
        fail(f"{dmn_files[0]} is not a DMN 1.5 <definitions>")
    if root.findall("dmn:decisionService", NS):
        fail(f"{dmn_files[0]} declares a decisionService")
    decisions = root.findall("dmn:decision", NS)
    if not decisions:
        fail(f"{dmn_files[0]} holds no decision")
    for decision in decisions:
        if decision.find("dmn:decisionTable", NS) is None and decision.find("dmn:literalExpression", NS) is None:
            fail(f"{dmn_files[0]}: the logic of decision {decision.get('name')!r} is neither a decisionTable nor a literalExpression")
    check_authoring_surface(dmn_files[0], root)
    return dmn_files[0], root


def check_authoring_surface(dmn_file: Path, root: ET.Element) -> None:
    """The authoring surface agrees with what the file holds.

    Nothing graded this and `validate` reports neither value, so a rule authored with the wrong
    surface passed every task in the suite. Agents reached for `decision-graph` on single-table
    rules because the skill documented no other value.

    Only the two shapes the product pins are asserted. A single decision whose logic is a literal
    expression is left alone: `editor` is per-decision, and which surface the designer wants for
    that file is not something this suite can evidence.
    """
    element = root.find("dmn:extensionElements/uipath:authoring", {**NS, "uipath": UIPATH_NS})
    surface = element.get("surface") if element is not None else None
    if not surface:
        fail(f"{dmn_file} declares no <uipath:authoring surface=\"...\" /> in the definitions' "
             f"<extensionElements>; without it the designer cannot tell which editor to open")
    if surface not in (TABLE_SURFACE, GRAPH_SURFACE):
        fail(f"{dmn_file} declares surface {surface!r}; the designer reads {TABLE_SURFACE!r} or "
             f"{GRAPH_SURFACE!r}")
    decisions = root.findall("dmn:decision", NS)
    canvas_only = (root.findall("dmn:businessKnowledgeModel", NS)
                   + root.findall("dmn:knowledgeSource", NS)
                   + root.findall("dmn:textAnnotation", NS))
    if (len(decisions) > 1 or canvas_only) and surface != GRAPH_SURFACE:
        reason = ("holds several decisions" if len(decisions) > 1
                  else "holds a knowledge model, knowledge source or text annotation, which only the canvas draws")
        fail(f"{dmn_file} {reason} but declares surface {surface!r}; it opens as a bare table and "
             f"the requirement edges are invisible. Use {GRAPH_SURFACE!r}")
    one_table = (len(decisions) == 1 and not canvas_only
                 and decisions[0].find("dmn:decisionTable", NS) is not None)
    if one_table and surface != TABLE_SURFACE:
        fail(f"{dmn_file} is one decision table and nothing else, but declares surface {surface!r}; "
             f"that opens it on the graph canvas instead of the table editor. `uip rules init` "
             f"scaffolds {TABLE_SURFACE!r} — leave it as it is")


def load_rule(project: Path) -> tuple[Path, ET.Element]:
    """`load_graph`, for a rule that must hold exactly one decision."""
    dmn_file, root = load_graph(project)
    decisions = root.findall("dmn:decision", NS)
    if len(decisions) != 1:
        fail(f"{dmn_file} holds {len(decisions)} decisions, expected exactly one")
    return dmn_file, root


def decision_of(root: ET.Element) -> ET.Element:
    return root.find("dmn:decision", NS)


def table_of(root: ET.Element) -> ET.Element:
    return decision_of(root).find("dmn:decisionTable", NS)


def input_columns(table: ET.Element) -> list[str]:
    return [(i.findtext("dmn:inputExpression/dmn:text", default="", namespaces=NS) or "").strip()
            for i in table.findall("dmn:input", NS)]


def output_names(table: ET.Element) -> list[str]:
    return [o.get("name") or "" for o in table.findall("dmn:output", NS)]


def annotations(table: ET.Element) -> list[str]:
    return [(rule.findtext("dmn:annotationEntry/dmn:text", default="", namespaces=NS) or "").strip()
            for rule in table.findall("dmn:rule", NS)]


def check_annotations_in_order(table: ET.Element, expected: list[str]) -> None:
    remaining = iter(annotations(table))
    if not all(text in remaining for text in expected):
        fail(f"the rows' annotations read {annotations(table)}, expected {expected} among them in that order")


def check_named_rules(table: ET.Element | None) -> None:
    # A literal expression has no rules, so no annotation column and nothing to name.
    if table is None:
        return
    clauses = len(table.findall("dmn:annotation", NS))
    if clauses != 1:
        fail(f"the table declares {clauses} <annotation> columns, expected 1")
    miscounted = [index + 1 for index, rule in enumerate(table.findall("dmn:rule", NS))
                  if len(rule.findall("dmn:annotationEntry", NS)) != 1]
    if miscounted:
        fail(f"rows {miscounted} do not carry exactly one annotationEntry for the one annotation column")
    inputs, outputs = len(table.findall("dmn:input", NS)), len(table.findall("dmn:output", NS))
    ragged = [index + 1 for index, rule in enumerate(table.findall("dmn:rule", NS))
              if len(rule.findall("dmn:inputEntry", NS)) != inputs
              or len(rule.findall("dmn:outputEntry", NS)) != outputs]
    if ragged:
        fail(f"rows {ragged} do not carry one entry per input and output column")
    unnamed = [index + 1 for index, text in enumerate(annotations(table)) if not text]
    if unnamed:
        fail(f"rows {unnamed} have no annotation; every rule needs a name")


def check_input_data(root: ET.Element, inputs: dict[str, str]) -> None:
    declared = {e.get("name"): e.find("dmn:variable", NS) for e in root.findall("dmn:inputData", NS)}
    columns = input_columns(table_of(root))
    for name, type_ref in inputs.items():
        variable = declared.get(name)
        if variable is None or variable.get("typeRef") != type_ref:
            fail(f"input argument {name} is missing or not typed {type_ref}")
        if name not in columns:
            fail(f"no input column reads {name}")


def read_entry_points(project: Path) -> list:
    try:
        return json.loads((project / "entry-points.json").read_text(encoding="utf-8"))["entryPoints"]
    except (OSError, ValueError, KeyError):
        fail(f"{project}/entry-points.json is missing or unreadable")
        raise AssertionError


def output_properties(schema: dict) -> dict:
    """Output argument schemas by name; a decision-keyed schema nests them under each decision."""
    properties = schema.get("properties") or {}
    if not schema.get("x-uipath-decision-keyed"):
        return properties
    return {name: prop for decision in properties.values() for name, prop in (decision.get("properties") or {}).items()}


def check_contract(project: Path, dmn_file: Path, root: ET.Element, inputs: dict, outputs: dict, whole_file: bool = False) -> dict:
    """The entry point addressing the decision (or, with `whole_file`, the file), carrying the contract `uip rules refresh` writes; returns it."""
    file_path = f"/{dmn_file.name}" if whole_file else f"/{dmn_file.name}#{decision_of(root).get('id')}"
    entry = next((e for e in read_entry_points(project) if e.get("filePath") == file_path), None)
    if entry is None:
        fail(f"no entry point addresses {file_path}; the decision id or file name changed")
    declared_inputs = (entry.get("input") or {}).get("properties") or {}
    for name, json_type in inputs.items():
        if (declared_inputs.get(name) or {}).get("type") != json_type:
            fail(f"entry-points.json has no {json_type} input {name}; run `uip rules refresh`")
    declared_outputs = output_properties(entry.get("output") or {})
    for name, json_type in outputs.items():
        if (declared_outputs.get(name) or {}).get("type") != json_type:
            fail(f"entry-points.json has no {json_type} output {name}; run `uip rules refresh`")
    return entry


def unary_test(cell: str, value: object) -> bool:
    """Evaluates the FEEL unary tests a numeric, boolean, or string column uses."""
    cell = cell.strip()
    if cell in ("", "-"):
        return True
    negated = re.fullmatch(r"not\s*\((.*)\)", cell)
    if negated:
        return not unary_test(negated.group(1), value)
    # Commas outside quotes separate alternatives: `< 10, > 90` and `"High", "Medium"`.
    parts = [part.strip() for part in re.findall(r'(?:"[^"]*"|[^,])+', cell)]
    if len(parts) > 1:
        return any(unary_test(part, value) for part in parts)
    if value is None:
        return False
    if cell in ("true", "false"):
        return value is (cell == "true")
    if re.fullmatch(r'"[^"]*"', cell):
        return value == cell[1:-1]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        fail(f"cell {cell!r} tests a non-numeric value {value!r}")
    match = re.fullmatch(rf"(<=|>=|<|>|=)?\s*({NUMBER})", cell)
    if match:
        op, number = match.group(1) or "=", float(match.group(2))
        return {"<": value < number, "<=": value <= number, ">": value > number,
                ">=": value >= number, "=": value == number}[op]
    match = re.fullmatch(rf"([\[\(\]])\s*({NUMBER})\s*\.\.\s*({NUMBER})\s*([\]\)\[])", cell)
    if match:
        low, high = float(match.group(2)), float(match.group(3))
        above = value >= low if match.group(1) == "[" else value > low
        below = value <= high if match.group(4) == "]" else value < high
        return above and below
    fail(f"input cell {cell!r} is outside the unary tests this check evaluates")
    raise AssertionError


class _Unevaluable:
    """A cell the offline evaluator cannot read — a call or a formula, which only the engine runs."""

    def __repr__(self) -> str:
        return "<unevaluable: a call or a formula>"


UNEVALUABLE = _Unevaluable()


def literal(text: str) -> object:
    text = text.strip()
    if re.fullmatch(r'"[^"]*"', text):
        return text[1:-1]
    if re.fullmatch(NUMBER, text):
        return float(text)
    if text in ("true", "false"):
        return text == "true"
    # The FEEL constructors for the designer's own types. Critical Rule 5 offers date, time,
    # date and time, and both durations as column types, so a cell spelling one of them is a
    # literal like any other and is kept as its source text for comparison.
    if re.fullmatch(r'(date and time|date|time|duration)\s*\(\s*"[^"]*"\s*\)', text):
        return text
    # Anything else carrying a call or an operator is neither a literal nor a name. Returning the
    # raw source would grade `scoreModel(1)` as the string "scoreModel(1)" and silently mark a
    # correct rule wrong, so the cell is answered as unevaluable and the caller decides. Failing
    # here instead aborted a whole graph on a cell no case asked about.
    if re.search(r"[()+*/]|(?<![<>=!])-(?!\s*$)", text):
        return UNEVALUABLE
    return text


def read_name(names: dict, text: str) -> tuple[bool, object]:
    """`text` as a name the table may read, plain or dotted, resolved against `names`.

    A decision whose table has one output answers with that value, so a reader names it bare.
    A decision with several answers with a structure, so a reader names one field of it —
    `risk.riskBand`, which the guide documents. Without this the dotted form fell through to
    `literal` and graded as its own source text, which is a wrong value and never an error.
    """
    parts = text.strip().split(".")
    if parts[0] not in names:
        return False, None
    value: object = names[parts[0]]
    for part in parts[1:]:
        if not isinstance(value, dict) or part not in value:
            return False, None
        value = value[part]
    return True, value


def evaluate(table: ET.Element, inputs: dict, names: dict | None = None) -> dict | None:
    """The single result the table's hit policy returns, keyed by output name.

    An output entry that is one of `names` returns that name's value, as a
    decision that passes an upstream result through does.
    """
    names = names or {}
    columns = input_columns(table)
    policy = table.get("hitPolicy", "UNIQUE")
    if policy not in ("FIRST", "UNIQUE", "ANY"):
        fail(f"hit policy {policy} is outside the single-result policies this check evaluates")
    hits = []
    for rule in table.findall("dmn:rule", NS):
        cells = [(e.findtext("dmn:text", default="", namespaces=NS) or "") for e in rule.findall("dmn:inputEntry", NS)]
        if len(cells) != len(columns):
            fail("a rule's input entries do not match the input columns")
        if all(unary_test(cell, inputs[column]) for cell, column in zip(cells, columns) if column in inputs):
            values = [(e.findtext("dmn:text", default="", namespaces=NS) or "") for e in rule.findall("dmn:outputEntry", NS)]
            resolved = []
            for value in values:
                found, read = read_name(names, value)
                resolved.append(read if found else literal(value))
            hits.append(dict(zip(output_names(table), resolved)))
            # FIRST answers with this row, so the rows below it are never evaluated. Reading them
            # anyway means a later fallback row holding a call or a formula aborts grading on
            # `literal()`'s refusal, though the engine would never have looked at it.
            if policy == "FIRST":
                break
    if policy == "UNIQUE" and len(hits) > 1:
        fail(f"{inputs} matches {len(hits)} rows of a UNIQUE table")
    if policy == "ANY" and any(hit != hits[0] for hit in hits):
        fail(f"{inputs} matches rows of an ANY table with different outputs")
    return hits[0] if hits else None


def check_cases(table: ET.Element, output: str, cases: list) -> None:
    for inputs, expected in cases:
        actual = (evaluate(table, inputs) or {}).get(output)
        if actual is UNEVALUABLE:
            fail(f"output {output} for {inputs} is a call or a formula; grade it with 'graph_check.py engine'")
        if actual != expected:
            fail(f"{inputs} returned {actual!r}, expected {expected!r}")


def grade_policy() -> None:
    project = find_project()
    dmn_file, root = load_rule(project)
    check_input_data(root, POLICY_INPUTS)
    if output_names(table_of(root)) != list(POLICY_OUTPUTS):
        fail(f"output columns are {output_names(table_of(root))}, expected {list(POLICY_OUTPUTS)}")
    check_contract(project, dmn_file, root, POLICY_INPUTS, POLICY_OUTPUTS)
    check_cases(table_of(root), "riskBand", POLICY)
    print(f"OK: profile holds, the entry point carries the contract, and all {len(POLICY)} cases match")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "policy"
    name = sys.argv[2] if len(sys.argv) > 2 else None
    if mode == "validate":
        run_validate(find_project(name))
        print("OK: uip rules validate passes")
    elif mode == "format":
        run_format_check(find_project(name))
        print("OK: uip rules format changes nothing")
    elif mode == "policy":
        grade_policy()
    elif mode == "names":
        check_named_rules(table_of(load_rule(find_project())[1]))
        print("OK: every rule carries an annotation")
    else:
        fail(f"unknown mode {mode!r}")
