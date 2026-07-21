#!/usr/bin/env python3
"""Grade declaration-complete BPMN projection from either supported SDD shape."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _shared.bpmn_assertions import (  # noqa: E402
    BPMNDI_NS,
    BPMN_NS,
    UIPATH_NS,
    assert_package_lifecycle,
    fail,
    load_bpmn,
)


PROJECT = Path("LoanOriginationBpmn")
BPMN_NAME = "LoanOriginationBpmn.bpmn"
BPMN = PROJECT / BPMN_NAME


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def clean_cell(value: str) -> str:
    return re.sub(r"[`*_]", "", value).strip()


def header_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", clean_cell(value).lower()).strip()


def parse_markdown_tables(text: str) -> list[list[dict[str, str]]]:
    lines = text.splitlines()
    tables: list[list[dict[str, str]]] = []
    index = 0
    while index + 1 < len(lines):
        if not lines[index].lstrip().startswith("|") or not re.match(
            r"^\s*\|?(?:\s*:?-+:?\s*\|)+\s*$", lines[index + 1]
        ):
            index += 1
            continue
        headers = [header_key(cell) for cell in lines[index].strip().strip("|").split("|")]
        index += 2
        rows: list[dict[str, str]] = []
        while index < len(lines) and lines[index].lstrip().startswith("|"):
            cells = [clean_cell(cell) for cell in lines[index].strip().strip("|").split("|")]
            if len(cells) == len(headers):
                rows.append(dict(zip(headers, cells)))
            index += 1
        if rows:
            tables.append(rows)
    return tables


def table_with(tables: list[list[dict[str, str]]], *required: tuple[str, ...]):
    for table in tables:
        keys = set(table[0])
        if all(any(header_key(alias) in keys for alias in aliases) for aliases in required):
            return table
    fail(f"supplied SDD is missing a required semantic table: {required}")


def cell(row: dict[str, str], *aliases: str) -> str:
    for alias in aliases:
        value = row.get(header_key(alias))
        if value is not None:
            return value
    fail(f"SDD row is missing one of these columns: {aliases}")


def supplied_sdd() -> Path:
    candidates = [Path("sdd.md"), *sorted(Path(".").glob("*SDD.md"))]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    fail("supplied SDD fixture is missing")


def bpmn_kind(value: str) -> str:
    normalized = header_key(value)
    mappings = (
        ("start event", "startEvent"),
        ("end event", "endEvent"),
        ("script task", "scriptTask"),
        ("user task", "userTask"),
        ("service task", "serviceTask"),
        ("business rule task", "businessRuleTask"),
        ("exclusive gateway", "exclusiveGateway"),
        ("inclusive gateway", "inclusiveGateway"),
        ("parallel gateway", "parallelGateway"),
        ("event based gateway", "eventBasedGateway"),
        ("subprocess", "subProcess"),
        ("call activity", "callActivity"),
        ("task", "task"),
    )
    for phrase, tag in mappings:
        if phrase in normalized:
            return tag
    fail(f"unsupported BPMN kind in supplied SDD: {value!r}")


def semantic_model(text: str):
    tables = parse_markdown_tables(text)
    node_rows = table_with(
        tables,
        ("Logical ID", "Node ID"),
        ("BPMN kind", "Node type"),
        ("Name",),
    )
    flow_rows = table_with(
        tables,
        ("Logical flow ID", "Flow ID"),
        ("From node", "Source Node ID"),
        ("To node", "Target Node ID"),
        ("Condition",),
        ("Default path", "Default"),
    )
    variable_rows = table_with(
        tables,
        ("Variable ID", "Variable"),
        ("Type",),
        ("Source", "Producer"),
        ("Consumers",),
    )

    nodes = {
        cell(row, "Logical ID", "Node ID"): {
            "kind": bpmn_kind(cell(row, "BPMN kind", "Node type")),
            "name": cell(row, "Name"),
        }
        for row in node_rows
    }
    flows = {
        cell(row, "Logical flow ID", "Flow ID"): {
            "source": cell(row, "From node", "Source Node ID"),
            "target": cell(row, "To node", "Target Node ID"),
            "condition": cell(row, "Condition"),
            "default": cell(row, "Default path", "Default").lower() == "yes",
        }
        for row in flow_rows
    }
    variables = {
        cell(row, "Variable ID", "Variable"): cell(row, "Type").split()[0].lower()
        for row in variable_rows
    }
    if not nodes or not flows or not variables:
        fail("supplied SDD semantic model is empty")
    return nodes, flows, variables


def find_logical_element(root, logical_id: str, expected_kind: str):
    token = compact(logical_id)
    candidates = root.findall(f".//{{{BPMN_NS}}}{expected_kind}")
    for element in candidates:
        if token in compact(element.attrib.get("id", "")) or token in compact(
            element.attrib.get("name", "")
        ):
            return element
    fail(f"missing {expected_kind} for SDD logical node {logical_id!r}")


def find_logical_flow(root, logical_id: str):
    token = compact(logical_id)
    for flow in root.findall(f".//{{{BPMN_NS}}}sequenceFlow"):
        if token in compact(flow.attrib.get("id", "")):
            return flow
    fail(f"missing sequence flow for SDD logical flow {logical_id!r}")


def require_variables(root, expected: dict[str, str]) -> None:
    variables = root.findall(f".//{{{UIPATH_NS}}}variables/*")
    for logical_id, expected_type in expected.items():
        token = compact(logical_id)
        matched = next(
            (
                variable
                for variable in variables
                if token in compact(variable.attrib.get("id", ""))
                or token in compact(variable.attrib.get("name", ""))
            ),
            None,
        )
        if matched is None:
            fail(f"missing declared SDD variable {logical_id!r}")
        actual_type = matched.attrib.get("type", "").lower()
        if compact(actual_type) != compact(expected_type):
            fail(
                f"SDD variable {logical_id!r} must have type {expected_type!r}, "
                f"got {actual_type or '<missing>'!r}"
            )


def extension_types(element) -> set[str]:
    return {
        type_element.attrib["value"]
        for type_element in element.findall(f".//{{{UIPATH_NS}}}type")
        if type_element.attrib.get("value")
    }


def require_flow_semantics(
    declared_flows: dict[str, dict[str, object]],
    generated_flows: dict[str, object],
    generated_nodes: dict[str, object],
    declared_variables: dict[str, str],
) -> None:
    variable_tokens = {compact(variable): variable for variable in declared_variables}
    for logical_id, declaration in declared_flows.items():
        flow = generated_flows[logical_id]
        source = generated_nodes[str(declaration["source"])]
        target = generated_nodes[str(declaration["target"])]
        if flow.attrib.get("sourceRef") != source.attrib["id"]:
            fail(f"{logical_id!r} does not preserve its SDD source node")
        if flow.attrib.get("targetRef") != target.attrib["id"]:
            fail(f"{logical_id!r} does not preserve its SDD target node")

        expression = flow.find(f"{{{BPMN_NS}}}conditionExpression")
        condition = str(declaration["condition"])
        if bool(declaration["default"]):
            if source.attrib.get("default") != flow.attrib["id"]:
                fail(f"{logical_id!r} is declared default but its gateway does not reference it")
            if expression is not None:
                fail(f"default flow {logical_id!r} must be unconditional")
        elif condition.lower() == "always":
            if expression is not None:
                fail(f"unconditional flow {logical_id!r} unexpectedly has a condition")
        else:
            if expression is None or not (expression.text or "").strip():
                fail(f"conditional SDD flow {logical_id!r} has no BPMN conditionExpression")
            declared_refs = [
                variable
                for token, variable in variable_tokens.items()
                if token and token in compact(condition)
            ]
            if not declared_refs:
                fail(f"SDD condition for {logical_id!r} references no declared variable")
            generated_condition = compact(expression.text or "")
            missing = [
                variable
                for variable in declared_refs
                if compact(variable) not in generated_condition
            ]
            if missing:
                fail(f"condition for {logical_id!r} dropped SDD variables: {missing}")


def require_di(root, nodes: dict[str, object], flows: dict[str, object]) -> None:
    shapes = {
        shape.attrib.get("bpmnElement")
        for shape in root.findall(f".//{{{BPMNDI_NS}}}BPMNShape")
    }
    edges = {
        edge.attrib.get("bpmnElement")
        for edge in root.findall(f".//{{{BPMNDI_NS}}}BPMNEdge")
    }
    for logical_id, node in nodes.items():
        if node.attrib["id"] not in shapes:
            fail(f"missing BPMNDI shape for SDD node {logical_id!r}")
    for logical_id, flow in flows.items():
        if flow.attrib["id"] not in edges:
            fail(f"missing BPMNDI edge for SDD flow {logical_id!r}")


def require_registry_calls() -> None:
    call_log = Path("mocks/.calls.jsonl")
    if not call_log.is_file():
        fail("mock uip call log is missing; registry discovery did not use the dispatcher")
    calls = [json.loads(line).get("args", "") for line in call_log.read_text().splitlines()]
    required = [
        "maestro bpmn registry pull",
        "maestro bpmn registry get BPMN.Variables",
        "maestro bpmn registry get BPMN.ScriptTask",
        "maestro bpmn registry get Actions.HITL",
        "is connections list --all-folders",
    ]
    missing = [pattern for pattern in required if not any(pattern in call for call in calls)]
    if missing:
        fail(f"registry discovery did not make required mocked calls: {missing}")
    connection_calls = [call for call in calls if "is connections list --all-folders" in call]
    if len(connection_calls) != 1:
        fail(
            "supplied-SDD discovery must refresh all-folder connections exactly once; "
            f"observed {len(connection_calls)} calls"
        )
    if not any(
        "maestro bpmn registry list" in call or "maestro bpmn registry search" in call
        for call in calls
    ):
        fail("registry discovery must list or search extension types")


def require_no_unrelated_connection_binding(bpmn_text: str) -> None:
    bindings_path = PROJECT / "bindings_v2.json"
    bindings = json.loads(bindings_path.read_text(encoding="utf-8"))
    resources = bindings.get("resources", [])
    if resources:
        fail(
            "this SDD declares ScriptTask and HITL templates with no connection "
            f"contract; bindings_v2.json must stay empty, got {len(resources)} resource(s)"
        )
    if "bindings." in bpmn_text:
        fail("BPMN references an unrelated connection binding absent from the SDD")


def require_validator_clean() -> None:
    skills_root = os.environ.get("SKILLS_REPO_PATH")
    if not skills_root:
        fail("SKILLS_REPO_PATH is required to run the bundled validator")
    validator = Path(skills_root) / "skills/uipath-maestro-bpmn/validator"
    install = subprocess.run(
        ["npm", "install", "--silent"],
        cwd=validator,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if install.returncode:
        fail(f"bundled validator dependencies failed to install: {install.stderr.strip()}")
    result = subprocess.run(
        ["node", "validate-bpmn.mjs", str(BPMN.resolve())],
        cwd=validator,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if result.returncode:
        fail(f"bundled validator failed:\n{result.stdout}{result.stderr}")
    if "VALID" not in result.stdout:
        fail(f"bundled validator did not report VALID:\n{result.stdout}{result.stderr}")


def main() -> int:
    if Path("sdd.draft.md").exists():
        fail("supplied SDD must bypass Phase 0; found sdd.draft.md")
    if not BPMN.is_file():
        fail(f"missing generated BPMN: {BPMN}")

    declared_nodes, declared_flows, declared_variables = semantic_model(
        supplied_sdd().read_text(encoding="utf-8")
    )
    undeclared_endpoints = {
        endpoint
        for flow in declared_flows.values()
        for endpoint in (str(flow["source"]), str(flow["target"]))
        if endpoint not in declared_nodes
    }
    if undeclared_endpoints:
        fail(f"supplied SDD flows reference undeclared nodes: {sorted(undeclared_endpoints)}")

    root = load_bpmn(str(BPMN))
    bpmn_text = BPMN.read_text(encoding="utf-8")
    if "unresolved" in bpmn_text.lower():
        fail("generated executable BPMN still contains an unresolved resource marker")

    nodes = {
        logical_id: find_logical_element(root, logical_id, str(declaration["kind"]))
        for logical_id, declaration in declared_nodes.items()
    }
    flows = {logical_id: find_logical_flow(root, logical_id) for logical_id in declared_flows}
    require_flow_semantics(declared_flows, flows, nodes, declared_variables)
    require_variables(root, declared_variables)

    for logical_id, declaration in declared_nodes.items():
        if declaration["kind"] == "scriptTask" and "BPMN.ScriptTask" not in extension_types(
            nodes[logical_id]
        ):
            fail(f"script task {logical_id!r} must use the registry-owned BPMN.ScriptTask wrapper")
        if declaration["kind"] == "userTask" and "Actions.HITL" not in extension_types(
            nodes[logical_id]
        ):
            fail(f"user task {logical_id!r} must use the registry-owned Actions.HITL wrapper")

    require_di(root, nodes, flows)
    starts = [node for logical_id, node in nodes.items() if declared_nodes[logical_id]["kind"] == "startEvent"]
    if len(starts) != 1:
        fail(f"expected one root start event from this SDD fixture, got {len(starts)}")
    assert_package_lifecycle(PROJECT, BPMN_NAME, starts[0].attrib["id"])
    require_no_unrelated_connection_binding(bpmn_text)
    require_registry_calls()
    require_validator_clean()

    print(
        "OK: every supplied SDD declaration produced a registry-backed, "
        "validator-clean BPMN project"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
