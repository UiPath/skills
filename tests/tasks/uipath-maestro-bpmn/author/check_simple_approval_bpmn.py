#!/usr/bin/env python3

import json
import os
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
    has_uipath_extension,
    one_or_more,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)


def local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def variable(
    variables: list[ET.Element],
    *,
    name: str,
    kind: str,
    element_id: str | None = None,
) -> ET.Element:
    matches = [
        item
        for item in variables
        if local_name(item) == kind
        and item.attrib.get("name") == name
        and (
            element_id is None
            or item.attrib.get("elementId") == element_id
        )
    ]
    if len(matches) != 1:
        scope = f" on {element_id!r}" if element_id else ""
        fail(
            f"expected one {kind} variable named {name!r}{scope}, "
            f"found {len(matches)}"
        )
    return matches[0]


def variable_by_id(
    variables: list[ET.Element],
    variable_id: str,
) -> ET.Element:
    matches = [
        item
        for item in variables
        if item.attrib.get("id") == variable_id
    ]
    if len(matches) != 1:
        fail(
            f"expected one declared variable with id={variable_id!r}, "
            f"found {len(matches)}"
        )
    return matches[0]


def variables_mapping(element: ET.Element) -> ET.Element:
    mapping = element.find(
        "bpmn:extensionElements/uipath:mapping",
        NS,
    )
    if mapping is None:
        fail(f"{attr(element, 'id')!r} is missing a uipath:mapping")
    mapping_type = mapping.find("uipath:type", NS)
    if (
        mapping_type is None
        or mapping_type.attrib.get("value") != "BPMN.Variables"
    ):
        fail(f"{attr(element, 'id')!r} must use a BPMN.Variables mapping")
    return mapping


def main() -> None:
    path, root = parse_bpmn("ExpenseApprovalBpmn")
    bpmn_path = Path(path)
    project_path = bpmn_path.parent / "project.uiproj"
    if not project_path.is_file():
        fail(f"missing project descriptor beside BPMN: {project_path}")
    try:
        project = json.loads(project_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"project.uiproj is not valid JSON: {exc}")
    if project.get("Name") != "ExpenseApprovalBpmn":
        fail("project.uiproj Name must be ExpenseApprovalBpmn")
    if project.get("ProjectType") != "ProcessOrchestration":
        fail("project.uiproj ProjectType must be ProcessOrchestration")
    if "main" in project:
        fail("project.uiproj must not duplicate the runtime main path")

    agent_jobs = [
        task
        for task in elements(root, "serviceTask")
        if has_uipath_extension(task, "Orchestrator.StartAgentJob")
    ]
    if not agent_jobs:
        fail("missing bpmn:serviceTask with Orchestrator.StartAgentJob uipath:activity shell")

    queue_sends = [
        task
        for task in elements(root, "sendTask")
        if has_uipath_extension(task, "Orchestrator.CreateQueueItem")
    ]
    if not queue_sends:
        fail("missing bpmn:sendTask with Orchestrator.CreateQueueItem uipath:activity shell")

    exclusive = one_or_more(root, "exclusiveGateway")
    if not any(attr(gateway, "default") for gateway in exclusive):
        fail("exclusive gateway missing a default sequence-flow reference")

    flows = one_or_more(root, "sequenceFlow")
    if not any(flow.find("bpmn:conditionExpression", NS) is not None for flow in flows):
        fail("missing conditional sequence flow on the gateway branches")

    scripts = elements(root, "scriptTask")
    if not scripts:
        fail("missing bpmn:scriptTask")
    script_task = scripts[0]
    if attr(script_task, "scriptFormat").lower() != "javascript":
        fail('script task must set scriptFormat="JavaScript"')
    if not has_uipath_extension(script_task, "scriptVersion"):
        fail("script task missing uipath:scriptVersion metadata")

    process = root.find("bpmn:process", NS)
    if process is None:
        fail("missing bpmn:process element")
    # `isExecutable` is deliberately not graded: nothing in the CLI reads it
    # (no reference in maestro-sdk/maestro-tool outside the spec), so pack,
    # validate, and the canvas all tolerate any value. The skill documents the
    # scaffold default; failing an agent over an inert attribute would grade
    # style, not behaviour -- see .claude/rules/test-writing.md.

    starts = process.findall("bpmn:startEvent", NS)
    ends = process.findall("bpmn:endEvent", NS)
    if len(starts) != 1 or len(ends) != 1:
        fail("expected exactly one root start event and one root completion end event")
    start, end = starts[0], ends[0]
    start_id, end_id = attr(start, "id"), attr(end, "id")

    entry_point = start.find(
        "bpmn:extensionElements/uipath:entryPointId",
        NS,
    )
    if entry_point is None or not entry_point.attrib.get("value"):
        fail("manual start must declare a stable uipath:entryPointId")
    entry_point_id = entry_point.attrib["value"]
    try:
        UUID(entry_point_id)
    except ValueError:
        fail("manual-start uipath:entryPointId must be a UUID")
    if entry_point_id == "00000000-0000-4000-8000-000000000001":
        fail("manual-start uipath:entryPointId copied the documentation example")

    operate_path = bpmn_path.parent / "operate.json"
    if not operate_path.is_file():
        fail(f"missing generated runtime descriptor beside BPMN: {operate_path}")
    try:
        operate = json.loads(operate_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"operate.json is not valid JSON: {exc}")
    expected_main = f"/content/{bpmn_path.name}#{starts[0].attrib['id']}"
    if operate.get("main") != expected_main:
        fail(f"operate.json main must be {expected_main}")
    if operate.get("contentType") != "ProcessOrchestration":
        fail("operate.json contentType must be ProcessOrchestration")

    entry_points_path = bpmn_path.parent / "entry-points.json"
    if not entry_points_path.is_file():
        fail(f"missing generated entry-point descriptor: {entry_points_path}")
    try:
        entry_points = json.loads(entry_points_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"entry-points.json is not valid JSON: {exc}")
    entries = entry_points.get("entryPoints")
    if not isinstance(entries, list) or len(entries) != 1:
        fail("entry-points.json must contain exactly one manual entry point")
    entry = entries[0]
    if entry.get("uniqueId") != entry_point_id:
        fail("entry-points.json uniqueId must match uipath:entryPointId")
    if entry.get("filePath") != expected_main:
        fail(f"entry-points.json filePath must be {expected_main}")
    if entry.get("type") != "ProcessOrchestration":
        fail("entry-points.json type must be ProcessOrchestration")

    descriptor_path = bpmn_path.parent / "package-descriptor.json"
    if not descriptor_path.is_file():
        fail(f"missing generated package descriptor: {descriptor_path}")
    try:
        descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"package-descriptor.json is not valid JSON: {exc}")
    # Subset, not equality: this map is CLI-generated, so pinning it exactly
    # turns any future CLI addition into an eval failure.
    required_files = {
        "operate.json": "operate.json",
        "entry-points.json": "entry-points.json",
        "bindings.json": "bindings_v2.json",
        bpmn_path.name: bpmn_path.name,
    }
    files = descriptor.get("files")
    if not isinstance(files, dict):
        fail("package-descriptor.json has no files map")
    missing = {k: v for k, v in required_files.items() if files.get(k) != v}
    if missing:
        fail(f"package-descriptor.json files map is missing entries: {missing}")

    variables = process.findall(
        "bpmn:extensionElements/uipath:variables/*",
        NS,
    )
    start_mapping = variables_mapping(start)
    for input_name in ("expenseId", "amount"):
        public_input = variable(
            variables,
            name=input_name,
            kind="input",
            element_id=start_id,
        )
        bridges = [
            output
            for output in start_mapping.findall("uipath:output", NS)
            if output.attrib.get("source")
            == f"=vars.{attr(public_input, 'id')}"
            and output.attrib.get("type") == public_input.attrib.get("type")
            and output.attrib.get("var")
        ]
        if len(bridges) != 1:
            fail(
                f"start event must bridge public {input_name!r} "
                "to its mutable process variable"
            )
        internal_input = variable_by_id(variables, attr(bridges[0], "var"))
        if local_name(internal_input) != "inputOutput":
            fail(f"{input_name!r} start bridge must target uipath:inputOutput")
        if public_input.attrib.get("type") != internal_input.attrib.get("type"):
            fail(f"{input_name!r} public and mutable variable types must match")
        if input_name == "amount" and public_input.attrib.get("type") != "double":
            fail("numeric public and mutable amount variables must use type='double'")

    public_output = variable(
        variables,
        name="decision",
        kind="output",
        element_id=end_id,
    )
    end_mapping = variables_mapping(end)
    output_bridges = [
        output
        for output in end_mapping.findall("uipath:output", NS)
        if output.attrib.get("var") == attr(public_output, "id")
        and output.attrib.get("type") == public_output.attrib.get("type")
        and (output.attrib.get("source") or "").startswith("=vars.")
    ]
    if len(output_bridges) != 1:
        fail("completion end must bridge mutable 'decision' to the public output")
    internal_output_id = output_bridges[0].attrib["source"].removeprefix("=vars.")
    internal_output = variable_by_id(variables, internal_output_id)
    if local_name(internal_output) != "inputOutput":
        fail("'decision' end bridge must read from uipath:inputOutput")
    if public_output.attrib.get("type") != internal_output.attrib.get("type"):
        fail("'decision' public and mutable variable types must match")

    migration_versions = {
        elem.attrib.get("version") for elem in root.findall(".//uipath:migrationVersion", NS)
    }
    numeric_versions = {v for v in migration_versions if v and any(ch.isdigit() for ch in v)}
    if not numeric_versions:
        fail('missing numeric uipath:migrationVersion (e.g. version="11" or "11.5")')

    require_no_private_connector_values(root)
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} contains the documented simple approval BPMN shape")


if __name__ == "__main__":
    main()
