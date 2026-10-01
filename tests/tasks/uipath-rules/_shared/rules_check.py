#!/usr/bin/env python3
"""Shared grading for the uipath-rules tasks.

`rules_check.py validate` passes when `uip rules validate` passes on the
RiskRules project. `rules_check.py policy` grades a freshly authored RiskRules
rule: the authoring profile `validate` does not enforce, the entry-point
contract `uip rules refresh` writes, and the table's risk band for each POLICY
case. DMN files are authored by the agent under test and parsed with stdlib
ElementTree.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
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


def find_project(name: str = PROJECT_NAME) -> Path:
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


def load_rule(project: Path) -> tuple[Path, ET.Element]:
    """The project's one `.dmn`, once it holds the profile `validate` deliberately accepts."""
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
    for unsupported in ("businessKnowledgeModel", "knowledgeSource", "decisionService"):
        if root.findall(f"dmn:{unsupported}", NS):
            fail(f"{dmn_files[0]} declares a {unsupported}")
    decisions = root.findall("dmn:decision", NS)
    if len(decisions) != 1:
        fail(f"{dmn_files[0]} holds {len(decisions)} decisions, expected exactly one")
    if decisions[0].find("dmn:decisionTable", NS) is None:
        fail(f"{dmn_files[0]}: the decision's logic is not a decisionTable")
    return dmn_files[0], root


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


def check_contract(project: Path, dmn_file: Path, root: ET.Element, inputs: dict, outputs: dict) -> dict:
    """The entry point addressing the decision, carrying the contract `uip rules refresh` writes; returns it."""
    file_path = f"/{dmn_file.name}#{decision_of(root).get('id')}"
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
    if "," in cell and not cell.startswith('"'):
        return any(unary_test(part, value) for part in cell.split(","))
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


def literal(text: str) -> object:
    text = text.strip()
    if re.fullmatch(r'"[^"]*"', text):
        return text[1:-1]
    if re.fullmatch(NUMBER, text):
        return float(text)
    if text in ("true", "false"):
        return text == "true"
    return text


def evaluate(table: ET.Element, inputs: dict) -> dict | None:
    """The single result the table's hit policy returns, keyed by output name."""
    columns = input_columns(table)
    names = output_names(table)
    hits = []
    for rule in table.findall("dmn:rule", NS):
        cells = [(e.findtext("dmn:text", default="", namespaces=NS) or "") for e in rule.findall("dmn:inputEntry", NS)]
        if len(cells) != len(columns):
            fail("a rule's input entries do not match the input columns")
        if all(unary_test(cell, inputs[column]) for cell, column in zip(cells, columns) if column in inputs):
            values = [(e.findtext("dmn:text", default="", namespaces=NS) or "") for e in rule.findall("dmn:outputEntry", NS)]
            hits.append({name: literal(value) for name, value in zip(names, values)})
    policy = table.get("hitPolicy", "UNIQUE")
    if policy == "UNIQUE" and len(hits) > 1:
        fail(f"{inputs} matches {len(hits)} rows of a UNIQUE table")
    if policy == "ANY" and any(hit != hits[0] for hit in hits):
        fail(f"{inputs} matches rows of an ANY table with different outputs")
    if policy not in ("FIRST", "UNIQUE", "ANY"):
        fail(f"hit policy {policy} is outside the single-result policies this check evaluates")
    return hits[0] if hits else None


def check_cases(table: ET.Element, output: str, cases: list) -> None:
    for inputs, expected in cases:
        actual = (evaluate(table, inputs) or {}).get(output)
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
    if mode == "validate":
        run_validate(find_project())
        print("OK: uip rules validate passes")
    elif mode == "policy":
        grade_policy()
    else:
        fail(f"unknown mode {mode!r}")
