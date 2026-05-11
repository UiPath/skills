#!/usr/bin/env python3

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    has_uipath_extension,
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


def root_variables_by_name(root: ET.Element) -> dict[str, str]:
    variables: dict[str, str] = {}
    process = root.find("bpmn:process", NS)
    if process is None:
        return variables
    for variable in process.findall(
        "bpmn:extensionElements/uipath:variables/*",
        NS,
    ):
        name = variable.attrib.get("name")
        variable_id = variable.attrib.get("id")
        if name and variable_id:
            variables[name] = variable_id
    return variables


def first_uipath_input(task: ET.Element, name: str) -> ET.Element | None:
    return task.find(
        f"bpmn:extensionElements/uipath:mapping/uipath:input[@name='{name}']",
        NS,
    )


def uipath_outputs(task: ET.Element) -> list[ET.Element]:
    return task.findall("bpmn:extensionElements/uipath:mapping/uipath:output", NS)


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
    path, root = parse_bpmn("RiskScoreScriptBpmn")
    scripts = elements(root, "scriptTask")
    if not scripts:
        fail("missing bpmn:scriptTask")
    task = scripts[0]
    if attr(task, "scriptFormat").lower() != "javascript":
        fail('script task must set scriptFormat="JavaScript"')
    if not has_uipath_extension(task, "scriptVersion"):
        fail("script task missing uipath:scriptVersion metadata")
    script = task.find("bpmn:script", NS)
    if script is None or not text_content(script).strip():
        fail("script task is missing bpmn:script content")
    body = strip_js_comments(text_content(script))
    present = [token for token in FORBIDDEN if token in body]
    if present:
        fail(f"script uses APIs outside the Jint boundary: {present}")
    if "args." in body:
        fail("script body should read mapped fields as top-level identifiers, not args.*")
    for identifier in ("amount", "daysOverdue"):
        if identifier not in body:
            fail(f"script body should reference mapped input identifier {identifier!r}")

    variables = root_variables_by_name(root)
    for required in ("amount", "daysOverdue", "riskScore"):
        if required not in variables:
            fail(f"missing root variable named {required!r}")

    args_input = first_uipath_input(task, "args")
    if args_input is None:
        fail('script mapping must include uipath:input name="args"')
    args_body = text_content(args_input)
    for variable_name in ("amount", "daysOverdue"):
        expected = f"=vars.{variables[variable_name]}"
        if expected not in args_body:
            fail(f"script args should map {variable_name!r} through {expected!r}")
        if f"={variable_name}" in args_body:
            fail(f"script args should not use bare variable expression ={variable_name}")

    output_var = variables["riskScore"]
    outputs = uipath_outputs(task)
    if not any(out.attrib.get("var") == output_var for out in outputs):
        fail("script output must map to the declared riskScore variable id")
    if not any((out.attrib.get("source") or "").startswith("=result.") for out in outputs):
        fail("script output should map from a result expression such as =result.response")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} contains a Jint-compatible BPMN script task")


if __name__ == "__main__":
    main()
