#!/usr/bin/env python3

import json
import os
import sys
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
    if process.attrib.get("isExecutable") not in (None, "false"):
        fail("new projects must preserve the CLI scaffold executable default")

    starts = process.findall("bpmn:startEvent", NS)
    if len(starts) != 1:
        fail("expected exactly one root start event")
    entry_point = starts[0].find(
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
    expected_files = {
        "operate.json": "operate.json",
        "entry-points.json": "entry-points.json",
        "bindings.json": "bindings_v2.json",
        bpmn_path.name: bpmn_path.name,
    }
    if descriptor.get("files") != expected_files:
        fail("package-descriptor.json must preserve the current CLI root files map")

    variable_names = {
        var.attrib.get("name")
        for var in process.findall("bpmn:extensionElements/uipath:variables/*", NS)
        if var.attrib.get("name")
    }
    for required in ("expenseId", "amount", "decision"):
        if required not in variable_names:
            fail(f"missing root variable named {required!r}")

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
