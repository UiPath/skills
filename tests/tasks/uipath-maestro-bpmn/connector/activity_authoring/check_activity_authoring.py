#!/usr/bin/env python3
"""Check provider-neutral authoring of curated and generic IS activities."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


PROJECT = Path("ConnectorContract")
BPMN = PROJECT / "ConnectorContract.bpmn"
PROJECT_FILE = PROJECT / "project.uiproj"
CALL_LOG = Path("mocks/.calls.jsonl")

CONNECTION_ID = "11111111-2222-4333-8444-555555555555"
FOLDER_KEY = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
SOLUTION_RESOURCE_KEY = "solution-resource-synthetic-primary"
CONNECTOR_KEY = "uipath-synthetic-records"
PROFILE = "connector-contract"

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
DI_NS = "http://www.omg.org/spec/DD/20100524/DI"
DC_NS = "http://www.omg.org/spec/DD/20100524/DC"
UIPATH_NS = "http://uipath.org/schema/bpmn"

ALLOWED_ELEMENT_NAMESPACES = {BPMN_NS, BPMNDI_NS, DI_NS, DC_NS, UIPATH_NS}
RECOGNIZED_ELEMENT_NAMESPACES = {
    **dict.fromkeys(
        (
            "definitions",
            "process",
            "extensionElements",
            "startEvent",
            "endEvent",
            "sendTask",
            "sequenceFlow",
            "incoming",
            "outgoing",
        ),
        BPMN_NS,
    ),
    **dict.fromkeys(
        ("BPMNDiagram", "BPMNPlane", "BPMNShape", "BPMNEdge"),
        BPMNDI_NS,
    ),
    "waypoint": DI_NS,
    "Bounds": DC_NS,
    **dict.fromkeys(
        (
            "variables",
            "inputOutput",
            "output",
            "bindings",
            "binding",
            "entryPointId",
            "activity",
            "type",
            "context",
            "input",
        ),
        UIPATH_NS,
    ),
}

STRING_CONTEXT_NAMES = {
    "activityConfigurationVersion",
    "connectorKey",
    "connection",
    "folderKey",
    "operation",
    "objectName",
    "method",
    "path",
}


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def assert_element_namespaces(root: ET.Element) -> None:
    expected_root = f"{{{BPMN_NS}}}definitions"
    if root.tag != expected_root:
        fail(f"BPMN root must be {expected_root!r}, got {root.tag!r}")
    for element in root.iter():
        tag = element.tag
        if not isinstance(tag, str) or not tag.startswith("{"):
            fail(f"XML element {tag!r} must use an approved namespace")
        namespace, separator, name = tag[1:].partition("}")
        if not separator or not namespace or not name:
            fail(f"XML element {tag!r} has an invalid expanded QName")
        if namespace not in ALLOWED_ELEMENT_NAMESPACES:
            fail(f"XML element {name!r} uses unsupported namespace {namespace!r}")
        expected = RECOGNIZED_ELEMENT_NAMESPACES.get(name)
        if expected is not None and namespace != expected:
            fail(
                f"recognized XML element {name!r} must use namespace "
                f"{expected!r}, got {namespace!r}"
            )


def descendants(element: ET.Element, name: str) -> list[ET.Element]:
    return [item for item in element.iter() if local_name(item) == name]


def direct_children(element: ET.Element, name: str) -> list[ET.Element]:
    return [item for item in element if local_name(item) == name]


def one(items: list[ET.Element], label: str) -> ET.Element:
    if len(items) != 1:
        fail(f"expected exactly one {label}, found {len(items)}")
    return items[0]


def unique_named(elements: list[ET.Element], label: str) -> dict[str, ET.Element]:
    result: dict[str, ET.Element] = {}
    for element in elements:
        name = element.get("name")
        if not name:
            fail(f"{label} without a name")
        if name in result:
            fail(f"duplicate {label} name {name!r}")
        result[name] = element
    return result


def json_body(element: ET.Element, label: str) -> Any:
    if element.get("type") != "json":
        fail(f"{label} must have type=json")
    text = (element.text or "").strip()
    if not text:
        fail(f"{label} must carry its JSON body as element content")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        fail(f"{label} is not valid JSON: {exc}")


def binding_reference(value: str | None, label: str) -> str:
    match = re.fullmatch(r"=bindings\.([A-Za-z0-9_-]+)", value or "")
    if not match:
        fail(f"{label} must be an exact =bindings.<id> reference")
    return match.group(1)


def context_for(task: ET.Element) -> tuple[ET.Element, dict[str, ET.Element]]:
    extensions = one(direct_children(task, "extensionElements"), "task extensionElements")
    activity = one(direct_children(extensions, "activity"), "uipath:activity")
    if activity.get("version") != "v1":
        fail(f"task {task.get('id')} activity version must be v1")
    activity_type = one(direct_children(activity, "type"), "uipath:type")
    if (
        activity_type.get("value") != "Intsvc.ActivityExecution"
        or activity_type.get("version") != "v1"
    ):
        fail(f"task {task.get('id')} does not use Intsvc.ActivityExecution V1")
    context = one(direct_children(activity, "context"), "uipath:context")
    return activity, unique_named(direct_children(context, "input"), "context input")


def assert_context(
    task: ET.Element,
    context: dict[str, ET.Element],
    expected: dict[str, str],
) -> None:
    expected_names = {
        *STRING_CONTEXT_NAMES,
        "metadata",
    }
    if set(context) != expected_names:
        fail(
            f"task {task.get('id')} context names differ: "
            f"expected {sorted(expected_names)}, got {sorted(context)}"
        )
    for name, value in expected.items():
        if context[name].get("value") != value:
            fail(
                f"task {task.get('id')} context {name!r} must be {value!r}, "
                f"got {context[name].get('value')!r}"
            )
    for name in STRING_CONTEXT_NAMES:
        if context[name].get("type") != "string":
            fail(
                f"task {task.get('id')} context {name!r} must use type=string"
            )
    if json_body(context["metadata"], "metadata context") != {}:
        fail("raw registry enrichment was serialized as runtime metadata")


def assert_binding_pair(
    task: ET.Element,
    context: dict[str, ET.Element],
    bindings: dict[str, ET.Element],
    resource_key: str,
) -> None:
    connection_ref = binding_reference(
        context["connection"].get("value"), f"{task.get('id')} connection"
    )
    folder_ref = binding_reference(
        context["folderKey"].get("value"), f"{task.get('id')} folderKey"
    )
    if connection_ref == folder_ref:
        fail(f"task {task.get('id')} reused one binding for connection and folder")
    try:
        connection = bindings[connection_ref]
        folder = bindings[folder_ref]
    except KeyError as exc:
        fail(f"task {task.get('id')} references missing binding {exc.args[0]!r}")
    if connection.get("name") == folder.get("name"):
        fail(f"task {task.get('id')} connection and folder bindings need distinct names")

    expected_rows = (
        (connection, "ConnectionId", CONNECTION_ID),
        (folder, "folderKey", FOLDER_KEY),
    )
    for binding, property_attribute, default in expected_rows:
        if binding.get("resource") != "Connection":
            fail(f"binding {binding.get('id')} must use resource=Connection")
        if binding.get("type") != "string":
            fail(f"binding {binding.get('id')} must use type=string")
        if not binding.get("name"):
            fail(f"binding {binding.get('id')} must have a name")
        if binding.get("resourceKey") != resource_key:
            fail(
                f"binding {binding.get('id')} must preserve resourceKey "
                f"{resource_key!r}"
            )
        if binding.get("propertyAttribute") != property_attribute:
            fail(
                f"binding {binding.get('id')} propertyAttribute must be "
                f"{property_attribute!r}"
            )
        if binding.get("default") != default:
            fail(f"binding {binding.get('id')} has the wrong discovered default")


def schema_leaf_types(schema: Any, prefix: str = "") -> dict[str, str]:
    if not isinstance(schema, dict):
        fail("jsonSchema variable body must be an object")
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        fail("every response schema object must have a properties object")
    result: dict[str, str] = {}
    for name, definition in properties.items():
        if "." in name:
            fail(f"response schema retained dotted key {name!r}")
        if not isinstance(definition, dict):
            fail(f"response schema definition for {name!r} must be an object")
        path = f"{prefix}.{name}" if prefix else name
        if isinstance(definition.get("properties"), dict):
            if definition.get("type") not in (None, "object"):
                fail(f"nested response property {path!r} must have object type")
            result.update(schema_leaf_types(definition, path))
        else:
            data_type = definition.get("type")
            if not isinstance(data_type, str):
                fail(f"response property {path!r} is missing a type")
            result[path] = data_type
    return result


def assert_response_schema(
    task: ET.Element,
    activity: ET.Element,
    variables: dict[str, ET.Element],
    expected_leaves: dict[str, str],
) -> str:
    outputs = direct_children(activity, "output")
    output = one(outputs, f"response output for {task.get('id')}")
    if (
        output.get("name") != "response"
        or output.get("type") != "jsonSchema"
        or output.get("source") != "=response"
    ):
        fail(f"task {task.get('id')} did not preserve the registry response output")
    variable_id = output.get("var")
    if not variable_id or variable_id not in variables:
        fail(f"task {task.get('id')} response output references a missing variable")
    variable = variables[variable_id]
    if variable.get("type") != "jsonSchema":
        fail(f"response variable {variable_id} must use type=jsonSchema")
    element_id = variable.get("elementId")
    if element_id is not None and element_id != task.get("id"):
        fail(
            f"response variable {variable_id} has unrelated elementId "
            f"{element_id!r}"
        )
    try:
        schema = json.loads((variable.text or "").strip())
    except json.JSONDecodeError as exc:
        fail(f"response variable {variable_id} has invalid JSON schema: {exc}")
    if schema.get("type") != "object":
        fail(f"response variable {variable_id} schema root must have object type")
    leaves = schema_leaf_types(schema)
    if leaves != expected_leaves:
        fail(
            f"response variable {variable_id} leaves differ: "
            f"expected {expected_leaves}, got {leaves}"
        )
    return variable_id


def assert_operation_inputs(
    activity: ET.Element,
    label: str,
    expected: dict[str, tuple[str, str, str]],
) -> None:
    inputs = unique_named(direct_children(activity, "input"), f"{label} activity input")
    if set(inputs) != set(expected):
        fail(
            f"{label} activity inputs differ: expected {sorted(expected)}, "
            f"got {sorted(inputs)}"
        )
    for name, (data_type, target, value) in expected.items():
        element = inputs[name]
        actual = (
            element.get("type"),
            element.get("target"),
            element.get("value"),
        )
        wanted = (data_type, target, value)
        if actual != wanted:
            fail(f"{label} input {name!r} must be {wanted}, got {actual}")
        if (element.text or "").strip():
            fail(f"{label} scalar input {name!r} must use its value attribute")


def read_calls() -> list[str]:
    if not CALL_LOG.is_file():
        fail("mock CLI call log is missing")
    calls: list[str] = []
    for line in CALL_LOG.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"mock CLI call log is invalid JSON: {exc}")
        calls.append(str(record.get("args", "")))
    return calls


def has_option(call: str, option: str, value: str) -> bool:
    return re.search(
        rf"(?:^|\s){re.escape(option)}(?:=|\s+){re.escape(value)}(?=\s|$)",
        call,
    ) is not None


def has_profile(call: str) -> bool:
    return has_option(call, "--profile", PROFILE)


def index_of(calls: list[str], predicate: Any, label: str) -> int:
    for index, call in enumerate(calls):
        if predicate(call):
            return index
    fail(f"missing CLI discovery call: {label}")


def check_calls() -> None:
    calls = read_calls()
    login_index = index_of(
        calls,
        lambda call: "login status" in call and has_profile(call),
        "named-profile login status",
    )

    parsed_markers = (
        "login status",
        "maestro bpmn registry pull",
        "maestro bpmn registry list",
        "maestro bpmn registry search",
        "maestro bpmn registry get",
        "is connections list",
        "is activities list",
        "is resources list",
        "is resources describe",
    )
    # The required profiled status is located above and must precede discovery.
    # A redundant read-only check of the default status does not select a source.
    profile_markers = (
        "maestro bpmn registry pull",
        "maestro bpmn registry list",
        "maestro bpmn registry search",
        "maestro bpmn registry get Intsvc.ActivityExecution",
        "is connections list",
        "is activities list",
        "is resources list",
        "is resources describe",
    )
    for call in calls:
        if any(marker in call for marker in parsed_markers):
            if any(marker in call for marker in profile_markers) and not has_profile(call):
                fail(f"live discovery call omitted the requested profile: {call}")
            if "--output json" not in call and "--output=json" not in call:
                fail(f"parsed CLI call omitted --output json: {call}")

    for index, call in enumerate(calls):
        if index < login_index and any(
            marker in call
            for marker in profile_markers
            if marker != "login status"
        ):
            fail("tenant-dependent discovery ran before login status")

    pulls = [call for call in calls if "maestro bpmn registry pull" in call]
    if len(pulls) != 1:
        fail(f"registry pull must run exactly once; observed {len(pulls)}")

    base_registry_index = index_of(
        calls,
        lambda call: (
            "maestro bpmn registry get Intsvc.ActivityExecution" in call
            and "--object-name" not in call
        ),
        "base Intsvc.ActivityExecution registry contract",
    )
    connection_indices = [
        index
        for index, call in enumerate(calls)
        if "is connections list uipath-synthetic-records" in call
    ]
    if len(connection_indices) != 1:
        fail(
            "exact connector connection discovery must run once; "
            f"observed {len(connection_indices)}"
        )
    connection_call = calls[connection_indices[0]]
    if "--all-folders" not in connection_call:
        fail("connection discovery was not exhaustive across folders")

    activity_indices = [
        index
        for index, call in enumerate(calls)
        if "is activities list uipath-synthetic-records" in call
    ]
    if len(activity_indices) != 1:
        fail(f"catalog activity discovery must run once; observed {len(activity_indices)}")

    resource_list_indices = [
        index
        for index, call in enumerate(calls)
        if "is resources list uipath-synthetic-records" in call
    ]
    if len(resource_list_indices) != 1:
        fail(f"generic resource discovery must run once; observed {len(resource_list_indices)}")
    resource_list = calls[resource_list_indices[0]]
    if (
        not has_option(resource_list, "--connection-id", CONNECTION_ID)
        or not has_option(resource_list, "--operation", "List")
    ):
        fail("generic resource discovery omitted the exact connection or List operation")

    curated_calls = [
        (index, call)
        for index, call in enumerate(calls)
        if "resources describe uipath-synthetic-records curated_submit_artifact" in call
    ]
    generic_calls = [
        (index, call)
        for index, call in enumerate(calls)
        if "resources describe uipath-synthetic-records ledger_entries" in call
    ]
    for _, call in curated_calls + generic_calls:
        if not has_option(call, "--connection-id", CONNECTION_ID):
            fail(f"resource description omitted the exact connection: {call}")

    curated_available = [
        index
        for index, call in curated_calls
        if not re.search(r"(?:^|\s)--operation(?:=|\s)", call)
    ]
    curated_operation = [
        index
        for index, call in curated_calls
        if has_option(call, "--operation", "Create")
        and not re.search(r"(?:^|\s)-f(?:=|\s)", call)
    ]
    curated_parent = [
        index
        for index, call in curated_calls
        if has_option(call, "--operation", "Create")
        and has_option(call, "-f", "tenant.scope=finance")
    ]
    generic_available = [
        index
        for index, call in generic_calls
        if not re.search(r"(?:^|\s)--operation(?:=|\s)", call)
    ]
    generic_operation = [
        index for index, call in generic_calls
        if has_option(call, "--operation", "List")
    ]
    phases = {
        "curated available operations": curated_available,
        "curated Create schema": curated_operation,
        "curated parent-enriched schema": curated_parent,
        "generic available operations": generic_available,
        "generic List schema": generic_operation,
    }
    for label, indices in phases.items():
        if not indices:
            fail(f"missing required resource-description phase: {label}")
    if not (
        curated_available[0] < curated_operation[0] < curated_parent[0]
        and generic_available[0] < generic_operation[0]
    ):
        fail("resource schemas were not resolved in available -> operation -> parent order")

    for object_name in ("curated_submit_artifact", "ledger_entries"):
        matches = [
            index
            for index, call in enumerate(calls)
            if (
                "maestro bpmn registry get Intsvc.ActivityExecution" in call
                and has_option(call, "--object-name", object_name)
                and has_option(call, "--connection-id", CONNECTION_ID)
            )
        ]
        if not matches:
            fail(f"missing enriched registry identity check for {object_name}")

    if not (
        login_index < base_registry_index
        and connection_indices[0] < activity_indices[0]
        and activity_indices[0] < resource_list_indices[0]
    ):
        fail("discovery did not follow context -> connection -> catalog -> resource order")

    validate_indices = [
        index for index, call in enumerate(calls) if "maestro bpmn validate" in call
    ]
    if not validate_indices:
        fail("local BPMN validation preflight was not attempted")
    if validate_indices[-1] < max(
        curated_parent[0],
        generic_operation[0],
    ):
        fail("BPMN validation preflight was attempted before schema discovery completed")

    forbidden = re.compile(
        r"(?:is\s+resources\s+run|"
        r"is\s+connections\s+(?:create|edit|update|delete)|"
        r"maestro\s+bpmn\s+(?:pack|publish|deploy|debug)|"
        r"solution\s+(?:pack|publish|deploy|activate))"
    )
    for call in calls:
        if forbidden.search(call):
            fail(f"read-only authoring invoked a mutation or external operation: {call}")


def main() -> None:
    if not BPMN.is_file():
        fail(f"{BPMN} is missing")
    if not PROJECT_FILE.is_file():
        fail(f"{PROJECT_FILE} is missing")
    try:
        project = json.loads(PROJECT_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"project.uiproj is invalid JSON: {exc}")
    if project.get("ProjectType") != "ProcessOrchestration":
        fail("project.uiproj must use ProjectType=ProcessOrchestration")
    if project.get("Name") != "ConnectorContract":
        fail("project.uiproj must preserve the CLI-init project Name")

    try:
        root = ET.parse(BPMN).getroot()
    except ET.ParseError as exc:
        fail(f"BPMN is not well-formed XML: {exc}")
    assert_element_namespaces(root)

    process = one(descendants(root, "process"), "bpmn:process")
    process_extensions = one(
        direct_children(process, "extensionElements"), "process extensionElements"
    )
    bindings_root = one(direct_children(process_extensions, "bindings"), "uipath:bindings")
    if bindings_root.get("version") != "v1":
        fail("source bindings must use version=v1")
    binding_elements = direct_children(bindings_root, "binding")
    if len(binding_elements) != 4:
        fail(
            "the distinct solution-resource and standalone identities require "
            f"four bindings; found {len(binding_elements)}"
        )
    bindings = {
        element.get("id", ""): element
        for element in binding_elements
        if element.get("id")
    }
    if len(bindings) != 4:
        fail("binding ids must be present and unique")
    resource_key_counts: dict[str, int] = {}
    for binding in binding_elements:
        key = binding.get("resourceKey", "")
        resource_key_counts[key] = resource_key_counts.get(key, 0) + 1
    if resource_key_counts != {
        SOLUTION_RESOURCE_KEY: 2,
        CONNECTION_ID: 2,
    }:
        fail(
            "bindings did not preserve the existing solution resource key and "
            f"the standalone connection-id fallback: {resource_key_counts}"
        )

    variables_root = one(direct_children(process_extensions, "variables"), "uipath:variables")
    if variables_root.get("version") != "v1":
        fail("response variables must use version=v1")
    variable_elements = [
        variable
        for variable in variables_root
        if local_name(variable) in {"output", "inputOutput"}
    ]
    variables = {
        variable.get("id", ""): variable
        for variable in variable_elements
        if variable.get("id")
    }
    if len(variables) != 2 or len(variable_elements) != 2:
        fail("exactly two output-capable response variables are required")

    start = one(direct_children(process, "startEvent"), "start event")
    end = one(direct_children(process, "endEvent"), "end event")
    tasks = direct_children(process, "sendTask")
    if len(tasks) != 2:
        fail(f"expected exactly two Integration Service send tasks, found {len(tasks)}")

    task_records: dict[str, tuple[ET.Element, ET.Element, dict[str, ET.Element]]] = {}
    for task in tasks:
        activity, context = context_for(task)
        operation = context.get("operation")
        operation_name = operation.get("value") if operation is not None else None
        if not operation_name or operation_name in task_records:
            fail("tasks must have distinct catalog operation identities")
        task_records[operation_name] = (task, activity, context)
    if set(task_records) != {"SubmitArtifact", "ListAllRecords"}:
        fail(f"wrong catalog operations authored: {sorted(task_records)}")

    curated, curated_activity, curated_context = task_records["SubmitArtifact"]
    generic, generic_activity, generic_context = task_records["ListAllRecords"]

    assert_context(
        curated,
        curated_context,
        {
            "activityConfigurationVersion": "v1",
            "connectorKey": CONNECTOR_KEY,
            "operation": "SubmitArtifact",
            "objectName": "curated_submit_artifact",
            "method": "POST",
            "path": "/v1/artifacts",
        },
    )
    assert_binding_pair(curated, curated_context, bindings, SOLUTION_RESOURCE_KEY)
    assert_operation_inputs(
        curated_activity,
        "curated",
        {
            "tenant.scope": ("string", "body", "finance"),
            "artifact.title": ("string", "body", "Quarterly packet"),
            "artifact.details.code": ("string", "body", "Q4-017"),
        },
    )
    curated_variable_id = assert_response_schema(
        curated,
        curated_activity,
        variables,
        {
            "submission.id": "string",
            "submission.state": "string",
            "server.receipt": "string",
        },
    )

    assert_context(
        generic,
        generic_context,
        {
            "activityConfigurationVersion": "v1",
            "connectorKey": CONNECTOR_KEY,
            "operation": "ListAllRecords",
            "objectName": "ledger_entries",
            "method": "GET",
            "path": "/v2/tenants/{tenantId}/ledger-entries",
        },
    )
    assert_binding_pair(generic, generic_context, bindings, CONNECTION_ID)
    assert_operation_inputs(
        generic_activity,
        "generic",
        {
            "tenantId": ("string", "path", "tenant-west"),
            "limit": ("integer", "query", "50"),
        },
    )
    generic_variable_id = assert_response_schema(
        generic,
        generic_activity,
        variables,
        {
            "items": "array",
            "next.token": "string",
            "count": "integer",
        },
    )
    if curated_variable_id == generic_variable_id:
        fail("the two activity responses must not overwrite the same variable")

    flows = direct_children(process, "sequenceFlow")
    if len(flows) != 3:
        fail(f"linear four-node process requires three sequence flows, found {len(flows)}")
    flow_pairs = {(flow.get("sourceRef"), flow.get("targetRef")) for flow in flows}
    expected_pairs = {
        (start.get("id"), curated.get("id")),
        (curated.get("id"), generic.get("id")),
        (generic.get("id"), end.get("id")),
    }
    if flow_pairs != expected_pairs:
        fail(f"activities are not wired in requested order: {flow_pairs}")
    flow_ids_by_pair = {
        (flow.get("sourceRef"), flow.get("targetRef")): flow.get("id")
        for flow in flows
    }
    expected_node_refs = (
        (start, "outgoing", flow_ids_by_pair[(start.get("id"), curated.get("id"))]),
        (curated, "incoming", flow_ids_by_pair[(start.get("id"), curated.get("id"))]),
        (curated, "outgoing", flow_ids_by_pair[(curated.get("id"), generic.get("id"))]),
        (generic, "incoming", flow_ids_by_pair[(curated.get("id"), generic.get("id"))]),
        (generic, "outgoing", flow_ids_by_pair[(generic.get("id"), end.get("id"))]),
        (end, "incoming", flow_ids_by_pair[(generic.get("id"), end.get("id"))]),
    )
    for node, direction, expected_flow_id in expected_node_refs:
        references = direct_children(node, direction)
        if len(references) != 1 or (references[0].text or "").strip() != expected_flow_id:
            fail(
                f"node {node.get('id')} must have one {direction} reference "
                f"to {expected_flow_id}"
            )

    diagrams = descendants(root, "BPMNDiagram")
    diagram = one(diagrams, "bpmndi:BPMNDiagram")
    plane = one(direct_children(diagram, "BPMNPlane"), "bpmndi:BPMNPlane")
    if plane.get("bpmnElement") != process.get("id"):
        fail("BPMNPlane does not reference the process")
    shape_refs = {
        shape.get("bpmnElement")
        for shape in direct_children(plane, "BPMNShape")
    }
    node_ids = {start.get("id"), curated.get("id"), generic.get("id"), end.get("id")}
    if not node_ids.issubset(shape_refs):
        fail(f"BPMN diagram is missing node shapes: {sorted(node_ids - shape_refs)}")
    edge_refs = {
        edge.get("bpmnElement")
        for edge in direct_children(plane, "BPMNEdge")
    }
    flow_ids = {flow.get("id") for flow in flows}
    if not flow_ids.issubset(edge_refs):
        fail(f"BPMN diagram is missing flow edges: {sorted(flow_ids - edge_refs)}")
    for edge in direct_children(plane, "BPMNEdge"):
        if edge.get("bpmnElement") in flow_ids and len(direct_children(edge, "waypoint")) < 2:
            fail(f"diagram edge {edge.get('id')} needs at least two waypoints")

    xml_text = BPMN.read_text(encoding="utf-8")
    for trap in (
        "ISEnrichment",
        "RequestCurated",
        "titleLookup",
        "responseOnlyTrap",
        'name="resourceKey"',
        'name="pathParameters"',
        'name="queryParameters"',
        'name="result"',
        'type="custom"',
        'source="."',
    ):
        if trap in xml_text:
            fail(f"authoring-only or stale contract field leaked into BPMN: {trap}")

    check_calls()
    print(
        "OK: curated + generic activities preserve registry, binding, request, "
        "response, and read-only current V1 contracts"
    )


if __name__ == "__main__":
    main()
