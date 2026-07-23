#!/usr/bin/env python3
"""Verify the interactive escalation artifact without prescribing element ids."""

from __future__ import annotations

import itertools
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, NoReturn


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
EVIDENCE = PROJECT / "registry-evidence"

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
    "attachments": "array",
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
    "lastAttachmentName": "string",
    "failureReason": "string",
}
FLOW_NODE_KINDS = {
    "startEvent",
    "endEvent",
    "boundaryEvent",
    "intermediateCatchEvent",
    "intermediateThrowEvent",
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
}


def fail(message: str) -> NoReturn:
    raise SystemExit(f"FAIL: {message}")


def q(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def get_ci(mapping: Any, name: str) -> Any:
    if not isinstance(mapping, dict):
        return None
    wanted = name.casefold()
    for key, value in mapping.items():
        if str(key).casefold() == wanted:
            return value
    return None


def parse_json_output(text: str, label: str) -> Any:
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    for index, character in enumerate(stripped):
        if character not in "[{":
            continue
        try:
            return json.loads(stripped[index:])
        except json.JSONDecodeError:
            continue
    fail(f"{label} returned invalid JSON")


def child_refs(element: ET.Element, kind: str) -> list[str]:
    return [
        (child.text or "").strip()
        for child in element.findall(f"./{q(BPMN_NS, kind)}")
        if (child.text or "").strip()
    ]


def mapping_outputs(element: ET.Element) -> list[ET.Element]:
    return element.findall(
        f".//{q(UIPATH_NS, 'output')}"
    )


def load_registry_evidence(extension_type: str) -> dict[str, Any]:
    path = EVIDENCE / f"{extension_type}.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing registry evidence: {path}")
    except json.JSONDecodeError as exc:
        fail(f"registry evidence is not exact JSON output ({path}): {exc}")

    data = get_ci(payload, "Data")
    entry = get_ci(data, "ExtensionType")
    if not isinstance(entry, dict):
        fail(f"{path} has no Data.ExtensionType registry entry")
    if get_ci(entry, "ExtensionType") != extension_type:
        fail(f"{path} is evidence for the wrong extension type")

    expected_element = {
        "BPMN.ScriptTask": "bpmn:ScriptTask",
        "BPMN.Variables": "bpmn:Task",
    }[extension_type]
    if str(get_ci(entry, "BpmnElement") or "").casefold() != expected_element.casefold():
        fail(f"{path} has an unexpected BpmnElement")
    if str(get_ci(entry, "ExtensionTag") or "").casefold() != "uipath:mapping":
        fail(f"{path} does not identify the registry-owned uipath:mapping wrapper")
    template = get_ci(entry, "XmlTemplate")
    if not isinstance(template, str) or extension_type not in template:
        fail(f"{path} has no usable XmlTemplate for {extension_type}")
    if "<uipath:mapping" not in template or "<uipath:type" not in template:
        fail(f"{path} XmlTemplate is missing the registry wrapper contract")

    current = subprocess.run(
        [
            "uip",
            "maestro",
            "bpmn",
            "registry",
            "get",
            extension_type,
            "--output",
            "json",
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    if current.returncode != 0:
        fail(
            f"could not independently refresh {extension_type} registry evidence: "
            f"{current.stderr or current.stdout}"
        )
    live_payload = parse_json_output(
        current.stdout, f"live registry get for {extension_type}"
    )
    live_entry = get_ci(get_ci(live_payload, "Data"), "ExtensionType")
    if payload != live_payload:
        fail(
            f"{path} is not the exact current registry response for {extension_type}"
        )
    if entry != live_entry:
        fail(f"live registry response for {extension_type} has an unexpected shape")
    return entry


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


def require_variables(
    process: ET.Element, start_id: str
) -> tuple[dict[str, ET.Element], dict[str, str]]:
    container = process.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'variables')}"
    )
    if container is None:
        fail("process is missing uipath:variables")

    declarations: dict[str, ET.Element] = {}
    ids_to_names: dict[str, str] = {}
    for variable in container:
        name = variable.attrib.get("name")
        variable_id = variable.attrib.get("id")
        if not name or not variable_id:
            fail("every process variable must have a non-empty name and id")
        if name in declarations:
            fail(f"duplicate process variable name: {name}")
        if variable_id in ids_to_names:
            fail(f"duplicate process variable id: {variable_id}")
        declarations[name] = variable
        ids_to_names[variable_id] = name

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
            f"entry-point inputs must bind to start event {start_id!r}: "
            f"{unbound_inputs}"
        )
    return declarations, ids_to_names


def build_scope_graph(
    scope: ET.Element,
) -> tuple[
    dict[str, ET.Element],
    dict[str, ET.Element],
    dict[str, list[str]],
    dict[str, list[str]],
]:
    nodes = {
        element.attrib["id"]: element
        for element in scope
        if local(element.tag) in FLOW_NODE_KINDS and element.attrib.get("id")
    }
    flows = {
        element.attrib["id"]: element
        for element in scope.findall(f"./{q(BPMN_NS, 'sequenceFlow')}")
        if element.attrib.get("id")
    }
    if not flows:
        fail(f"scope {scope.attrib.get('id', '<unknown>')!r} has no sequence flows")

    outgoing: dict[str, list[str]] = defaultdict(list)
    incoming: dict[str, list[str]] = defaultdict(list)
    for flow_id, flow in flows.items():
        source = flow.attrib.get("sourceRef")
        target = flow.attrib.get("targetRef")
        if source not in nodes or target not in nodes:
            fail(
                f"sequence flow {flow_id!r} has unresolved same-scope refs "
                f"{source!r}->{target!r}"
            )
        outgoing[source].append(target)
        incoming[target].append(source)
        if child_refs(nodes[source], "outgoing").count(flow_id) != 1:
            fail(f"source {source!r} must declare outgoing {flow_id!r} exactly once")
        if child_refs(nodes[target], "incoming").count(flow_id) != 1:
            fail(f"target {target!r} must declare incoming {flow_id!r} exactly once")

    for node_id, node in nodes.items():
        expected_in = sorted(
            flow_id
            for flow_id, flow in flows.items()
            if flow.attrib.get("targetRef") == node_id
        )
        expected_out = sorted(
            flow_id
            for flow_id, flow in flows.items()
            if flow.attrib.get("sourceRef") == node_id
        )
        if sorted(child_refs(node, "incoming")) != expected_in:
            fail(f"node {node_id!r} incoming declarations do not match its flows")
        if sorted(child_refs(node, "outgoing")) != expected_out:
            fail(f"node {node_id!r} outgoing declarations do not match its flows")
    return nodes, flows, dict(outgoing), dict(incoming)


def walk(origin: str, graph: dict[str, list[str]], *, stop: str | None = None) -> set[str]:
    visited: set[str] = set()
    queue: deque[str] = deque([origin])
    while queue:
        current = queue.popleft()
        if current in visited or current == stop:
            continue
        visited.add(current)
        queue.extend(graph.get(current, []))
    return visited


def require_scope_reachability(
    nodes: dict[str, ET.Element],
    outgoing: dict[str, list[str]],
    incoming: dict[str, list[str]],
    start_id: str,
    end_ids: set[str],
    *,
    boundary_ids: set[str] | None = None,
) -> None:
    boundary_ids = boundary_ids or set()
    reachable = walk(start_id, outgoing)
    for boundary_id in boundary_ids:
        reachable.update(walk(boundary_id, outgoing))
    missing = sorted(set(nodes) - reachable)
    if missing:
        fail(f"flow nodes are unreachable from start {start_id!r}: {missing}")

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
        fail(f"flow nodes cannot reach an end event: {trapped}")


def require_gateway_contract(
    scope: ET.Element,
    flows: dict[str, ET.Element],
    *,
    require_diverging: bool = True,
) -> list[str]:
    conditions: list[str] = []
    diverging = 0
    for gateway in scope.findall(f"./{q(BPMN_NS, 'exclusiveGateway')}"):
        outgoing_ids = child_refs(gateway, "outgoing")
        if len(outgoing_ids) < 2:
            continue
        diverging += 1
        default_id = gateway.attrib.get("default")
        if not default_id or default_id not in outgoing_ids:
            fail(
                f"exclusive gateway {gateway.attrib.get('id')!r} needs an "
                "explicit default flow"
            )
        for flow_id in outgoing_ids:
            condition = flows[flow_id].find(
                f"./{q(BPMN_NS, 'conditionExpression')}"
            )
            if flow_id == default_id:
                if condition is not None and (condition.text or "").strip():
                    fail(f"default flow {flow_id!r} must not have a condition")
                continue
            expression = (condition.text or "").strip() if condition is not None else ""
            if not expression.startswith("="):
                fail(f"non-default flow {flow_id!r} needs an '=' condition")
            if any(token in expression for token in ("===", "!==", "&&", "||")):
                if not expression.startswith("=js:"):
                    fail(
                        f"flow {flow_id!r} uses JavaScript-only operators "
                        "without '=js:'"
                    )
            conditions.append(expression)
    if require_diverging and diverging == 0:
        fail(f"scope {scope.attrib.get('id')!r} has no visible exclusive decision")
    return conditions


def referenced_variable_ids(expressions: str) -> set[str]:
    """Return exact `vars.<id>` references without prefix collisions."""
    return set(re.findall(r"\bvars\.([A-Za-z0-9_-]+)", expressions))


def require_registry_activities(root: ET.Element) -> tuple[ET.Element, list[ET.Element]]:
    load_registry_evidence("BPMN.ScriptTask")
    load_registry_evidence("BPMN.Variables")

    scripts: list[ET.Element] = []
    variable_tasks: list[ET.Element] = []
    unexpected: list[tuple[str, str | None]] = []
    for element in root.iter():
        if local(element.tag) not in ACTIVITY_KINDS:
            continue
        type_elements = element.findall(
            f"./{q(BPMN_NS, 'extensionElements')}//{q(UIPATH_NS, 'type')}"
        )
        values = [item.attrib.get("value") for item in type_elements]
        if len(values) != 1 or not values[0]:
            fail(
                f"activity {element.attrib.get('id')!r} must contain exactly "
                f"one registry type; found {values}"
            )
        if values[0] == "BPMN.ScriptTask" and local(element.tag) == "scriptTask":
            scripts.append(element)
        elif values[0] == "BPMN.Variables" and local(element.tag) == "task":
            variable_tasks.append(element)
        else:
            unexpected.append((local(element.tag), values[0]))

    if unexpected:
        fail(f"portable process contains unsupported/unrequested activities: {unexpected}")
    if len(scripts) != 1:
        fail(f"expected exactly one normalization ScriptTask, found {len(scripts)}")
    if len(variable_tasks) < 8:
        fail(
            "expected substantial registry-derived Variables activity usage "
            f"across decisions and workstreams, found {len(variable_tasks)}"
        )
    return scripts[0], variable_tasks


def require_normalization_script(
    script: ET.Element,
    variables: dict[str, ET.Element],
    ids_to_names: dict[str, str],
) -> set[str]:
    if script.attrib.get("scriptFormat") != "JavaScript":
        fail("normalization ScriptTask must use scriptFormat='JavaScript'")
    version = script.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'scriptVersion')}"
    )
    if version is None or version.attrib.get("value") != "v3":
        fail("normalization ScriptTask must use uipath:scriptVersion v3")

    mapping_input = script.find(
        f"./{q(BPMN_NS, 'extensionElements')}//{q(UIPATH_NS, 'input')}"
    )
    if mapping_input is None or mapping_input.attrib.get("name") != "args":
        fail("normalization ScriptTask must use the registry args input mapping")
    input_text = mapping_input.text or ""
    mapped_input_ids = referenced_variable_ids(input_text)
    required_input_ids = {
        variables[name].attrib["id"]
        for name in (
            "customerTier",
            "serviceState",
            "duplicateIssueKey",
            "correlationId",
        )
    }
    missing_inputs = sorted(
        variable_id
        for variable_id in required_input_ids
        if variable_id not in mapped_input_ids
    )
    if missing_inputs:
        fail(f"normalization ScriptTask input mapping misses variables: {missing_inputs}")

    script_body = (
        script.findtext(f"./{q(BPMN_NS, 'script')}", default="") or ""
    )
    lowered = script_body.casefold()
    if "tolowercase" not in lowered:
        fail("normalization script does not perform case normalization")
    if "trim" not in lowered:
        fail("normalization script does not trim duplicateIssueKey")
    forbidden = {
        "manualreview",
        "existingissue",
        "newescalation",
        "informational",
        "sev1",
        "sev2",
        "sev3",
        "crmnotfound",
        "crmambiguous",
        "invalidagentoutput",
        "jiraunavailable",
        "updateexisting",
        "createissue",
        "postalert",
        "send",
    }
    leaked = sorted(token for token in forbidden if token in lowered)
    if leaked:
        fail(
            "normalization script hides business decisions that must remain "
            f"visible in gateways/tasks: {leaked}"
        )

    targets = {
        output.attrib["var"]
        for output in mapping_outputs(script)
        if output.attrib.get("var") in ids_to_names
    }
    forbidden_targets = {
        variables[name].attrib["id"]
        for name in (
            "route",
            "severity",
            "engineeringNeeded",
            "jiraAction",
            "attachmentAction",
            "slackAction",
            "responseMode",
            "lastAttachmentName",
            "failureReason",
        )
        if name in variables
    }
    leaked_targets = sorted(
        ids_to_names[variable_id]
        for variable_id in targets & forbidden_targets
    )
    if leaked_targets:
        fail(
            "normalization ScriptTask must not initialize or assign business "
            f"decision/downstream outputs: {leaked_targets}"
        )
    if variables["caseKey"].attrib["id"] not in targets:
        fail("normalization ScriptTask must preserve correlationId into caseKey")
    string_targets = {
        variable_id
        for variable_id in targets
        if next(
            (
                declaration.attrib.get("type")
                for declaration in variables.values()
                if declaration.attrib.get("id") == variable_id
            ),
            None,
        )
        == "string"
    }
    if len(string_targets - {variables["caseKey"].attrib["id"]}) < 3:
        fail(
            "normalization ScriptTask needs distinct string outputs for tier, "
            "service state, and trimmed duplicate key"
        )
    return targets


def output_names_in_elements(
    elements: list[ET.Element], ids_to_names: dict[str, str]
) -> set[str]:
    names: set[str] = set()
    for element in elements:
        for output in mapping_outputs(element):
            mapped = ids_to_names.get(output.attrib.get("var", ""))
            if mapped:
                names.add(mapped)
            if output.attrib.get("name"):
                names.add(output.attrib["name"])
    return names


def output_literal_exists(
    elements: list[ET.Element],
    ids_to_names: dict[str, str],
    variable_name: str,
    literal: str,
) -> bool:
    for element in elements:
        for output in mapping_outputs(element):
            mapped_name = ids_to_names.get(output.attrib.get("var", ""))
            if mapped_name != variable_name and output.attrib.get("name") != variable_name:
                continue
            if literal in (output.attrib.get("source") or ""):
                return True
    return False


def require_assessment_subprocess(
    root: ET.Element,
    process: ET.Element,
    variables: dict[str, ET.Element],
    ids_to_names: dict[str, str],
    normalization_targets: set[str],
) -> tuple[ET.Element, ET.Element]:
    subprocesses = [
        item
        for item in process.findall(f"./{q(BPMN_NS, 'subProcess')}")
        if item.find(f"./{q(BPMN_NS, 'multiInstanceLoopCharacteristics')}")
        is None
    ]
    if len(subprocesses) != 1:
        fail(
            "expected exactly one ordinary root embedded assessment "
            f"subprocess, found {len(subprocesses)}"
        )
    subprocess = subprocesses[0]
    if subprocess.attrib.get("triggeredByEvent") == "true":
        fail("assessment must be an ordinary embedded subprocess, not an event subprocess")

    sub_nodes, sub_flows, sub_outgoing, sub_incoming = build_scope_graph(subprocess)
    starts = [
        node_id for node_id, node in sub_nodes.items() if local(node.tag) == "startEvent"
    ]
    ends = [node_id for node_id, node in sub_nodes.items() if local(node.tag) == "endEvent"]
    if len(starts) != 1 or not ends:
        fail("assessment subprocess needs one start and at least one end")
    require_scope_reachability(
        sub_nodes, sub_outgoing, sub_incoming, starts[0], set(ends)
    )
    conditions = require_gateway_contract(subprocess, sub_flows)
    if len(
        [
            node
            for node in sub_nodes.values()
            if local(node.tag) == "exclusiveGateway"
            and len(child_refs(node, "outgoing")) >= 2
        ]
    ) < 6:
        fail("assessment subprocess is not a substantial visible decision phase")

    condition_blob = "\n".join(conditions)
    condition_folded = condition_blob.casefold()
    condition_variable_ids = referenced_variable_ids(condition_blob)
    required_condition_vars = {
        "crmMatchCount": variables["crmMatchCount"].attrib["id"],
        "agentOutputValid": variables["agentOutputValid"].attrib["id"],
        "jiraAvailable": variables["jiraAvailable"].attrib["id"],
    }
    missing_condition_vars = [
        name
        for name, variable_id in required_condition_vars.items()
        if variable_id not in condition_variable_ids
    ]
    if missing_condition_vars:
        fail(
            "visible assessment conditions omit required decision inputs: "
            f"{missing_condition_vars}"
        )
    for literal in ("enterprise", "unavailable", "degraded", "sev1", "sev2"):
        if literal not in condition_folded:
            fail(f"visible assessment conditions omit policy token {literal!r}")

    context_only_ids = {
        variables["businessImpact"].attrib["id"],
        variables["correlationId"].attrib["id"],
        variables["caseKey"].attrib["id"],
    }
    leaked_context = sorted(
        variable_id
        for variable_id in context_only_ids
        if variable_id in condition_variable_ids
    )
    if leaked_context:
        fail(f"context/correlation values must not influence routing: {leaked_context}")
    used_normalized = {
        target
        for target in normalization_targets
        if target != variables["caseKey"].attrib["id"]
        and target in condition_variable_ids
    }
    if len(used_normalized) < 3:
        fail(
            "assessment conditions do not consume all three values mapped from "
            "the normalization ScriptTask"
        )

    error_declarations = root.findall(f"./{q(BPMN_NS, 'error')}")
    jira_errors = [
        error
        for error in error_declarations
        if "jira" in " ".join(error.attrib.values()).casefold()
        and "unavail" in " ".join(error.attrib.values()).casefold()
    ]
    if len(jira_errors) != 1:
        fail("definitions must declare exactly one Jira-unavailable BPMN error")
    error = jira_errors[0]
    error_id = error.attrib.get("id")
    if not error_id or not error.attrib.get("errorCode"):
        fail("Jira-unavailable BPMN error needs id and errorCode")

    error_ends = []
    for end_id in ends:
        definition = sub_nodes[end_id].find(f"./{q(BPMN_NS, 'errorEventDefinition')}")
        if definition is not None and definition.attrib.get("errorRef") == error_id:
            error_ends.append(sub_nodes[end_id])
    if len(error_ends) != 1:
        fail("assessment needs exactly one error end referencing the Jira error")

    error_end = error_ends[0]
    incoming_ids = child_refs(error_end, "incoming")
    if len(incoming_ids) != 1:
        fail("Jira error end must have exactly one visibly guarded incoming flow")
    error_flow = sub_flows[incoming_ids[0]]
    source = sub_nodes[error_flow.attrib["sourceRef"]]
    error_assignment_tasks: list[ET.Element] = []
    while local(source.tag) == "task":
        type_values = [
            item.attrib.get("value")
            for item in source.findall(
                f"./{q(BPMN_NS, 'extensionElements')}//{q(UIPATH_NS, 'type')}"
            )
        ]
        if type_values != ["BPMN.Variables"]:
            fail(
                "only registry-derived Variables tasks may appear between the "
                "Jira guard and error end"
            )
        if len(child_refs(source, "incoming")) != 1 or len(
            child_refs(source, "outgoing")
        ) != 1:
            fail(
                "Jira error assignment path must be straight-line with no "
                "branching"
            )
        error_assignment_tasks.append(source)
        error_flow = sub_flows[child_refs(source, "incoming")[0]]
        source = sub_nodes[error_flow.attrib["sourceRef"]]
    if local(source.tag) != "exclusiveGateway":
        fail(
            "Jira error end must be selected by an exclusive gateway, with "
            "only straight-line Variables assignments in between"
        )
    error_condition = error_flow.find(f"./{q(BPMN_NS, 'conditionExpression')}")
    error_expression = (error_condition.text or "") if error_condition is not None else ""
    jira_id = variables["jiraAvailable"].attrib["id"]
    error_variable_ids = referenced_variable_ids(error_expression)
    if jira_id not in error_variable_ids or (
        "sev1" not in error_expression.casefold()
        and "sev2" not in error_expression.casefold()
        and variables["severity"].attrib["id"] not in error_variable_ids
    ):
        fail(
            "Jira error-end flow must visibly guard Jira unavailability with "
            "Sev1/Sev2 eligibility"
        )
    boundaries = [
        event
        for event in process.findall(f"./{q(BPMN_NS, 'boundaryEvent')}")
        if event.attrib.get("attachedToRef") == subprocess.attrib.get("id")
    ]
    matching_boundaries = []
    for boundary in boundaries:
        definition = boundary.find(f"./{q(BPMN_NS, 'errorEventDefinition')}")
        if definition is not None and definition.attrib.get("errorRef") == error_id:
            matching_boundaries.append(boundary)
    if len(matching_boundaries) != 1:
        fail("assessment must have one matching Jira interrupting error boundary")
    boundary = matching_boundaries[0]
    if boundary.attrib.get("cancelActivity", "true") != "true":
        fail("Jira error boundary must be interrupting")

    root_nodes, _root_flows, root_outgoing, _root_incoming = build_scope_graph(process)
    boundary_region = walk(boundary.attrib["id"], root_outgoing)
    boundary_tasks = [
        root_nodes[node_id]
        for node_id in boundary_region
        if node_id in root_nodes and local(root_nodes[node_id].tag) == "task"
    ]
    if not output_literal_exists(
        [*error_assignment_tasks, *boundary_tasks],
        ids_to_names,
        "failureReason",
        "JiraUnavailable",
    ):
        fail("Jira error/boundary path never emits failureReason JiraUnavailable")
    if not output_literal_exists(
        boundary_tasks, ids_to_names, "route", "ManualReview"
    ):
        fail("Jira boundary path never emits route ManualReview")
    return subprocess, boundary


def branch_region(
    origin: str,
    join: str,
    outgoing: dict[str, list[str]],
) -> set[str]:
    region = walk(origin, outgoing, stop=join)
    if join not in walk(origin, outgoing):
        fail(f"parallel branch rooted at {origin!r} cannot reach join {join!r}")
    return region


def require_sequential_attachment_loop(
    elements: list[ET.Element],
    variables: dict[str, ET.Element],
    ids_to_names: dict[str, str],
) -> None:
    candidates: list[ET.Element] = []
    for element in elements:
        marker = element.find(f"./{q(BPMN_NS, 'multiInstanceLoopCharacteristics')}")
        if marker is None or marker.attrib.get("isSequential") != "true":
            continue
        loop = marker.find(
            f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'loopCharacteristics')}"
        )
        if loop is None:
            continue
        collection = loop.attrib.get("inputCollection", "")
        input_element = loop.attrib.get("inputElement", "")
        if (
            variables["attachments"].attrib["id"]
            not in referenced_variable_ids(collection)
            or not input_element
        ):
            continue
        candidates.append(element)
    if len(candidates) != 1:
        fail(
            "attachment branch needs exactly one sequential multi-instance "
            "activity bound to the attachments input"
        )

    loop_activity = candidates[0]
    last_name_id = variables["lastAttachmentName"].attrib["id"]
    if local(loop_activity.tag) == "subProcess":
        required_iterator = "iterator[0].item"
    else:
        required_iterator = "iterator.item"
    item_mappings = [
        output
        for output in mapping_outputs(loop_activity)
        if (
            output.attrib.get("var") == last_name_id
            or ids_to_names.get(output.attrib.get("var", "")) == "lastAttachmentName"
        )
        and required_iterator in (output.attrib.get("source") or "")
    ]
    if len(item_mappings) != 1:
        fail(
            "sequential attachment activity must consume its documented "
            f"{required_iterator} value and map it to lastAttachmentName"
        )


def require_parallel_workstreams(
    process: ET.Element,
    nodes: dict[str, ET.Element],
    outgoing: dict[str, list[str]],
    incoming: dict[str, list[str]],
    variables: dict[str, ET.Element],
    ids_to_names: dict[str, str],
) -> tuple[str, str]:
    parallel = [
        node_id for node_id, node in nodes.items() if local(node.tag) == "parallelGateway"
    ]
    splits = [node_id for node_id in parallel if len(outgoing.get(node_id, [])) == 3]
    joins = [node_id for node_id in parallel if len(incoming.get(node_id, [])) == 3]
    if len(splits) != 1 or len(joins) != 1 or splits[0] == joins[0]:
        fail("expected exactly one three-way parallel split and one three-way join")
    split, join = splits[0], joins[0]

    regions = [
        branch_region(origin, join, outgoing) for origin in outgoing.get(split, [])
    ]
    for left, right in itertools.combinations(regions, 2):
        overlap = left & right
        if overlap:
            fail(f"parallel workstreams overlap before the join: {sorted(overlap)}")

    region_elements = [
        [nodes[node_id] for node_id in region if node_id in nodes] for region in regions
    ]
    branch_outputs = [
        output_names_in_elements(elements, ids_to_names) for elements in region_elements
    ]
    required = (
        {"jiraAction"},
        {"attachmentAction", "lastAttachmentName"},
        {"slackAction", "responseMode"},
    )
    matching_order: tuple[set[str], ...] | None = None
    for order in itertools.permutations(branch_outputs):
        if all(wanted <= observed for wanted, observed in zip(required, order)):
            matching_order = order
            break
    if matching_order is None:
        fail(
            "three parallel workstreams must independently own Jira, attachment "
            "(including lastAttachmentName), and combined communication outputs; "
            f"observed {branch_outputs}"
        )

    attachment_index = next(
        index
        for index, outputs in enumerate(branch_outputs)
        if {"attachmentAction", "lastAttachmentName"} <= outputs
    )
    require_sequential_attachment_loop(
        region_elements[attachment_index], variables, ids_to_names
    )
    return split, join


def require_di(
    root: ET.Element,
    nodes: dict[str, ET.Element],
    flows: dict[str, ET.Element],
    subprocess_nodes: dict[str, ET.Element],
    subprocess_flows: dict[str, ET.Element],
) -> None:
    shapes = {
        shape.attrib.get("bpmnElement"): shape
        for shape in root.findall(f".//{q(BPMNDI_NS, 'BPMNShape')}")
    }
    edges = {
        edge.attrib.get("bpmnElement"): edge
        for edge in root.findall(f".//{q(BPMNDI_NS, 'BPMNEdge')}")
    }
    for node_id, node in {**nodes, **subprocess_nodes}.items():
        shape = shapes.get(node_id)
        if shape is None:
            fail(f"visible flow node {node_id!r} is missing BPMNShape")
        bounds = shape.find(f"./{q(DC_NS, 'Bounds')}")
        if bounds is None:
            fail(f"BPMNShape for {node_id!r} is missing dc:Bounds")
        try:
            x, y, width, height = (
                float(bounds.attrib[name]) for name in ("x", "y", "width", "height")
            )
        except (KeyError, ValueError):
            fail(f"BPMNShape for {node_id!r} has invalid bounds")
        if width <= 0 or height <= 0 or x < 0 or y < 0:
            fail(f"BPMNShape for {node_id!r} has invalid geometry")
        if local(node.tag) == "subProcess" and shape.attrib.get("isExpanded") != "true":
            fail("assessment subprocess must be expanded so its decisions are visible")

    for flow_id in {**flows, **subprocess_flows}:
        edge = edges.get(flow_id)
        if edge is None:
            fail(f"sequence flow {flow_id!r} is missing BPMNEdge")
        if len(edge.findall(f"./{q(DI_NS, 'waypoint')}")) < 2:
            fail(f"BPMNEdge for {flow_id!r} needs at least two waypoints")


def main() -> None:
    if not BPMN.is_file():
        fail(f"missing BPMN file: {BPMN}")
    try:
        root = ET.parse(BPMN).getroot()
    except ET.ParseError as exc:
        fail(f"{BPMN} is not well-formed XML: {exc}")

    processes = root.findall(f"./{q(BPMN_NS, 'process')}")
    if len(processes) != 1:
        fail(f"expected exactly one root process, found {len(processes)}")
    process = processes[0]
    if process.attrib.get("isExecutable") != "true":
        fail("BPMN process must be executable")

    starts = process.findall(f"./{q(BPMN_NS, 'startEvent')}")
    ends = process.findall(f"./{q(BPMN_NS, 'endEvent')}")
    if len(starts) != 1 or len(ends) != 1:
        fail("root process needs exactly one start and one end event")
    start_id = starts[0].attrib.get("id")
    end_id = ends[0].attrib.get("id")
    if not start_id or not end_id:
        fail("root start/end events need ids")
    entry_points = starts[0].findall(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'entryPointId')}"
    )
    if len(entry_points) != 1 or not entry_points[0].attrib.get("value"):
        fail("root start event must declare one non-empty uipath:entryPointId")

    require_unique_ids(root)
    variables, ids_to_names = require_variables(process, start_id)
    script, _variable_tasks = require_registry_activities(root)
    normalization_targets = require_normalization_script(
        script, variables, ids_to_names
    )
    subprocess, boundary = require_assessment_subprocess(
        root, process, variables, ids_to_names, normalization_targets
    )

    nodes, flows, outgoing, incoming = build_scope_graph(process)
    boundary_id = boundary.attrib.get("id")
    require_scope_reachability(
        nodes,
        outgoing,
        incoming,
        start_id,
        {end_id},
        boundary_ids={boundary_id} if boundary_id else set(),
    )
    # The assessment subprocess must expose the policy decisions. At root
    # scope, an exclusive gateway is optional: a conditional loop collection
    # can correctly encode zero attachment iterations without an extra XOR.
    require_gateway_contract(process, flows, require_diverging=False)
    split, join = require_parallel_workstreams(
        process, nodes, outgoing, incoming, variables, ids_to_names
    )
    if split not in walk(subprocess.attrib["id"], outgoing):
        fail("normal assessment completion does not reach the parallel fan-out")
    if boundary_id and split not in walk(boundary_id, outgoing):
        fail("Jira boundary-error path does not rejoin before the parallel fan-out")

    nested_nodes: dict[str, ET.Element] = {}
    nested_flows: dict[str, ET.Element] = {}
    for nested_scope in process.findall(f".//{q(BPMN_NS, 'subProcess')}"):
        scope_nodes, scope_flows, _scope_outgoing, _scope_incoming = build_scope_graph(
            nested_scope
        )
        nested_nodes.update(scope_nodes)
        nested_flows.update(scope_flows)
    require_di(root, nodes, flows, nested_nodes, nested_flows)
    require_no_private_connector_values(root)
    assert_package_lifecycle(PROJECT, BPMN.name, start_id)

    print(
        f"OK: registry-derived project has {len(nodes) + len(nested_nodes)} visible "
        f"nodes, one normalization ScriptTask, an expanded assessment subprocess "
        f"with Jira error boundary, sequential attachment iteration, and parallel "
        f"workstreams {split!r}->{join!r}"
    )


if __name__ == "__main__":
    main()
