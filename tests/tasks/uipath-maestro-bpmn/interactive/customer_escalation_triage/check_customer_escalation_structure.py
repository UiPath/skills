#!/usr/bin/env python3
"""Check package integrity and behavior-justified BPMN orchestration structure."""

from __future__ import annotations

import itertools
import os
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict, deque
from pathlib import Path
from typing import NoReturn


_directory = os.path.dirname(os.path.abspath(__file__))
while _directory != os.path.dirname(_directory) and not os.path.isdir(
    os.path.join(_directory, "_shared")
):
    _directory = os.path.dirname(_directory)
sys.path.insert(0, _directory)

from _shared.bpmn_assertions import assert_package_lifecycle  # noqa: E402
from _shared.bpmn_check import require_no_private_connector_values  # noqa: E402


PROJECT = Path("CustomerEscalationTriage")
BPMN = PROJECT / "CustomerEscalationTriage.bpmn"
BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
DC_NS = "http://www.omg.org/spec/DD/20100524/DC"
DI_NS = "http://www.omg.org/spec/DD/20100524/DI"
UIPATH_NS = "http://uipath.org/schema/bpmn"

EXPECTED_INPUTS = {
    "customerTier": "string",
    "crmMatchCount": "integer",
    "serviceState": "string",
    "workaroundAvailable": "boolean",
    "duplicateIssueKey": "string",
    "attachmentCount": "integer",
    "agentOutputValid": "boolean",
    "jiraAvailable": "boolean",
    "autoSendEnabled": "boolean",
    "businessImpact": "string",
    "correlationId": "string",
}
EXPECTED_OUTPUTS = {
    "route": "string",
    "severity": "string",
    "engineeringNeeded": "boolean",
    "jiraAction": "string",
    "attachmentAction": "string",
    "slackAction": "string",
    "responseMode": "string",
    "caseKey": "string",
    "failureReason": "string",
}
FLOW_NODE_KINDS = {
    "startEvent",
    "endEvent",
    "task",
    "serviceTask",
    "sendTask",
    "receiveTask",
    "userTask",
    "businessRuleTask",
    "scriptTask",
    "callActivity",
    "subProcess",
    "exclusiveGateway",
    "parallelGateway",
    "inclusiveGateway",
    "eventBasedGateway",
}
ACTIVITY_KINDS = {
    "task",
    "serviceTask",
    "sendTask",
    "receiveTask",
    "userTask",
    "businessRuleTask",
    "scriptTask",
    "callActivity",
    "subProcess",
}


def fail(message: str) -> NoReturn:
    raise SystemExit(f"FAIL: {message}")


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def child_refs(element: ET.Element, kind: str) -> list[str]:
    return [
        (child.text or "").strip()
        for child in element.findall(f"./{{{BPMN_NS}}}{kind}")
        if (child.text or "").strip()
    ]


def require_unique_ids(root: ET.Element) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for element in root.iter():
        element_id = element.attrib.get("id")
        if not element_id:
            continue
        if element_id in seen:
            duplicates.add(element_id)
        seen.add(element_id)
    if duplicates:
        fail(f"duplicate BPMN/XML ids: {sorted(duplicates)}")


def require_variables(process: ET.Element, start_id: str) -> dict[str, str]:
    container = process.find(
        f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}variables"
    )
    if container is None:
        fail("process is missing uipath:variables")

    declarations: dict[str, ET.Element] = {}
    variable_ids: set[str] = set()
    for variable in container:
        name = variable.attrib.get("name")
        variable_id = variable.attrib.get("id")
        if not name or not variable_id:
            fail("every process variable must have non-empty name and id")
        if name in declarations:
            fail(f"duplicate process variable name: {name}")
        if variable_id in variable_ids:
            fail(f"duplicate process variable id: {variable_id}")
        declarations[name] = variable
        variable_ids.add(variable_id)

    required = {**EXPECTED_INPUTS, **EXPECTED_OUTPUTS}
    missing = sorted(set(required) - set(declarations))
    if missing:
        fail(f"missing required process variables: {missing}")
    wrong_types = {
        name: (expected, declarations[name].attrib.get("type"))
        for name, expected in required.items()
        if declarations[name].attrib.get("type") != expected
    }
    if wrong_types:
        fail(f"process variable types do not match the contract: {wrong_types}")

    unbound_inputs = sorted(
        name
        for name in EXPECTED_INPUTS
        if declarations[name].attrib.get("elementId") != start_id
    )
    if unbound_inputs:
        fail(
            f"entry-point inputs must bind to start event {start_id!r}: {unbound_inputs}"
        )
    return {
        variable.attrib["id"]: variable.attrib["name"] for variable in declarations.values()
    }


def require_registry_backed_activities(activities: list[ET.Element]) -> None:
    if len(activities) < 3:
        fail("expected at least three activities for the independent action workstreams")
    for activity in activities:
        activity_id = activity.attrib.get("id", "<missing-id>")
        type_elements = activity.findall(
            f"./{{{BPMN_NS}}}extensionElements/.//{{{UIPATH_NS}}}type"
        )
        values = [element.attrib.get("value") for element in type_elements]
        if len(type_elements) != 1 or not values[0]:
            fail(
                f"activity {activity_id!r} must contain exactly one non-empty "
                f"registry-derived uipath:type; found {values}"
            )


def build_graph(
    process: ET.Element,
) -> tuple[
    dict[str, ET.Element],
    dict[str, ET.Element],
    dict[str, list[str]],
    dict[str, list[str]],
]:
    nodes = {
        element.attrib["id"]: element
        for element in process
        if local(element.tag) in FLOW_NODE_KINDS and element.attrib.get("id")
    }
    flows = {
        element.attrib["id"]: element
        for element in process.findall(f"./{{{BPMN_NS}}}sequenceFlow")
        if element.attrib.get("id")
    }
    if not flows:
        fail("process has no sequence flows")

    outgoing: dict[str, list[str]] = defaultdict(list)
    incoming: dict[str, list[str]] = defaultdict(list)
    for flow_id, flow in flows.items():
        source = flow.attrib.get("sourceRef")
        target = flow.attrib.get("targetRef")
        if source not in nodes or target not in nodes:
            fail(f"sequence flow {flow_id!r} has unresolved refs {source!r}->{target!r}")
        outgoing[source].append(target)
        incoming[target].append(source)

        if child_refs(nodes[source], "outgoing").count(flow_id) != 1:
            fail(f"source {source!r} must declare outgoing flow {flow_id!r} exactly once")
        if child_refs(nodes[target], "incoming").count(flow_id) != 1:
            fail(f"target {target!r} must declare incoming flow {flow_id!r} exactly once")

    for node_id, node in nodes.items():
        declared_in = child_refs(node, "incoming")
        declared_out = child_refs(node, "outgoing")
        expected_in = sorted(
            flow_id for flow_id, flow in flows.items() if flow.attrib.get("targetRef") == node_id
        )
        expected_out = sorted(
            flow_id for flow_id, flow in flows.items() if flow.attrib.get("sourceRef") == node_id
        )
        if sorted(declared_in) != expected_in:
            fail(f"node {node_id!r} incoming declarations do not match sequence flows")
        if sorted(declared_out) != expected_out:
            fail(f"node {node_id!r} outgoing declarations do not match sequence flows")

    return nodes, flows, dict(outgoing), dict(incoming)


def require_reachability(
    nodes: dict[str, ET.Element],
    outgoing: dict[str, list[str]],
    incoming: dict[str, list[str]],
    start_id: str,
    end_ids: set[str],
) -> None:
    def walk(origin: str, graph: dict[str, list[str]]) -> set[str]:
        visited: set[str] = set()
        queue: deque[str] = deque([origin])
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            queue.extend(graph.get(current, []))
        return visited

    reachable = walk(start_id, outgoing)
    missing = sorted(set(nodes) - reachable)
    if missing:
        fail(f"flow nodes are unreachable from the root start event: {missing}")

    can_reach_end: set[str] = set()
    queue: deque[str] = deque(end_ids)
    while queue:
        current = queue.popleft()
        if current in can_reach_end:
            continue
        can_reach_end.add(current)
        queue.extend(incoming.get(current, []))
    trapped = sorted(set(nodes) - can_reach_end)
    if trapped:
        fail(f"flow nodes cannot reach any end event: {trapped}")


def require_exclusive_decisions(
    process: ET.Element, flows: dict[str, ET.Element]
) -> None:
    gateways = process.findall(f"./{{{BPMN_NS}}}exclusiveGateway")
    diverging = [gateway for gateway in gateways if len(child_refs(gateway, "outgoing")) >= 2]
    if not diverging:
        fail("expected at least one exclusive decision gateway")
    for gateway in diverging:
        gateway_id = gateway.attrib.get("id")
        outgoing_ids = child_refs(gateway, "outgoing")
        default_id = gateway.attrib.get("default")
        if not default_id or default_id not in outgoing_ids:
            fail(f"diverging exclusive gateway {gateway_id!r} needs an explicit default flow")
        for flow_id in outgoing_ids:
            if flow_id == default_id:
                continue
            condition = flows[flow_id].find(f"./{{{BPMN_NS}}}conditionExpression")
            if condition is None or not (condition.text or "").strip():
                fail(
                    f"non-default flow {flow_id!r} from exclusive gateway "
                    f"{gateway_id!r} needs a non-empty conditionExpression"
                )
            expression = (condition.text or "").strip()
            if not expression.startswith("="):
                fail(f"condition on flow {flow_id!r} must start with '='")
            if ("===" in expression or "!==" in expression) and not expression.startswith(
                "=js:"
            ):
                fail(
                    f"condition on flow {flow_id!r} uses a JavaScript strict "
                    "comparison without the required '=js:' prefix"
                )


def require_visible_success_routing(
    process: ET.Element, flows: dict[str, ET.Element]
) -> None:
    conditions: list[str] = []
    for gateway in process.findall(f"./{{{BPMN_NS}}}exclusiveGateway"):
        if len(child_refs(gateway, "outgoing")) < 2:
            continue
        for flow_id in child_refs(gateway, "outgoing"):
            condition = flows[flow_id].find(f"./{{{BPMN_NS}}}conditionExpression")
            if condition is not None and (condition.text or "").strip():
                conditions.append((condition.text or "").strip())

    condition_blob = "\n".join(conditions)
    named_route_literals = {
        literal
        for literal in ("ExistingIssue", "NewEscalation", "Informational")
        if literal in condition_blob
    }
    routes_from_inputs = (
        "Var_DuplicateIssueKey" in condition_blob
        and "Var_Severity" in condition_blob
    )
    if len(named_route_literals) < 2 and not routes_from_inputs:
        fail(
            "success routing must be visible in exclusive-gateway conditions "
            "(route literals, or duplicateIssueKey plus severity); computing all "
            "success routes only inside one mapping task is not sufficient"
        )


def require_jira_unavailable_guard(
    process: ET.Element, flows: dict[str, ET.Element]
) -> None:
    failure_tasks: list[ET.Element] = []
    for task in process.findall(f"./{{{BPMN_NS}}}task"):
        sources = {
            output.attrib.get("source")
            for output in task.findall(
                f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}mapping/"
                f"{{{UIPATH_NS}}}output"
            )
        }
        if "JiraUnavailable" in sources:
            failure_tasks.append(task)
    if len(failure_tasks) != 1:
        fail("expected exactly one task that emits failureReason JiraUnavailable")

    conditions: list[str] = []
    for flow_id in child_refs(failure_tasks[0], "incoming"):
        condition = flows[flow_id].find(f"./{{{BPMN_NS}}}conditionExpression")
        if condition is not None and (condition.text or "").strip():
            conditions.append((condition.text or "").strip())
    guard = "\n".join(conditions)
    required = ("Var_JiraAvailable", "Var_Severity", "Sev1", "Sev2")
    missing = [token for token in required if token not in guard]
    if missing:
        fail(
            "the JiraUnavailable branch must visibly retain the complete "
            "Sev1/Sev2 eligibility guard as well as Jira availability; missing "
            f"from its guarded incoming flow: {missing}"
        )


def simple_paths(
    start: str,
    end: str,
    outgoing: dict[str, list[str]],
    *,
    max_nodes: int,
) -> list[list[str]]:
    found: list[list[str]] = []
    stack: list[tuple[str, list[str]]] = [(start, [start])]
    while stack and len(found) < 300:
        current, path = stack.pop()
        if current == end:
            found.append(path)
            continue
        if len(path) >= max_nodes:
            continue
        for target in outgoing.get(current, []):
            if target not in path:
                stack.append((target, [*path, target]))
    return found


def mapped_output_names(
    path: list[str], nodes: dict[str, ET.Element], variables: dict[str, str]
) -> set[str]:
    mapped: set[str] = set()
    for node_id in path:
        for output in nodes[node_id].findall(
            f"./{{{BPMN_NS}}}extensionElements/.//{{{UIPATH_NS}}}output"
        ):
            declared_name = output.attrib.get("name")
            variable_name = variables.get(output.attrib.get("var", ""))
            for name in (declared_name, variable_name):
                if name:
                    mapped.add(name)
    return mapped


def require_parallel_workstreams(
    nodes: dict[str, ET.Element],
    outgoing: dict[str, list[str]],
    incoming: dict[str, list[str]],
    variables: dict[str, str],
) -> tuple[str, str, list[set[str]]]:
    parallel = [
        node_id for node_id, node in nodes.items() if local(node.tag) == "parallelGateway"
    ]
    splits = [node_id for node_id in parallel if len(outgoing.get(node_id, [])) == 3]
    joins = [node_id for node_id in parallel if len(incoming.get(node_id, [])) == 3]
    if not splits or not joins:
        fail("expected parallel gateways with exactly a three-way split and three-way join")

    for split in splits:
        branch_roots = outgoing.get(split, [])
        for join in joins:
            if split == join:
                continue
            candidates: dict[str, list[list[str]]] = {}
            for branch_root in branch_roots:
                paths = simple_paths(branch_root, join, outgoing, max_nodes=len(nodes) + 1)
                candidates[branch_root] = [
                    path
                    for path in paths
                    if any(local(nodes[node_id].tag) in ACTIVITY_KINDS for node_id in path[:-1])
                ]

            usable_roots = [root for root, paths in candidates.items() if paths]
            for roots in itertools.combinations(usable_roots, 3):
                for chosen in itertools.product(*(candidates[root] for root in roots)):
                    internal_sets = [set(path[:-1]) for path in chosen]
                    if not all(
                        left.isdisjoint(right)
                        for left, right in itertools.combinations(internal_sets, 2)
                    ):
                        continue
                    branch_outputs = [
                        mapped_output_names(path[:-1], nodes, variables) for path in chosen
                    ]
                    required_outputs = (
                        {"jiraAction"},
                        {"attachmentAction"},
                        {"slackAction", "responseMode"},
                    )
                    if any(
                        all(required <= branch_outputs[index] for index, required in enumerate(order))
                        for order in itertools.permutations(required_outputs)
                    ):
                        return split, join, branch_outputs

    fail(
        "parallel split/join must contain exactly three node-disjoint activity "
        "branches that map Jira, attachment, and both communication intent "
        "outputs (slackAction plus responseMode) on one communication branch; "
        "a decorative gateway pair is not sufficient"
    )


def require_di(root: ET.Element, nodes: dict[str, ET.Element], flows: dict[str, ET.Element]) -> None:
    shapes = {
        shape.attrib.get("bpmnElement"): shape
        for shape in root.findall(f".//{{{BPMNDI_NS}}}BPMNShape")
    }
    edges = {
        edge.attrib.get("bpmnElement"): edge
        for edge in root.findall(f".//{{{BPMNDI_NS}}}BPMNEdge")
    }
    for node_id in nodes:
        shape = shapes.get(node_id)
        if shape is None:
            fail(f"flow node {node_id!r} is missing BPMNShape")
        bounds = shape.find(f"./{{{DC_NS}}}Bounds")
        if bounds is None:
            fail(f"BPMNShape for {node_id!r} is missing dc:Bounds")
        try:
            values = [float(bounds.attrib[name]) for name in ("x", "y", "width", "height")]
        except (KeyError, ValueError):
            fail(f"BPMNShape for {node_id!r} has invalid bounds")
        if values[2] <= 0 or values[3] <= 0:
            fail(f"BPMNShape for {node_id!r} must have positive width and height")

    for flow_id in flows:
        edge = edges.get(flow_id)
        if edge is None:
            fail(f"sequence flow {flow_id!r} is missing BPMNEdge")
        if len(edge.findall(f"./{{{DI_NS}}}waypoint")) < 2:
            fail(f"BPMNEdge for {flow_id!r} needs at least two waypoints")


def main() -> None:
    if not BPMN.is_file():
        fail(f"missing BPMN file: {BPMN}")
    try:
        root = ET.parse(BPMN).getroot()
    except ET.ParseError as exc:
        fail(f"{BPMN} is not well-formed XML: {exc}")

    processes = root.findall(f"./{{{BPMN_NS}}}process")
    if len(processes) != 1:
        fail(f"expected exactly one root process, found {len(processes)}")
    process = processes[0]
    if process.attrib.get("isExecutable") != "true":
        fail("BPMN process must be executable")

    starts = process.findall(f"./{{{BPMN_NS}}}startEvent")
    ends = process.findall(f"./{{{BPMN_NS}}}endEvent")
    if len(starts) != 1:
        fail(f"expected exactly one root start event, found {len(starts)}")
    if not ends:
        fail("expected at least one root end event")
    start = starts[0]
    start_id = start.attrib.get("id")
    if not start_id:
        fail("root start event needs an id")
    entry_points = start.findall(
        f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}entryPointId"
    )
    if len(entry_points) != 1 or not entry_points[0].attrib.get("value"):
        fail("root start event must declare exactly one non-empty uipath:entryPointId")

    require_unique_ids(root)
    variable_ids = require_variables(process, start_id)
    nodes, flows, outgoing, incoming = build_graph(process)
    activities = [node for node in nodes.values() if local(node.tag) in ACTIVITY_KINDS]
    require_registry_backed_activities(activities)
    require_reachability(nodes, outgoing, incoming, start_id, {end.attrib["id"] for end in ends})
    require_exclusive_decisions(process, flows)
    require_visible_success_routing(process, flows)
    require_jira_unavailable_guard(process, flows)
    split_id, join_id, branch_outputs = require_parallel_workstreams(
        nodes, outgoing, incoming, variable_ids
    )
    require_di(root, nodes, flows)
    require_no_private_connector_values(root)
    assert_package_lifecycle(PROJECT, BPMN.name, start_id)

    print(
        f"OK: {BPMN} has {len(nodes)} reachable flow nodes, {len(activities)} "
        f"registry-backed activities, package-complete metadata, and a real "
        f"three-workstream parallel region {split_id!r}->{join_id!r} with "
        f"branch outputs {branch_outputs}"
    )


if __name__ == "__main__":
    main()
