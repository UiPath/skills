#!/usr/bin/env python3

from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET

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

FORBIDDEN = [
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
]


def root_variables(root: ET.Element) -> list[ET.Element]:
    process = root.find("bpmn:process", NS)
    if process is None:
        return []
    return process.findall(
        "bpmn:extensionElements/uipath:variables/*",
        NS,
    )


def local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def one_variable(
    variables: list[ET.Element],
    *,
    name: str,
    kind: str,
    element_id: str | None,
) -> ET.Element:
    matches = [
        variable
        for variable in variables
        if local_name(variable) == kind
        and variable.attrib.get("name") == name
        and variable.attrib.get("elementId") == element_id
    ]
    if len(matches) != 1:
        fail(
            f"expected exactly one {kind} variable named {name!r} "
            f"with elementId={element_id!r}, found {len(matches)}"
        )
    return matches[0]


def variable_by_id(
    variables: list[ET.Element],
    variable_id: str,
) -> ET.Element:
    matches = [
        variable
        for variable in variables
        if variable.attrib.get("id") == variable_id
    ]
    if len(matches) != 1:
        fail(
            f"expected exactly one variable with id={variable_id!r}, "
            f"found {len(matches)}"
        )
    return matches[0]


def first_uipath_input(task: ET.Element, name: str) -> ET.Element | None:
    return task.find(
        f"bpmn:extensionElements/uipath:mapping/uipath:input[@name='{name}']",
        NS,
    )


def uipath_outputs(task: ET.Element) -> list[ET.Element]:
    return task.findall("bpmn:extensionElements/uipath:mapping/uipath:output", NS)


def one_output(
    element: ET.Element,
    *,
    name: str | None,
    var: str,
    source: str,
    output_type: str,
) -> ET.Element:
    matches = [
        output
        for output in uipath_outputs(element)
        if (name is None or output.attrib.get("name") == name)
        and output.attrib.get("var") == var
        and output.attrib.get("source") == source
        and output.attrib.get("type") == output_type
    ]
    if len(matches) != 1:
        fail(
            f"{element.attrib.get('id')!r} must map "
            f"{name if name is not None else var!r} exactly once to "
            f"var={var!r} from source={source!r} as type={output_type!r}"
        )
    return matches[0]


def bridge_target(
    element: ET.Element,
    *,
    source: str,
    output_type: str,
) -> str:
    matches = [
        output
        for output in uipath_outputs(element)
        if output.attrib.get("source") == source
        and output.attrib.get("type") == output_type
        and output.attrib.get("var")
    ]
    if len(matches) != 1:
        fail(
            f"{element.attrib.get('id')!r} must bridge source={source!r} "
            f"exactly once as type={output_type!r}"
        )
    return matches[0].attrib["var"]


def strip_js_comments(script: str) -> str:
    result = []
    index = 0
    in_string: str | None = None
    while index < len(script):
        char = script[index]
        next_char = script[index + 1] if index + 1 < len(script) else ""
        if in_string:
            result.append(char)
            if char == "\\":
                if index + 1 < len(script):
                    result.append(script[index + 1])
                    index += 2
                    continue
            elif char == in_string:
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
            while index + 1 < len(script) and not (
                script[index] == "*" and script[index + 1] == "/"
            ):
                index += 1
            index += 2
            continue
        result.append(char)
        index += 1
    return "".join(result)


def main() -> None:
    path, root = parse_bpmn()
    process = root.find("bpmn:process", NS)
    if process is None:
        fail("missing bpmn:process")
    if process.attrib.get("isExecutable") != "false":
        fail('process must use the Studio serializer contract isExecutable="false"')

    starts = elements(root, "startEvent")
    ends = elements(root, "endEvent")
    if len(starts) != 1 or len(ends) != 1:
        fail("expected exactly one root start and one root end")
    start = starts[0]
    end = ends[0]
    start_id = attr(start, "id")
    end_id = attr(end, "id")

    scripts = elements(root, "scriptTask")
    if len(scripts) != 1:
        fail(f"expected exactly one bpmn:scriptTask, found {len(scripts)}")
    task = scripts[0]
    task_id = attr(task, "id")
    if attr(task, "scriptFormat").lower() != "javascript":
        fail('script task must set scriptFormat="JavaScript"')
    script_version = task.find(
        "bpmn:extensionElements/uipath:scriptVersion",
        NS,
    )
    if script_version is None or script_version.attrib.get("value") != "v3":
        fail('script task must declare uipath:scriptVersion value="v3"')
    mapping_type = task.find(
        "bpmn:extensionElements/uipath:mapping/uipath:type",
        NS,
    )
    if (
        mapping_type is None
        or mapping_type.attrib.get("value") != "BPMN.Variables"
    ):
        fail("v3 script task must use the Studio BPMN.Variables mapping")

    script = task.find("bpmn:script", NS)
    if script is None or not text_content(script).strip():
        fail("script task is missing bpmn:script content")
    body = strip_js_comments(text_content(script))
    present = [token for token in FORBIDDEN if token in body]
    if present:
        fail(f"script uses APIs outside the Jint boundary: {present}")
    if "args." in body:
        fail("script body must read process variables through vars.*, not args.*")
    if re.search(r"return\s*\{\s*response\s*:", body):
        fail("v3 script must return the intended value directly, without a response wrapper")

    variables = root_variables(root)
    public_amount = one_variable(
        variables,
        name="amount",
        kind="input",
        element_id=start_id,
    )
    public_days = one_variable(
        variables,
        name="daysOverdue",
        kind="input",
        element_id=start_id,
    )
    public_risk = one_variable(
        variables,
        name="riskScore",
        kind="output",
        element_id=end_id,
    )
    response = one_variable(
        variables,
        name="scriptResponse",
        kind="inputOutput",
        element_id=task_id,
    )
    error = one_variable(
        variables,
        name="Error",
        kind="inputOutput",
        element_id=task_id,
    )
    if error.attrib.get("type") != "jsonSchema":
        fail("script Error variable must use type=jsonSchema")

    public_amount_id = attr(public_amount, "id")
    public_days_id = attr(public_days, "id")
    public_risk_id = attr(public_risk, "id")
    response_id = attr(response, "id")
    error_id = attr(error, "id")

    expected_types = {
        public_amount_id: "number",
        public_days_id: "integer",
        public_risk_id: "number",
        response_id: "number",
        error_id: "jsonSchema",
    }
    for variable_id, expected_type in expected_types.items():
        variable = variable_by_id(variables, variable_id)
        if variable.attrib.get("type") != expected_type:
            fail(
                f"variable {variable_id!r} must use type={expected_type!r}, "
                f"got {variable.attrib.get('type')!r}"
            )

    internal_amount_id = bridge_target(
        start,
        source=f"=vars.{public_amount_id}",
        output_type="number",
    )
    internal_days_id = bridge_target(
        start,
        source=f"=vars.{public_days_id}",
        output_type="integer",
    )
    end_outputs = [
        output
        for output in uipath_outputs(end)
        if output.attrib.get("var") == public_risk_id
        and output.attrib.get("type") == "number"
        and (output.attrib.get("source") or "").startswith("=vars.")
    ]
    if len(end_outputs) != 1:
        fail("root end must bridge one mutable number into public riskScore")
    internal_risk_id = end_outputs[0].attrib["source"].removeprefix("=vars.")

    for variable_id, expected_type, expected_element in (
        (internal_amount_id, "number", start_id),
        (internal_days_id, "integer", start_id),
        (internal_risk_id, "number", task_id),
    ):
        variable = variable_by_id(variables, variable_id)
        if local_name(variable) != "inputOutput":
            fail(f"mutable variable {variable_id!r} must be uipath:inputOutput")
        if variable.attrib.get("type") != expected_type:
            fail(
                f"mutable variable {variable_id!r} must use "
                f"type={expected_type!r}"
            )
        if variable.attrib.get("elementId") != expected_element:
            fail(
                f"mutable variable {variable_id!r} must bind to "
                f"elementId={expected_element!r}"
            )

    for variable_id in (internal_amount_id, internal_days_id):
        if f"vars.{variable_id}" not in body:
            fail(f"script body must read mutable input through vars.{variable_id}")

    args_input = first_uipath_input(task, "args")
    if args_input is None:
        fail('script mapping must include uipath:input name="args"')
    if args_input.attrib.get("target") != "bodyField":
        fail("script args input must target bodyField")
    args_body = f"{args_input.attrib.get('value', '')} {text_content(args_input)}"
    for expected in ('"vars":"=vars"', '"metadata":"=metadata"'):
        if expected not in re.sub(r"\s+", "", args_body):
            fail(f"script args must contain {expected}")
    input_schema = task.find(
        "bpmn:extensionElements/uipath:mapping/uipath:context/"
        "uipath:inputSchema",
        NS,
    )
    schema_body = text_content(input_schema) if input_schema is not None else ""
    if '"vars"' not in schema_body or '"metadata"' not in schema_body:
        fail("v3 script input schema must describe vars and metadata")

    one_output(
        task,
        name="scriptResponse",
        var=response_id,
        source="=result.response",
        output_type="number",
    )
    one_output(
        task,
        name="Error",
        var=error_id,
        source="=Error",
        output_type="jsonSchema",
    )
    risk_output = one_output(
        task,
        name=None,
        var=internal_risk_id,
        source=f"=vars.{response_id}",
        output_type="number",
    )
    if risk_output.attrib.get("custom") != "true":
        fail("riskScore process mapping must be marked custom=true")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} contains a Jint-compatible BPMN script task")


if __name__ == "__main__":
    main()
