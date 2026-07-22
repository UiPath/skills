#!/usr/bin/env python3
"""Assemble a deterministic BPMN.Variables process from a compact graph plan."""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, NoReturn


BPMN = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI = "http://www.omg.org/spec/BPMN/20100524/DI"
DC = "http://www.omg.org/spec/DD/20100524/DC"
DI = "http://www.omg.org/spec/DD/20100524/DI"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
UIPATH = "http://uipath.org/schema/bpmn"

for prefix, namespace in (
    ("bpmn", BPMN),
    ("bpmndi", BPMNDI),
    ("dc", DC),
    ("di", DI),
    ("xsi", XSI),
    ("uipath", UIPATH),
):
    ET.register_namespace(prefix, namespace)


NODE_TAGS = {
    "task": "task",
    "exclusiveGateway": "exclusiveGateway",
    "parallelGateway": "parallelGateway",
    "inclusiveGateway": "inclusiveGateway",
}
GATEWAYS = {"exclusiveGateway", "parallelGateway", "inclusiveGateway"}
ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")
REF_RE = re.compile(r"\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}")


def fail(message: str) -> NoReturn:
    raise SystemExit(f"ERROR: {message}")


def q(namespace: str, local: str) -> str:
    return f"{{{namespace}}}{local}"


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{label} must be a non-empty string")
    return value


def require_id(value: Any, label: str) -> str:
    identifier = require_string(value, label)
    if not ID_RE.fullmatch(identifier):
        fail(f"{label} is not a valid BPMN id: {identifier!r}")
    return identifier


def load_plan(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        fail(f"cannot read plan {path}: {exc}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON plan {path}: {exc}")
    if not isinstance(value, dict):
        fail("plan root must be an object")
    return value


def project_main(project_dir: Path) -> Path:
    metadata = project_dir / "project.uiproj"
    try:
        project = json.loads(metadata.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {metadata}: {exc}")
    main = project.get("main")
    if not isinstance(main, str) or not main.endswith(".bpmn"):
        fail(f"{metadata} does not declare a BPMN main file")
    path = project_dir / main
    if not path.is_file():
        fail(f"missing scaffold BPMN: {path}")
    return path


def declared_variables(process: ET.Element) -> tuple[dict[str, str], dict[str, str]]:
    ids: dict[str, str] = {}
    types: dict[str, str] = {}
    variables = process.find(f"./{{{BPMN}}}extensionElements/{{{UIPATH}}}variables")
    if variables is None:
        fail("scaffold has no root uipath:variables declaration")
    for variable in list(variables):
        name = variable.attrib.get("name")
        variable_id = variable.attrib.get("id")
        variable_type = variable.attrib.get("type")
        if name and variable_id and variable_type:
            ids[name] = variable_id
            types[name] = variable_type
    if not ids:
        fail("scaffold declares no variables")
    return ids, types


def expand_refs(expression: str, variable_ids: dict[str, str], label: str) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in variable_ids:
            fail(f"{label} references undeclared variable {name!r}")
        return f"vars.{variable_ids[name]}"

    expanded = REF_RE.sub(replace, expression)
    if "{{" in expanded or "}}" in expanded:
        fail(f"{label} contains a malformed variable reference")
    return expanded


def validate_expression(expression: str, label: str) -> None:
    if not expression.startswith("="):
        fail(f"{label} must start with '='")
    if ("===" in expression or "!==" in expression) and not expression.startswith(
        "=js:"
    ):
        fail(f"{label} uses JavaScript strict comparison without '=js:'")
    if any(operator in expression for operator in ("&&", "||")) and not expression.startswith(
        "=js:"
    ):
        fail(f"{label} uses a JavaScript boolean operator without '=js:'")


def parse_graph(
    plan: dict[str, Any], start_id: str, end_id: str, variable_ids: dict[str, str]
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    raw_nodes = plan.get("nodes")
    raw_flows = plan.get("flows")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        fail("plan.nodes must be a non-empty array")
    if not isinstance(raw_flows, list) or not raw_flows:
        fail("plan.flows must be a non-empty array")

    nodes: list[dict[str, Any]] = []
    node_ids = {start_id, end_id}
    for index, raw in enumerate(raw_nodes):
        if not isinstance(raw, dict):
            fail(f"nodes[{index}] must be an object")
        node_id = require_id(raw.get("id"), f"nodes[{index}].id")
        if node_id in node_ids:
            fail(f"duplicate node id {node_id!r}")
        kind = require_string(raw.get("kind"), f"nodes[{index}].kind")
        if kind not in NODE_TAGS:
            fail(f"node {node_id!r} has unsupported kind {kind!r}")
        name = require_string(raw.get("name"), f"nodes[{index}].name")
        outputs = raw.get("outputs", {})
        if kind == "task":
            if not isinstance(outputs, dict):
                fail(f"task {node_id!r} outputs must be an object")
            normalized_outputs: dict[str, str] = {}
            for variable_name, source in outputs.items():
                if variable_name not in variable_ids:
                    fail(f"task {node_id!r} maps undeclared variable {variable_name!r}")
                if not isinstance(source, str):
                    fail(f"task {node_id!r} output {variable_name!r} source must be a string")
                expanded = expand_refs(source, variable_ids, f"task {node_id!r} output")
                if expanded.startswith("="):
                    validate_expression(expanded, f"task {node_id!r} output")
                normalized_outputs[variable_name] = expanded
            outputs = normalized_outputs
        elif outputs:
            fail(f"gateway {node_id!r} cannot declare outputs")

        node = dict(raw)
        node.update(id=node_id, kind=kind, name=name, outputs=outputs)
        if "default" in node:
            node["default"] = require_id(node["default"], f"node {node_id!r} default")
        nodes.append(node)
        node_ids.add(node_id)

    flows: list[dict[str, str]] = []
    flow_ids: set[str] = set()
    incoming: dict[str, list[str]] = defaultdict(list)
    outgoing: dict[str, list[str]] = defaultdict(list)
    for index, raw in enumerate(raw_flows):
        if not isinstance(raw, dict):
            fail(f"flows[{index}] must be an object")
        flow_id = require_id(raw.get("id"), f"flows[{index}].id")
        if flow_id in flow_ids or flow_id in node_ids:
            fail(f"duplicate flow id {flow_id!r}")
        source = require_id(raw.get("source"), f"flow {flow_id!r} source")
        target = require_id(raw.get("target"), f"flow {flow_id!r} target")
        if source not in node_ids or target not in node_ids:
            fail(f"flow {flow_id!r} references an unknown endpoint")
        flow: dict[str, str] = {"id": flow_id, "source": source, "target": target}
        condition = raw.get("condition")
        if condition is not None:
            if not isinstance(condition, str):
                fail(f"flow {flow_id!r} condition must be a string")
            expanded = expand_refs(condition, variable_ids, f"flow {flow_id!r} condition")
            validate_expression(expanded, f"flow {flow_id!r} condition")
            flow["condition"] = expanded
        flows.append(flow)
        flow_ids.add(flow_id)
        outgoing[source].append(flow_id)
        incoming[target].append(flow_id)

    if len(outgoing[start_id]) != 1 or incoming[start_id]:
        fail("start event must have exactly one outgoing and no incoming flow")
    if len(incoming[end_id]) != 1 or outgoing[end_id]:
        fail("end event must have exactly one incoming and no outgoing flow")
    for node in nodes:
        node_id = node["id"]
        if not incoming[node_id] or not outgoing[node_id]:
            fail(f"node {node_id!r} must have incoming and outgoing flow")
        if node["kind"] in {"exclusiveGateway", "inclusiveGateway"} and len(
            outgoing[node_id]
        ) >= 2:
            default = node.get("default")
            if default not in outgoing[node_id]:
                fail(f"diverging gateway {node_id!r} needs a valid default flow")
            for flow in flows:
                if flow["source"] == node_id and flow["id"] != default and "condition" not in flow:
                    fail(f"non-default flow {flow['id']!r} needs a condition")
        if node["kind"] == "parallelGateway":
            bad = [flow["id"] for flow in flows if flow["source"] == node_id and "condition" in flow]
            if bad:
                fail(f"parallel gateway {node_id!r} has conditional flows: {bad}")
    return nodes, flows


def add_refs(element: ET.Element, incoming: list[str], outgoing: list[str]) -> None:
    for flow_id in incoming:
        ET.SubElement(element, q(BPMN, "incoming")).text = flow_id
    for flow_id in outgoing:
        ET.SubElement(element, q(BPMN, "outgoing")).text = flow_id


def build_process_nodes(
    process: ET.Element,
    plan: dict[str, Any],
    nodes: list[dict[str, Any]],
    flows: list[dict[str, str]],
    start_id: str,
    end_id: str,
    entry_point_id: str,
    variable_ids: dict[str, str],
    variable_types: dict[str, str],
) -> None:
    incoming: dict[str, list[str]] = defaultdict(list)
    outgoing: dict[str, list[str]] = defaultdict(list)
    for flow in flows:
        outgoing[flow["source"]].append(flow["id"])
        incoming[flow["target"]].append(flow["id"])

    start = ET.SubElement(
        process,
        q(BPMN, "startEvent"),
        {"id": start_id, "name": str(plan.get("startName", "Start"))},
    )
    extension = ET.SubElement(start, q(BPMN, "extensionElements"))
    ET.SubElement(extension, q(UIPATH, "entryPointId"), {"value": entry_point_id})
    add_refs(start, incoming[start_id], outgoing[start_id])

    for node in nodes:
        attributes = {"id": node["id"], "name": node["name"]}
        if node["kind"] in {"exclusiveGateway", "inclusiveGateway"} and node.get("default"):
            attributes["default"] = node["default"]
        element = ET.SubElement(process, q(BPMN, NODE_TAGS[node["kind"]]), attributes)
        if node["kind"] == "task":
            node_extension = ET.SubElement(element, q(BPMN, "extensionElements"))
            mapping = ET.SubElement(node_extension, q(UIPATH, "mapping"), {"version": "v1"})
            ET.SubElement(
                mapping,
                q(UIPATH, "type"),
                {"value": "BPMN.Variables", "version": "v1"},
            )
            for variable_name, source in node["outputs"].items():
                ET.SubElement(
                    mapping,
                    q(UIPATH, "output"),
                    {
                        "name": variable_name,
                        "type": variable_types[variable_name],
                        "var": variable_ids[variable_name],
                        "custom": "true",
                        "source": source,
                    },
                )
        add_refs(element, incoming[node["id"]], outgoing[node["id"]])

    end = ET.SubElement(
        process,
        q(BPMN, "endEvent"),
        {"id": end_id, "name": str(plan.get("endName", "End"))},
    )
    add_refs(end, incoming[end_id], outgoing[end_id])

    for flow in flows:
        element = ET.SubElement(
            process,
            q(BPMN, "sequenceFlow"),
            {"id": flow["id"], "sourceRef": flow["source"], "targetRef": flow["target"]},
        )
        if "condition" in flow:
            condition = ET.SubElement(
                element,
                q(BPMN, "conditionExpression"),
                {q(XSI, "type"): "bpmn:tFormalExpression"},
            )
            condition.text = flow["condition"]


def graph_positions(
    ordered_ids: list[str], flows: list[dict[str, str]], start_id: str
) -> dict[str, tuple[int, int]]:
    predecessors: dict[str, list[str]] = defaultdict(list)
    successors: dict[str, list[str]] = defaultdict(list)
    indegree = {node_id: 0 for node_id in ordered_ids}
    for flow in flows:
        predecessors[flow["target"]].append(flow["source"])
        successors[flow["source"]].append(flow["target"])
        indegree[flow["target"]] += 1
    queue = deque(node_id for node_id in ordered_ids if indegree[node_id] == 0)
    levels = {start_id: 0}
    visited: list[str] = []
    while queue:
        node_id = queue.popleft()
        visited.append(node_id)
        levels[node_id] = max((levels.get(parent, 0) + 1 for parent in predecessors[node_id]), default=0)
        for target in successors[node_id]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if len(visited) != len(ordered_ids):
        fail("automatic diagram layout requires an acyclic process graph")

    layers: dict[int, list[str]] = defaultdict(list)
    for node_id in ordered_ids:
        layers[levels[node_id]].append(node_id)
    positions: dict[str, tuple[int, int]] = {}
    for level, node_ids in layers.items():
        total_height = (len(node_ids) - 1) * 140
        for index, node_id in enumerate(node_ids):
            positions[node_id] = (120 + level * 180, 300 - total_height // 2 + index * 140)
    return positions


def node_size(kind: str) -> tuple[int, int]:
    if kind in {"startEvent", "endEvent"}:
        return 36, 36
    if kind in GATEWAYS:
        return 50, 50
    return 120, 80


def build_diagram(
    root: ET.Element,
    process_id: str,
    nodes: list[dict[str, Any]],
    flows: list[dict[str, str]],
    start_id: str,
    end_id: str,
) -> None:
    ordered = [start_id, *[node["id"] for node in nodes], end_id]
    kinds = {start_id: "startEvent", end_id: "endEvent", **{node["id"]: node["kind"] for node in nodes}}
    positions = graph_positions(ordered, flows, start_id)
    for node in nodes:
        if isinstance(node.get("x"), int) and isinstance(node.get("y"), int):
            positions[node["id"]] = (node["x"], node["y"])

    diagram = ET.SubElement(root, q(BPMNDI, "BPMNDiagram"), {"id": "Diagram_1"})
    plane = ET.SubElement(
        diagram,
        q(BPMNDI, "BPMNPlane"),
        {"id": "Plane_1", "bpmnElement": process_id},
    )
    for node_id in ordered:
        x, y = positions[node_id]
        width, height = node_size(kinds[node_id])
        shape = ET.SubElement(
            plane,
            q(BPMNDI, "BPMNShape"),
            {"id": f"Shape_{node_id}", "bpmnElement": node_id},
        )
        ET.SubElement(
            shape,
            q(DC, "Bounds"),
            {"x": str(x), "y": str(y), "width": str(width), "height": str(height)},
        )
    for flow in flows:
        source_x, source_y = positions[flow["source"]]
        target_x, target_y = positions[flow["target"]]
        source_w, source_h = node_size(kinds[flow["source"]])
        target_w, target_h = node_size(kinds[flow["target"]])
        start = (source_x + source_w, source_y + source_h // 2)
        end = (target_x, target_y + target_h // 2)
        edge = ET.SubElement(
            plane,
            q(BPMNDI, "BPMNEdge"),
            {"id": f"Edge_{flow['id']}", "bpmnElement": flow["id"]},
        )
        midpoint = (start[0] + end[0]) // 2
        for x, y in (start, (midpoint, start[1]), (midpoint, end[1]), end):
            ET.SubElement(edge, q(DI, "waypoint"), {"x": str(x), "y": str(y)})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="replace a process previously generated from a plan",
    )
    args = parser.parse_args()

    project_dir = args.project_dir.resolve()
    bpmn_path = project_main(project_dir)
    plan = load_plan(args.plan.resolve())
    try:
        tree = ET.parse(bpmn_path)
    except ET.ParseError as exc:
        fail(f"cannot parse scaffold {bpmn_path}: {exc}")
    root = tree.getroot()
    process = root.find(f"./{{{BPMN}}}process")
    if process is None:
        fail("scaffold has no BPMN process")
    extension = process.find(f"./{{{BPMN}}}extensionElements")
    starts = process.findall(f"./{{{BPMN}}}startEvent")
    ends = process.findall(f"./{{{BPMN}}}endEvent")
    if extension is None or len(starts) != 1 or len(ends) != 1:
        fail("assembler requires the scaffold's one process, start, and end")
    start_id = require_id(starts[0].attrib.get("id"), "start id")
    end_id = require_id(ends[0].attrib.get("id"), "end id")
    entry = starts[0].find(f"./{{{BPMN}}}extensionElements/{{{UIPATH}}}entryPointId")
    if entry is None or not entry.attrib.get("value"):
        fail("scaffold start event has no uipath:entryPointId")
    entry_point_id = entry.attrib["value"]

    existing_flow_nodes = [
        child
        for child in list(process)
        if child is not extension and child.tag != q(BPMN, "sequenceFlow")
    ]
    existing_flows = process.findall(f"./{{{BPMN}}}sequenceFlow")
    is_skeleton = (
        len(existing_flow_nodes) == 2
        and len(existing_flows) == 1
        and existing_flows[0].attrib.get("id") == "Flow_Skeleton"
    )
    if not is_skeleton and not args.replace:
        fail("process is not the untouched scaffold; pass --replace to regenerate it")

    variable_ids, variable_types = declared_variables(process)
    nodes, flows = parse_graph(plan, start_id, end_id, variable_ids)
    for child in list(process):
        if child is not extension:
            process.remove(child)
    for diagram in root.findall(f"./{{{BPMNDI}}}BPMNDiagram"):
        root.remove(diagram)

    build_process_nodes(
        process,
        plan,
        nodes,
        flows,
        start_id,
        end_id,
        entry_point_id,
        variable_ids,
        variable_types,
    )
    build_diagram(root, process.attrib.get("id", "Process_1"), nodes, flows, start_id, end_id)
    ET.indent(tree, space="  ")
    tree.write(bpmn_path, encoding="utf-8", xml_declaration=True)
    print(
        json.dumps(
            {
                "bpmn": str(bpmn_path),
                "nodes": len(nodes) + 2,
                "activities": sum(node["kind"] == "task" for node in nodes),
                "flows": len(flows),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
