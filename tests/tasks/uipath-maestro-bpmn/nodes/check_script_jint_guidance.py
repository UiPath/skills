#!/usr/bin/env python3
"""Assert the supported ScriptTask serialization and public I/O behavior."""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from uuid import UUID

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
    text_content,
)

FORBIDDEN = (
    "require(",
    "import ",
    "fetch(",
    "XMLHttpRequest",
    "process.",
    "fs.",
    "setTimeout",
    "setInterval",
    "window.",
    "document.",
    "await ",
    "Math.random",
    "Date.now",
    "new Date",
    "crypto.",
)

FLOW_NODE_NAMES = {
    "adHocSubProcess",
    "boundaryEvent",
    "businessRuleTask",
    "callActivity",
    "callChoreography",
    "choreographyTask",
    "complexGateway",
    "endEvent",
    "eventBasedGateway",
    "exclusiveGateway",
    "implicitThrowEvent",
    "inclusiveGateway",
    "intermediateCatchEvent",
    "intermediateThrowEvent",
    "manualTask",
    "parallelGateway",
    "receiveTask",
    "scriptTask",
    "sendTask",
    "serviceTask",
    "startEvent",
    "subChoreography",
    "subProcess",
    "task",
    "transaction",
    "userTask",
}

ERROR_SCHEMA_PROPERTIES = {
    "code": "string",
    "message": "string",
    "detail": "string",
    "category": "string",
    "status": "number",
    "element": "string",
}


def local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def root_variables(root: ET.Element) -> list[ET.Element]:
    process = root.find("bpmn:process", NS)
    if process is None:
        fail("missing bpmn:process")
    return process.findall(
        "bpmn:extensionElements/uipath:variables/*",
        NS,
    )


def exactly_one(
    values: list[ET.Element],
    description: str,
) -> ET.Element:
    if len(values) != 1:
        fail(f"expected exactly one {description}, found {len(values)}")
    return values[0]


def one_variable(
    variables: list[ET.Element],
    *,
    name: str,
    kind: str,
    element_id: str | None,
) -> ET.Element:
    scope = (
        f"scoped to {element_id!r}"
        if element_id is not None
        else "at process scope"
    )
    return exactly_one(
        [
            variable
            for variable in variables
            if local_name(variable) == kind
            and variable.attrib.get("name") == name
            and (
                variable.attrib.get("elementId") == element_id
                if element_id is not None
                else "elementId" not in variable.attrib
            )
        ],
        f"{kind} variable named {name!r} {scope}",
    )


def variable_by_id(
    variables: list[ET.Element],
    variable_id: str,
) -> ET.Element:
    return exactly_one(
        [
            variable
            for variable in variables
            if variable.attrib.get("id") == variable_id
        ],
        f"variable with id {variable_id!r}",
    )


def mapping_outputs(element: ET.Element) -> list[ET.Element]:
    return element.findall(
        "bpmn:extensionElements/uipath:mapping/uipath:output",
        NS,
    )


def variables_mapping(element: ET.Element) -> ET.Element:
    mapping = exactly_one(
        element.findall(
            "bpmn:extensionElements/uipath:mapping",
            NS,
        ),
        f"BPMN.Variables mapping on {attr(element, 'id')!r}",
    )
    if mapping.attrib.get("version") != "v1":
        fail(f"{attr(element, 'id')!r} mapping must use version='v1'")
    mapping_type = exactly_one(
        mapping.findall("uipath:type", NS),
        f"mapping type on {attr(element, 'id')!r}",
    )
    if (
        mapping_type.attrib.get("value") != "BPMN.Variables"
        or mapping_type.attrib.get("version") != "v1"
    ):
        fail(f"{attr(element, 'id')!r} must use a BPMN.Variables v1 mapping")
    return mapping


def bridge_target(
    element: ET.Element,
    *,
    name: str,
    source: str,
    output_type: str,
) -> str:
    output = exactly_one(
        [
            candidate
            for candidate in mapping_outputs(element)
            if candidate.attrib.get("name") == name
            and candidate.attrib.get("source") == source
            and candidate.attrib.get("type") == output_type
            and candidate.attrib.get("var")
        ],
        f"variable bridge from {source!r}",
    )
    return attr(output, "var")


def flow_reference_ids(element: ET.Element, direction: str) -> list[str]:
    return [
        (reference.text or "").strip()
        for reference in element.findall(f"bpmn:{direction}", NS)
    ]


def input_body(node: ET.Element) -> str:
    return (node.attrib.get("value") or text_content(node)).strip()


def strip_js_comments(script: str) -> str:
    result: list[str] = []
    index = 0
    in_string: str | None = None
    while index < len(script):
        char = script[index]
        next_char = script[index + 1] if index + 1 < len(script) else ""
        if in_string:
            result.append(char)
            if char == "\\" and index + 1 < len(script):
                result.append(script[index + 1])
                index += 2
                continue
            if char == in_string:
                in_string = None
            index += 1
            continue
        if char in {'"', "'", "`"}:
            in_string = char
            result.append(char)
            index += 1
            continue
        if char == "/" and next_char == "/":
            index += 2
            while index < len(script) and script[index] not in "\r\n":
                index += 1
            continue
        if char == "/" and next_char == "*":
            index += 2
            while index + 1 < len(script) and script[index : index + 2] != "*/":
                index += 1
            index += 2
            continue
        result.append(char)
        index += 1
    return "".join(result)


def main() -> None:
    path, root = parse_bpmn("RiskScoreScriptBpmn")
    bpmn_path = Path(path)
    project_path = bpmn_path.parent / "project.uiproj"
    if not project_path.is_file():
        fail(f"missing project descriptor beside BPMN: {project_path}")
    try:
        project = json.loads(project_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"project.uiproj is not valid JSON: {exc}")
    if project.get("Name") != "RiskScoreScriptBpmn":
        fail("project.uiproj Name must be RiskScoreScriptBpmn")
    if project.get("ProjectType") != "ProcessOrchestration":
        fail("project.uiproj ProjectType must be ProcessOrchestration")

    process = root.find("bpmn:process", NS)
    if process is None:
        fail("missing bpmn:process")
    if process.attrib.get("isExecutable") not in (None, "false"):
        fail("new projects must preserve the supported executable default")

    start = exactly_one(elements(root, "startEvent"), "root start event")
    end = exactly_one(elements(root, "endEvent"), "root end event")
    task = exactly_one(elements(root, "scriptTask"), "script task")
    start_id = attr(start, "id")
    end_id = attr(end, "id")
    task_id = attr(task, "id")
    for description, element_id in (
        ("StartEvent", start_id),
        ("ScriptTask", task_id),
        ("EndEvent", end_id),
    ):
        if not element_id:
            fail(f"{description} must have a non-empty id")
    if len({start_id, task_id, end_id}) != 3:
        fail("StartEvent, ScriptTask, and EndEvent ids must be distinct")

    flow_nodes = [
        element
        for element in root.iter()
        if local_name(element) in FLOW_NODE_NAMES
    ]
    actual_flow_nodes = [
        (local_name(element), attr(element, "id"))
        for element in flow_nodes
    ]
    expected_flow_nodes = [
        ("startEvent", start_id),
        ("scriptTask", task_id),
        ("endEvent", end_id),
    ]
    if sorted(actual_flow_nodes) != sorted(expected_flow_nodes):
        fail(
            "process must contain exactly StartEvent -> ScriptTask -> EndEvent; "
            f"found {actual_flow_nodes}"
        )

    flows = elements(root, "sequenceFlow")
    if len(flows) != 2:
        fail(f"expected exactly two sequence flows, found {len(flows)}")
    start_flow = exactly_one(
        [
            flow
            for flow in flows
            if attr(flow, "sourceRef") == start_id
            and attr(flow, "targetRef") == task_id
        ],
        "StartEvent-to-ScriptTask sequence flow",
    )
    end_flow = exactly_one(
        [
            flow
            for flow in flows
            if attr(flow, "sourceRef") == task_id
            and attr(flow, "targetRef") == end_id
        ],
        "ScriptTask-to-EndEvent sequence flow",
    )
    start_flow_id = attr(start_flow, "id")
    end_flow_id = attr(end_flow, "id")
    if (
        not start_flow_id
        or not end_flow_id
        or start_flow_id == end_flow_id
        or start_flow_id in {start_id, task_id, end_id}
        or end_flow_id in {start_id, task_id, end_id}
    ):
        fail("sequence flows must have distinct non-empty ids")
    start_incoming_ids = flow_reference_ids(start, "incoming")
    start_outgoing_ids = flow_reference_ids(start, "outgoing")
    if start_incoming_ids or (start_outgoing_ids != [start_flow_id]):
        fail("StartEvent incoming/outgoing references do not match its sequence flow")
    task_incoming_ids = flow_reference_ids(task, "incoming")
    task_outgoing_ids = flow_reference_ids(task, "outgoing")
    if task_incoming_ids != [start_flow_id] or task_outgoing_ids != [end_flow_id]:
        fail("ScriptTask incoming/outgoing references do not match its sequence flows")
    end_incoming_ids = flow_reference_ids(end, "incoming")
    end_outgoing_ids = flow_reference_ids(end, "outgoing")
    if (end_incoming_ids != [end_flow_id]) or end_outgoing_ids:
        fail("EndEvent incoming/outgoing references do not match its sequence flow")

    entry_point = exactly_one(
        start.findall(
            "bpmn:extensionElements/uipath:entryPointId",
            NS,
        ),
        "manual-start entryPointId",
    )
    entry_point_id = entry_point.attrib.get("value", "").strip()
    try:
        UUID(entry_point_id)
    except (ValueError, AttributeError):
        fail("manual start entryPointId must be a valid UUID")
    if entry_point_id == "00000000-0000-4000-8000-000000000001":
        fail("manual start entryPointId copied the documentation example")

    if attr(task, "scriptFormat") != "JavaScript":
        fail('script task must set scriptFormat="JavaScript"')
    script_version = exactly_one(
        task.findall(
            "bpmn:extensionElements/uipath:scriptVersion",
            NS,
        ),
        "scriptVersion",
    )
    version_match = re.fullmatch(r"v(\d+)", script_version.attrib.get("value", ""))
    if version_match is None or int(version_match.group(1)) < 3:
        fail("script task must use a supported vars/metadata script version")
    # These calls also enforce the StartEvent and EndEvent mapping contracts.
    variables_mapping(start)
    task_mapping = variables_mapping(task)
    variables_mapping(end)

    variables = root_variables(root)
    variable_ids = [variable.attrib.get("id", "") for variable in variables]
    if not all(variable_ids) or len(variable_ids) != len(set(variable_ids)):
        fail("all root variables must have unique non-empty ids")

    public_amount = one_variable(
        variables, name="amount", kind="input", element_id=start_id
    )
    public_days = one_variable(
        variables, name="daysOverdue", kind="input", element_id=start_id
    )
    public_risk = one_variable(
        variables, name="riskScore", kind="output", element_id=end_id
    )
    response = one_variable(
        variables, name="scriptResponse", kind="inputOutput", element_id=task_id
    )
    error = one_variable(
        variables, name="Error", kind="inputOutput", element_id=task_id
    )
    for variable, expected_type, description in (
        (public_amount, "double", "public amount"),
        (public_days, "integer", "public daysOverdue"),
        (public_risk, "double", "public riskScore"),
        (response, "double", "scriptResponse"),
    ):
        if variable.attrib.get("type") != expected_type:
            fail(f"{description} variable must use type {expected_type!r}")

    if error.attrib.get("type") != "jsonSchema":
        fail("task-scoped Error must use type='jsonSchema'")
    try:
        error_schema = json.loads(text_content(error).strip())
    except json.JSONDecodeError as exc:
        fail(f"task-scoped Error schema is not valid JSON: {exc}")
    if not isinstance(error_schema, dict) or error_schema.get("type") != "object":
        fail("task-scoped Error schema must describe an object")
    error_properties = error_schema.get("properties")
    if not isinstance(error_properties, dict):
        fail("task-scoped Error schema must declare properties")
    for property_name, property_type in ERROR_SCHEMA_PROPERTIES.items():
        property_schema = error_properties.get(property_name)
        if (
            not isinstance(property_schema, dict)
            or property_schema.get("type") != property_type
        ):
            fail(
                "task-scoped Error schema must declare "
                f"{property_name!r} as {property_type!r}"
            )

    internal_amount_id = bridge_target(
        start,
        name="amount",
        source=f"=vars.{attr(public_amount, 'id')}",
        output_type="double",
    )
    internal_days_id = bridge_target(
        start,
        name="daysOverdue",
        source=f"=vars.{attr(public_days, 'id')}",
        output_type="integer",
    )
    end_output = exactly_one(
        [
            output
            for output in mapping_outputs(end)
            if output.attrib.get("name") == "riskScore"
            and output.attrib.get("var") == attr(public_risk, "id")
            and output.attrib.get("type") == "double"
            and re.fullmatch(
                r"=vars\.[A-Za-z_][A-Za-z0-9_]*",
                output.attrib.get("source", ""),
            )
        ],
        "numeric result to public riskScore output bridge",
    )
    result_variable_id = attr(end_output, "source").removeprefix("=vars.")

    for variable_id, expected_name, expected_type in (
        (internal_amount_id, "amount", "double"),
        (internal_days_id, "daysOverdue", "integer"),
    ):
        variable = variable_by_id(variables, variable_id)
        named_variable = one_variable(
            variables,
            name=expected_name,
            kind="inputOutput",
            element_id=None,
        )
        if named_variable is not variable:
            fail(
                f"{expected_name!r} bridge must target the uniquely scoped "
                "mutable variable"
            )
        if local_name(variable) != "inputOutput":
            fail(f"{variable_id!r} must be a mutable inputOutput variable")
        if variable.attrib.get("name") != expected_name:
            fail(f"{variable_id!r} must be named {expected_name!r}")
        if variable.attrib.get("type") != expected_type:
            fail(f"{variable_id!r} must use type {expected_type!r}")
        if "elementId" in variable.attrib:
            fail(f"{variable_id!r} must remain a process-scoped mutable variable")

    response_id = attr(response, "id")

    if len(mapping_outputs(start)) != 2:
        fail("StartEvent mapping must contain exactly the two public-input bridges")
    if len(mapping_outputs(end)) != 1:
        fail("EndEvent mapping must contain exactly the public-output bridge")

    input_schema = exactly_one(
        task.findall(
            "bpmn:extensionElements/uipath:mapping/uipath:context/uipath:inputSchema",
            NS,
        ),
        "ScriptTask inputSchema",
    )
    if input_schema.attrib.get("type") != "jsonSchema":
        fail("ScriptTask must declare a jsonSchema inputSchema")
    exactly_one(
        task_mapping.findall("uipath:context", NS),
        "ScriptTask mapping context",
    )
    try:
        schema = json.loads(input_body(input_schema))
    except json.JSONDecodeError as exc:
        fail(f"ScriptTask inputSchema is not valid JSON: {exc}")
    properties = schema.get("properties", {}) if isinstance(schema, dict) else {}
    if (
        not isinstance(schema, dict)
        or schema.get("$schema") != "http://json-schema.org/draft-07/schema#"
        or schema.get("type") != "object"
        or schema.get("required") != []
        or set(properties) != {"vars", "metadata"}
    ):
        fail("ScriptTask inputSchema must use the current vars/metadata schema")
    for name in ("vars", "metadata"):
        if not isinstance(properties.get(name), dict) or properties[name].get("type") != "object":
            fail(f"ScriptTask inputSchema must declare {name!r} as an object")

    task_inputs = task.findall(
        "bpmn:extensionElements/uipath:mapping/uipath:input",
        NS,
    )
    args = exactly_one(
        [
            task_input
            for task_input in task_inputs
            if task_input.attrib.get("name") == "args"
        ],
        "ScriptTask args input",
    )
    if len(task_inputs) != 1:
        fail("ScriptTask mapping must contain exactly one args input")
    if args.attrib.get("type") != "json" or args.attrib.get("target") != "bodyField":
        fail("ScriptTask must declare args targeting bodyField")
    try:
        args_value = json.loads(input_body(args))
    except json.JSONDecodeError as exc:
        fail(f"ScriptTask args is not valid JSON: {exc}")
    if args_value != {"vars": "=vars", "metadata": "=metadata"}:
        fail("ScriptTask args must pass exactly vars and metadata")

    script = task.find("bpmn:script", NS)
    if script is None or not text_content(script).strip():
        fail("script task is missing JavaScript source")
    body = strip_js_comments(text_content(script))
    forbidden = [token for token in FORBIDDEN if token in body]
    if forbidden:
        fail(f"script uses APIs outside the Jint boundary: {forbidden}")
    if re.search(r"return\s*\{\s*response\s*:", body):
        fail("ScriptTask must return the intended value without a response wrapper")
    if not re.search(r"(^|[;{}]\s*)return\b", body, re.MULTILINE):
        fail("script must contain an executable return statement")
    for variable_id in (internal_amount_id, internal_days_id):
        if f"vars.{variable_id}" not in body:
            fail(f"script must read input through vars.{variable_id}")

    task_outputs = mapping_outputs(task)
    error_id = attr(error, "id")
    expected_outputs = (
        ("scriptResponse", response_id, "=result.response", response.attrib.get("type")),
        ("Error", error_id, "=Error", "jsonSchema"),
    )
    for name, variable_id, source, output_type in expected_outputs:
        exactly_one(
            [
                output
                for output in task_outputs
                if output.attrib.get("name") == name
                and output.attrib.get("var") == variable_id
                and output.attrib.get("source") == source
                and output.attrib.get("type") == output_type
            ],
            f"{name} output mapping",
        )
    if result_variable_id == response_id:
        if len(task_outputs) != 2:
            fail(
                "a direct scriptResponse-to-EndEvent bridge requires exactly "
                "the two standard ScriptTask outputs"
            )
    else:
        business_result = variable_by_id(variables, result_variable_id)
        named_business_result = one_variable(
            variables,
            name="riskScore",
            kind="inputOutput",
            element_id=task_id,
        )
        if business_result is not named_business_result:
            fail("the optional business result must be the scoped riskScore variable")
        if business_result.attrib.get("type") != "double":
            fail("the optional mutable riskScore variable must use type='double'")
        if len(task_outputs) != 3:
            fail(
                "a distinct riskScore variable requires exactly one custom "
                "output in addition to scriptResponse and Error"
            )
        risk_mapping = exactly_one(
            [
                output
                for output in task_outputs
                if output.attrib.get("name") == "riskScore"
                and output.attrib.get("var") == result_variable_id
                and output.attrib.get("source") == f"=vars.{response_id}"
                and output.attrib.get("type") == "double"
            ],
            "optional scriptResponse-to-riskScore output mapping",
        )
        if risk_mapping.attrib.get("custom") != "true":
            fail("the optional riskScore mapping must be marked custom=true")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} uses the supported ScriptTask contract")


if __name__ == "__main__":
    main()
