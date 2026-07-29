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


def identifier_token(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


def normalization_field_roles(field_names: set[str]) -> set[str]:
    """Map semantically named normalized fields to the contract values."""
    roles: set[str] = set()
    for field_name in field_names:
        token = identifier_token(field_name)
        if "tier" in token:
            roles.add("tier")
        if ("service" in token and "state" in token) or token == "state":
            roles.add("serviceState")
        if "duplicate" in token:
            roles.add("duplicateIssueKey")
    return roles


def structured_normalization_roles(declaration: ET.Element) -> set[str]:
    """Return normalization roles declared by one typed structured variable."""
    if declaration.attrib.get("type") not in {"object", "json", "jsonSchema"}:
        return set()
    body = (declaration.text or "").strip()
    if not body:
        return set()
    try:
        schema = json.loads(body)
    except json.JSONDecodeError:
        return set()
    properties = schema.get("properties") if isinstance(schema, dict) else None
    if not isinstance(properties, dict):
        return set()
    return normalization_field_roles(set(properties))


def structured_normalization_roles_in_conditions(
    variable_id: str, condition_blob: str
) -> set[str]:
    """Return normalized object properties visibly consumed by gateways."""
    fields = set(
        re.findall(
            rf"\bvars\.{re.escape(variable_id)}\.([A-Za-z_$][\w$]*)",
            condition_blob,
        )
    )
    return normalization_field_roles(fields)


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


def find_registry_evidence(
    extension_type: str,
    evidence_dir: Path = EVIDENCE,
) -> list[tuple[Path, dict[str, Any], dict[str, Any]]]:
    """Find registry-get responses by content, independent of filename."""
    matches: list[tuple[Path, dict[str, Any], dict[str, Any]]] = []
    for path in sorted(evidence_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        entry = get_ci(get_ci(payload, "Data"), "ExtensionType")
        if (
            isinstance(entry, dict)
            and get_ci(entry, "ExtensionType") == extension_type
        ):
            matches.append((path, payload, entry))
    if not matches:
        names = sorted(path.name for path in evidence_dir.glob("*.json"))
        fail(
            f"missing exact {extension_type} registry-get evidence under "
            f"{evidence_dir}; inspected {names}"
        )
    return matches


def require_usable_registry_template(
    extension_type: str,
    entry: dict[str, Any],
    path: Path,
) -> None:
    template = get_ci(entry, "XmlTemplate")
    if not isinstance(template, str):
        fail(f"{path} has no usable XmlTemplate for {extension_type}")
    if "<uipath:mapping" not in template or "<uipath:type" not in template:
        fail(f"{path} XmlTemplate is missing the registry wrapper contract")
    accepted_mapping_types = {
        "BPMN.ScriptTask": {"BPMN.ScriptTask", "BPMN.Variables"},
        "BPMN.Variables": {"BPMN.Variables"},
    }[extension_type]
    if not any(
        f'value="{mapping_type}"' in template
        for mapping_type in accepted_mapping_types
    ):
        fail(
            f"{path} XmlTemplate does not contain a registry-served "
            f"{extension_type} mapping contract"
        )


def load_registry_evidence(extension_type: str) -> dict[str, Any]:
    candidates = find_registry_evidence(extension_type)

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
    exact = [
        candidate
        for candidate in candidates
        if candidate[1] == live_payload
    ]
    if not exact:
        paths = [str(candidate[0]) for candidate in candidates]
        fail(
            f"saved registry responses {paths} are not the exact current "
            f"response for {extension_type}"
        )
    path, _payload, entry = exact[0]
    if entry != live_entry:
        fail(f"live registry response for {extension_type} has an unexpected shape")

    expected_element = {
        "BPMN.ScriptTask": "bpmn:ScriptTask",
        "BPMN.Variables": "bpmn:Task",
    }[extension_type]
    if str(get_ci(entry, "BpmnElement") or "").casefold() != expected_element.casefold():
        fail(f"{path} has an unexpected BpmnElement")
    if str(get_ci(entry, "ExtensionTag") or "").casefold() != "uipath:mapping":
        fail(f"{path} does not identify the registry-owned uipath:mapping wrapper")
    require_usable_registry_template(extension_type, entry, path)
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
    process: ET.Element,
    start_id: str,
    end_id: str,
) -> tuple[dict[str, ET.Element], dict[str, str]]:
    container = process.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'variables')}"
    )
    if container is None:
        fail("process is missing uipath:variables")

    declarations_by_name: dict[str, list[ET.Element]] = defaultdict(list)
    ids_to_names: dict[str, str] = {}
    for variable in container:
        name = variable.attrib.get("name")
        variable_id = variable.attrib.get("id")
        if not name or not variable_id:
            fail("every process variable must have a non-empty name and id")
        if variable_id in ids_to_names:
            fail(f"duplicate process variable id: {variable_id}")
        declarations_by_name[name].append(variable)
        ids_to_names[variable_id] = name

    declarations: dict[str, ET.Element] = {}
    public_input_ids: dict[str, str] = {}
    public_output_ids: dict[str, str] = {}
    for name, expected_type in EXPECTED_INPUTS.items():
        candidates = declarations_by_name.get(name, [])
        public = [item for item in candidates if local(item.tag) == "input"]
        internal = [
            item for item in candidates if local(item.tag) == "inputOutput"
        ]
        if len(public) != 1 or len(internal) != 1:
            fail(
                f"input {name!r} needs one public input and one mutable "
                "inputOutput declaration"
            )
        if public[0].attrib.get("type") != expected_type or internal[
            0
        ].attrib.get("type") != expected_type:
            fail(f"input {name!r} has the wrong public/internal type")
        if public[0].attrib.get("elementId") != start_id:
            fail(f"public input {name!r} must bind to {start_id!r}")
        declarations[name] = internal[0]
        public_input_ids[name] = public[0].attrib["id"]

    for name, expected_type in EXPECTED_OUTPUTS.items():
        candidates = declarations_by_name.get(name, [])
        public = [item for item in candidates if local(item.tag) == "output"]
        internal = [
            item for item in candidates if local(item.tag) == "inputOutput"
        ]
        if len(public) != 1 or len(internal) != 1:
            fail(
                f"output {name!r} needs one public output and one mutable "
                "inputOutput declaration"
            )
        if public[0].attrib.get("type") != expected_type or internal[
            0
        ].attrib.get("type") != expected_type:
            fail(f"output {name!r} has the wrong public/internal type")
        if public[0].attrib.get("elementId") != end_id:
            fail(f"public output {name!r} must bind to {end_id!r}")
        declarations[name] = internal[0]
        public_output_ids[name] = public[0].attrib["id"]

    for name, candidates in declarations_by_name.items():
        internal = [
            item for item in candidates if local(item.tag) == "inputOutput"
        ]
        if name not in declarations and len(internal) == 1:
            declarations[name] = internal[0]

    start = process.find(f"./{q(BPMN_NS, 'startEvent')}[@id='{start_id}']")
    end = process.find(f"./{q(BPMN_NS, 'endEvent')}[@id='{end_id}']")
    if start is None or end is None:
        fail("could not resolve root start/end for public variable bridges")
    start_outputs = mapping_outputs(start)
    end_outputs = mapping_outputs(end)
    for name in EXPECTED_INPUTS:
        target_id = declarations[name].attrib["id"]
        expected_source = f"=vars.{public_input_ids[name]}"
        if not any(
            item.attrib.get("var") == target_id
            and item.attrib.get("source") == expected_source
            for item in start_outputs
        ):
            fail(f"root StartEvent does not bridge public input {name!r}")
    for name in EXPECTED_OUTPUTS:
        source_id = declarations[name].attrib["id"]
        public_id = public_output_ids[name]
        if not any(
            item.attrib.get("var") == public_id
            and item.attrib.get("source") == f"=vars.{source_id}"
            for item in end_outputs
        ):
            fail(f"root EndEvent does not bridge public output {name!r}")
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


def mapping_input_body(element: ET.Element) -> str:
    return element.attrib.get("value") or element.text or ""


def require_script_runtime_contract(script: ET.Element) -> None:
    script_id = script.attrib.get("id", "<unknown>")
    if script.attrib.get("scriptFormat") != "JavaScript":
        fail(f"ScriptTask {script_id!r} must use scriptFormat='JavaScript'")
    version = script.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'scriptVersion')}"
    )
    if version is None or version.attrib.get("value") != "v3":
        fail(f"ScriptTask {script_id!r} must use uipath:scriptVersion v3")
    mapping = script.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'mapping')}"
    )
    if mapping is None:
        fail(f"ScriptTask {script_id!r} is missing its mapping")
    type_element = mapping.find(f"./{q(UIPATH_NS, 'type')}")
    if type_element is None or type_element.attrib.get("value") != "BPMN.Variables":
        fail(
            f"ScriptTask {script_id!r} must use the current "
            "BPMN.Variables serializer contract"
        )
    schema = mapping.find(
        f"./{q(UIPATH_NS, 'context')}/{q(UIPATH_NS, 'inputSchema')}"
    )
    if schema is None or schema.attrib.get("type") != "jsonSchema":
        fail(f"ScriptTask {script_id!r} is missing inputSchema context")
    try:
        schema_body = json.loads((schema.text or "").strip())
    except json.JSONDecodeError:
        fail(f"ScriptTask {script_id!r} inputSchema is not valid JSON")
    properties = get_ci(schema_body, "properties") or {}

    mapping_input = mapping.find(f"./{q(UIPATH_NS, 'input')}")
    if (
        mapping_input is None
        or mapping_input.attrib.get("name") != "args"
        or mapping_input.attrib.get("type") != "json"
        or mapping_input.attrib.get("target") != "bodyField"
    ):
        fail(f"ScriptTask {script_id!r} must use the args bodyField input")
    try:
        args = json.loads(mapping_input_body(mapping_input).strip())
    except json.JSONDecodeError:
        fail(f"ScriptTask {script_id!r} args input is not valid runtime JSON")
    required_args = {"vars": "=vars", "metadata": "=metadata"}
    for name, expected in required_args.items():
        if get_ci(args, name) != expected or get_ci(properties, name) is None:
            fail(
                f"ScriptTask {script_id!r} must pass and declare {name!r}"
            )
    marker = script.find(
        f"./{q(BPMN_NS, 'multiInstanceLoopCharacteristics')}"
    )
    if marker is not None:
        if get_ci(args, "iterator") != "=iterator" or get_ci(
            properties, "iterator"
        ) is None:
            fail(
                f"multi-instance ScriptTask {script_id!r} must pass and "
                "declare iterator"
            )
    output_names = {
        item.attrib.get("name")
        for item in mapping.findall(f"./{q(UIPATH_NS, 'output')}")
    }
    if not {"scriptResponse", "Error"} <= output_names:
        fail(
            f"ScriptTask {script_id!r} must map standard scriptResponse "
            "and Error outputs"
        )


def require_registry_activities(
    root: ET.Element,
) -> tuple[ET.Element, list[ET.Element], list[ET.Element]]:
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
        if values[0] == "BPMN.Variables" and local(element.tag) == "scriptTask":
            scripts.append(element)
        elif values[0] == "BPMN.Variables" and local(element.tag) == "task":
            variable_tasks.append(element)
        else:
            unexpected.append((local(element.tag), values[0]))

    if unexpected:
        fail(f"portable process contains unsupported/unrequested activities: {unexpected}")
    if len(scripts) != 3:
        fail(
            "expected exactly three data-only ScriptTasks "
            f"(normalization, attachment marker, reducer), found {len(scripts)}"
        )
    declared_variables = {
        item.attrib.get("id"): item
        for item in root.findall(
            f"./{q(BPMN_NS, 'process')}/"
            f"{q(BPMN_NS, 'extensionElements')}/"
            f"{q(UIPATH_NS, 'variables')}/*"
        )
        if item.attrib.get("id")
    }
    for script in scripts:
        require_script_runtime_contract(script)
        script_id = script.attrib.get("id")
        for output in mapping_outputs(script):
            variable = declared_variables.get(output.attrib.get("var"))
            if variable is None:
                fail(
                    f"ScriptTask {script_id!r} maps undeclared variable "
                    f"{output.attrib.get('var')!r}"
                )
            if output.attrib.get("name") == "Error" and (
                variable.attrib.get("name") != "Error"
                or variable.attrib.get("elementId") != script_id
            ):
                fail(
                    f"ScriptTask {script_id!r} Error output needs a "
                    "same-named variable scoped to that script"
                )
    normalization_candidates = [
        script
        for script in scripts
        if "trim" in (
            script.findtext(f"./{q(BPMN_NS, 'script')}", default="") or ""
        ).casefold()
        and (
            "tolowercase"
            in (
                script.findtext(
                    f"./{q(BPMN_NS, 'script')}", default=""
                )
                or ""
            ).casefold()
            or "touppercase"
            in (
                script.findtext(
                    f"./{q(BPMN_NS, 'script')}", default=""
                )
                or ""
            ).casefold()
        )
    ]
    if len(normalization_candidates) != 1:
        fail("expected exactly one case/whitespace normalization ScriptTask")
    if len(variable_tasks) < 8:
        fail(
            "expected substantial registry-derived Variables activity usage "
            f"across decisions and workstreams, found {len(variable_tasks)}"
        )
    return normalization_candidates[0], scripts, variable_tasks


def require_normalization_script(
    script: ET.Element,
    variables: dict[str, ET.Element],
    ids_to_names: dict[str, str],
    variable_tasks: list[ET.Element],
) -> set[str]:
    mapping_input = script.find(
        f"./{q(BPMN_NS, 'extensionElements')}//{q(UIPATH_NS, 'input')}"
    )
    if mapping_input is None or mapping_input.attrib.get("name") != "args":
        fail("normalization ScriptTask must use the registry args input mapping")
    script_body = (
        script.findtext(f"./{q(BPMN_NS, 'script')}", default="") or ""
    )
    mapped_input_ids = referenced_variable_ids(script_body)
    required_input_ids = {
        variables[name].attrib["id"]
        for name in (
            "customerTier",
            "serviceState",
            "duplicateIssueKey",
        )
    }
    missing_inputs = sorted(
        variable_id
        for variable_id in required_input_ids
        if variable_id not in mapped_input_ids
    )
    if missing_inputs:
        fail(f"normalization ScriptTask input mapping misses variables: {missing_inputs}")

    lowered = script_body.casefold()
    if "tolowercase" not in lowered and "touppercase" not in lowered:
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

    script_outputs = mapping_outputs(script)
    response_ids = {
        output.attrib["var"]
        for output in script_outputs
        if output.attrib.get("name") == "scriptResponse"
        and output.attrib.get("var")
    }
    normalization_outputs = list(script_outputs)
    for task in variable_tasks:
        task_outputs = mapping_outputs(task)
        if any(
            response_ids
            & referenced_variable_ids(output.attrib.get("source", ""))
            for output in task_outputs
        ):
            # A Variables task that extracts the ScriptTask response is part of
            # the same normalization contract. Include all of its assignments
            # so a direct correlationId -> caseKey copy remains visible without
            # forcing an unnecessary round trip through JavaScript.
            normalization_outputs.extend(task_outputs)

    targets = {
        output.attrib["var"]
        for output in normalization_outputs
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
    case_key_targets = {
        output.attrib["var"]
        for output in normalization_outputs
        if output.attrib.get("var") in ids_to_names
        and (
            "casekey" in identifier_token(output.attrib.get("name", ""))
            or "casekey"
            in identifier_token(ids_to_names[output.attrib["var"]])
        )
    }
    if not case_key_targets:
        fail("normalization ScriptTask must preserve correlationId into caseKey")
    correlation_id = variables["correlationId"].attrib["id"]
    case_result_properties = {"caseKey"}
    for output in normalization_outputs:
        if output.attrib.get("var") not in case_key_targets:
            continue
        source = output.attrib.get("source", "")
        for response_id in response_ids:
            match = re.search(
                rf"\bvars\.{re.escape(response_id)}\."
                r"([A-Za-z_$][\w$]*)\b",
                source,
            )
            if match:
                case_result_properties.add(match.group(1))
    direct_copy = any(
        re.search(
            rf"\b{re.escape(property_name)}\s*:\s*"
            rf"vars\.{re.escape(correlation_id)}\b",
            script_body,
            flags=re.IGNORECASE,
        )
        for property_name in case_result_properties
    )
    alias_copy = False
    for match in re.finditer(
        rf"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*"
        rf"vars\.{re.escape(correlation_id)}"
        r"(?:\s*\|\|\s*[\"']{2})?\s*;",
        script_body,
        flags=re.IGNORECASE,
    ):
        alias = match.group(1)
        if any(
            re.search(
                rf"\b{re.escape(property_name)}\s*:\s*"
                rf"{re.escape(alias)}\b",
                script_body,
                flags=re.IGNORECASE,
            )
            for property_name in case_result_properties
        ):
            alias_copy = True
            break
    visible_copy = any(
        output.attrib.get("var") in case_key_targets
        and output.attrib.get("source", "").strip()
        == f"=vars.{correlation_id}"
        for output in normalization_outputs
    )
    if not direct_copy and not alias_copy and not visible_copy:
        fail(
            "normalization contract must copy correlationId exactly into "
            "caseKey, either in the ScriptTask result or its associated "
            "Variables extraction task"
        )
    declarations_by_id = {
        declaration.attrib["id"]: declaration
        for declaration in variables.values()
        if declaration.attrib.get("id")
    }
    string_targets = {
        variable_id
        for variable_id in targets
        if variable_id in declarations_by_id
        and declarations_by_id[variable_id].attrib.get("type") == "string"
        and ids_to_names.get(variable_id) not in {"scriptResponse", "Error"}
    }
    structured_targets = {
        variable_id
        for variable_id in targets
        if variable_id in declarations_by_id
        and structured_normalization_roles(declarations_by_id[variable_id])
        == {"tier", "serviceState", "duplicateIssueKey"}
    }
    if len(string_targets - case_key_targets) < 3 and not structured_targets:
        fail(
            "normalization ScriptTask needs either distinct string outputs or "
            "one typed structured result for tier, service state, and trimmed "
            "duplicate key"
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


def require_material_jira_intent(
    elements: list[ET.Element],
    ids_to_names: dict[str, str],
) -> None:
    outputs = [
        output
        for element in elements
        for output in mapping_outputs(element)
        if (
            output.attrib.get("name") == "jiraAction"
            or ids_to_names.get(output.attrib.get("var", "")) == "jiraAction"
        )
    ]
    for output in outputs:
        target = output.attrib.get("var", "")
        if output.attrib.get("source", "").strip() == f"=vars.{target}":
            fail(
                "Jira intent workstream contains a no-op self-assignment "
                "instead of materially deriving jiraAction"
            )
    sources = "\n".join(output.attrib.get("source", "") for output in outputs)
    missing = [
        literal
        for literal in ("UpdateExisting", "CreateIssue", "NoAction")
        if literal not in sources
    ]
    if missing:
        fail(
            "Jira intent workstream must visibly assign all route outcomes; "
            f"missing {missing}"
        )


def forbid_downstream_intents_in_assessment(
    subprocess: ET.Element,
    ids_to_names: dict[str, str],
) -> None:
    forbidden = {
        "jiraAction",
        "attachmentAction",
        "slackAction",
        "responseMode",
        "lastAttachmentName",
    }
    leaked = sorted(
        output_name
        for output_name in output_names_in_elements(
            [subprocess, *list(subprocess.iter())],
            ids_to_names,
        )
        if output_name in forbidden
    )
    if leaked:
        fail(
            "assessment subprocess precomputes outputs owned by downstream "
            f"parallel workstreams: {leaked}"
        )


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


def mapping_propagates_semantic(
    output: ET.Element,
    ids_to_names: dict[str, str],
    semantic_name: str,
    expected_type: str,
) -> bool:
    target_id = output.attrib.get("var", "")
    return (
        output.attrib.get("type") == expected_type
        and target_id in ids_to_names
        and (
            output.attrib.get("name") == semantic_name
            or ids_to_names[target_id] == semantic_name
        )
        and bool(referenced_variable_ids(output.attrib.get("source", "")))
    )


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
    forbid_downstream_intents_in_assessment(subprocess, ids_to_names)
    subprocess_outputs = mapping_outputs(subprocess)
    for name in (
        "route",
        "severity",
        "engineeringNeeded",
        "failureReason",
    ):
        if not any(
            mapping_propagates_semantic(
                item,
                ids_to_names,
                name,
                EXPECTED_OUTPUTS[name],
            )
            for item in subprocess_outputs
        ):
            fail(
                f"assessment subprocess does not propagate {name!r} "
                "to its parent/root scope"
            )

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

    normalization_case_targets = {
        variable_id
        for variable_id in normalization_targets
        if "casekey" in identifier_token(ids_to_names.get(variable_id, ""))
    }
    context_only_ids = {
        variables["businessImpact"].attrib["id"],
        variables["correlationId"].attrib["id"],
        variables["caseKey"].attrib["id"],
        *normalization_case_targets,
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
        if target not in normalization_case_targets
        and target in condition_variable_ids
    }
    declarations_by_id = {
        declaration.attrib["id"]: declaration
        for declaration in variables.values()
        if declaration.attrib.get("id")
    }
    structured_consumed = any(
        structured_normalization_roles(declarations_by_id[target])
        == {"tier", "serviceState", "duplicateIssueKey"}
        and structured_normalization_roles_in_conditions(target, condition_blob)
        == {"tier", "serviceState", "duplicateIssueKey"}
        for target in normalization_targets - normalization_case_targets
        if target in condition_variable_ids
    )
    if len(used_normalized) < 3 and not structured_consumed:
        fail(
            "assessment conditions do not visibly consume normalized tier, "
            "service state, and duplicate key values"
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
    for severity in ("Sev1", "Sev2"):
        if not output_literal_exists(
            boundary_tasks, ids_to_names, "severity", severity
        ):
            fail(
                "Jira boundary path must visibly restore both classified "
                f"severity outcomes; missing {severity}"
            )
    if not output_literal_exists(
        boundary_tasks, ids_to_names, "engineeringNeeded", "true"
    ):
        fail(
            "Jira boundary path must visibly restore engineeringNeeded=true"
        )

    boundary_conditions = []
    for node_id in boundary_region:
        node = root_nodes.get(node_id)
        if node is None or local(node.tag) != "exclusiveGateway":
            continue
        if len(child_refs(node, "outgoing")) < 2:
            continue
        for flow_id in child_refs(node, "outgoing"):
            flow = _root_flows.get(flow_id)
            if flow is None:
                continue
            expression = flow.find(f"./{q(BPMN_NS, 'conditionExpression')}")
            if expression is not None and expression.text:
                boundary_conditions.append(expression.text)
    boundary_condition_blob = "\n".join(boundary_conditions)
    boundary_condition_folded = boundary_condition_blob.casefold()
    if (
        "enterprise" not in boundary_condition_folded
        or "unavailable" not in boundary_condition_folded
        or variables["workaroundAvailable"].attrib["id"]
        not in referenced_variable_ids(boundary_condition_blob)
    ):
        fail(
            "Jira boundary path must visibly distinguish the Sev1 predicate "
            "from its Sev2 default before restoring subprocess-local outputs"
        )
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
        if (
            variables["attachments"].attrib["id"]
            not in referenced_variable_ids(collection)
        ):
            continue
        if loop.attrib.get("inputElement"):
            fail(
                "task-level attachment marker must omit inputElement so "
                "the runtime exposes iterator.item"
            )
        candidates.append(element)
    if len(candidates) != 1:
        fail(
            "attachment branch needs exactly one sequential multi-instance "
            "ScriptTask bound to the attachments input"
        )

    loop_activity = candidates[0]
    if local(loop_activity.tag) != "scriptTask":
        fail("sequential attachment marker must be a ScriptTask")
    script_body = (
        loop_activity.findtext(
            f"./{q(BPMN_NS, 'script')}",
            default="",
        )
        or ""
    )
    if "iterator.item" not in script_body:
        fail(
            "sequential attachment ScriptTask must read iterator.item"
        )
    marker_collection_ids = {
        output.attrib["var"]
        for output in mapping_outputs(loop_activity)
        if output.attrib.get("name") not in {"scriptResponse", "Error"}
        and output.attrib.get("type") == "array"
        and output.attrib.get("var")
    }
    reducer_collection_ids = {
        variables["attachments"].attrib["id"],
        *marker_collection_ids,
    }
    reducers = [
        element
        for element in elements
        if local(element.tag) == "scriptTask"
        and element is not loop_activity
        and element.find(
            f"./{q(BPMN_NS, 'multiInstanceLoopCharacteristics')}"
        )
        is None
        and bool(
            reducer_collection_ids
            & referenced_variable_ids(
            element.findtext(
                f"./{q(BPMN_NS, 'script')}",
                default="",
            )
            or ""
            )
        )
    ]
    if len(reducers) != 1:
        fail(
            "attachment branch needs one post-loop ScriptTask reducer"
        )
    reducer = reducers[0]
    reducer_body = (
        reducer.findtext(f"./{q(BPMN_NS, 'script')}", default="") or ""
    )
    if "length" not in reducer_body and "at(" not in reducer_body:
        fail("post-loop reducer does not select the final attachment")
    reducer_outputs = mapping_outputs(reducer)
    response_ids = {
        output.attrib["var"]
        for output in reducer_outputs
        if output.attrib.get("name") == "scriptResponse"
        and output.attrib.get("var")
    }
    if not any(
        (
            "lastattachmentname"
            in identifier_token(output.attrib.get("name", ""))
            or "lastattachmentname"
            in identifier_token(ids_to_names.get(output.attrib.get("var", ""), ""))
        )
        and (
            output.attrib.get("source") == "=result.response"
            or bool(
                response_ids
                & referenced_variable_ids(output.attrib.get("source", ""))
            )
        )
        for output in reducer_outputs
    ):
        fail(
            "post-loop reducer must map result.response to "
            "lastAttachmentName"
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

    jira_index = next(
        index
        for index, outputs in enumerate(branch_outputs)
        if {"jiraAction"} <= outputs
    )
    require_material_jira_intent(
        region_elements[jira_index],
        ids_to_names,
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
    if len(sys.argv) == 3 and sys.argv[1] == "--registry-evidence":
        extension_type = sys.argv[2]
        if extension_type not in {"BPMN.ScriptTask", "BPMN.Variables"}:
            fail(f"unsupported registry evidence type: {extension_type}")
        load_registry_evidence(extension_type)
        print(f"OK: exact current {extension_type} registry response retained")
        return
    if len(sys.argv) != 1:
        fail(
            "usage: check_customer_escalation_structure.py "
            "[--registry-evidence BPMN.ScriptTask|BPMN.Variables]"
        )
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
    if process.attrib.get("isExecutable") != "false":
        fail(
            "BPMN process must use the current Studio serializer "
            "isExecutable='false' contract"
        )
    migration = process.find(
        f"./{q(BPMN_NS, 'extensionElements')}/"
        f"{q(UIPATH_NS, 'migrationVersion')}"
    )
    if migration is None:
        fail("BPMN process is missing uipath:migrationVersion")
    try:
        migration_version = int(migration.attrib.get("version", ""))
    except ValueError:
        fail("uipath:migrationVersion must be an integer")
    if migration_version < 15:
        fail("BPMN process uses a pre-runtime-contract migration version")

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
    variables, ids_to_names = require_variables(process, start_id, end_id)
    script, scripts, variable_tasks = require_registry_activities(root)
    normalization_targets = require_normalization_script(
        script, variables, ids_to_names, variable_tasks
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
        f"nodes, {len(scripts)} runtime-contract ScriptTasks, an expanded "
        f"assessment subprocess with Jira error boundary and scope propagation, "
        f"sequential attachment iteration with post-loop reduction, and parallel "
        f"workstreams {split!r}->{join!r}"
    )


if __name__ == "__main__":
    main()
