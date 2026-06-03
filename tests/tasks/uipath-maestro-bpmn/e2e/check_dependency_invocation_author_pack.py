#!/usr/bin/env python3
"""Assert generic BPMN dependency invocation contracts in a generated project."""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
UIPATH_NS = "http://uipath.org/schema/bpmn"

PROJECT = Path("DependencyInvocationLab/DependencyInvocationLab")
BPMN_NAME = "DependencyInvocationLab.bpmn"
FOLDER_KEY = "99999999-9999-9999-9999-999999999999"
FOLDER_PATH = "Shared/SyntheticLab"
FOLDER_ID = "123456"


@dataclass(frozen=True)
class Dependency:
    name: str
    process_key: str
    wrapper_type: str
    require_folder_id: bool


EXPECTED = [
    Dependency(
        "SyntheticPolicyScoreApi",
        "11111111-1111-1111-1111-111111111111",
        "Orchestrator.ExecuteApiWorkflowAsync",
        False,
    ),
    Dependency(
        "SyntheticInvoiceRobot",
        "22222222-2222-2222-2222-222222222222",
        "Orchestrator.StartJob",
        True,
    ),
    Dependency(
        "SyntheticReviewAgent",
        "44444444-4444-4444-4444-444444444444",
        "Orchestrator.StartAgentJob",
        False,
    ),
    Dependency(
        "SyntheticEchoFunction",
        "33333333-3333-3333-3333-333333333333",
        "Orchestrator.StartJob",
        True,
    ),
]


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing JSON file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path} is not parseable JSON: {exc}")


def parse_bpmn() -> ET.Element:
    path = PROJECT / BPMN_NAME
    if not path.is_file():
        fail(f"missing BPMN file: {path}")
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        fail(f"{path} is not parseable XML: {exc}")


def bpmn_elements(root: ET.Element, local_name: str) -> list[ET.Element]:
    return root.findall(f".//{{{BPMN_NS}}}{local_name}")


def activity_type(element: ET.Element) -> str | None:
    type_elem = element.find(
        f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}activity/{{{UIPATH_NS}}}type"
    )
    return type_elem.attrib.get("value") if type_elem is not None else None


def context_inputs(element: ET.Element) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in element.findall(
        f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}activity/"
        f"{{{UIPATH_NS}}}context/{{{UIPATH_NS}}}input"
    ):
        name = item.attrib.get("name")
        if name:
            values[name] = item.attrib.get("value", "")
    return values


def direct_activity_inputs(element: ET.Element) -> list[ET.Element]:
    return element.findall(
        f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}activity/{{{UIPATH_NS}}}input"
    )


def activity_outputs(element: ET.Element) -> list[ET.Element]:
    return element.findall(
        f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}activity/{{{UIPATH_NS}}}output"
    )


def variable_ids(root: ET.Element) -> set[str]:
    ids: set[str] = set()
    for var in root.findall(f".//{{{UIPATH_NS}}}variables/*"):
        variable_id = var.attrib.get("id")
        if variable_id:
            ids.add(variable_id)
    return ids


def assert_shape(root: ET.Element, bpmn_id: str) -> None:
    shape = root.find(f".//{{{BPMNDI_NS}}}BPMNShape[@bpmnElement='{bpmn_id}']")
    if shape is None:
        fail(f"missing BPMN DI shape for {bpmn_id}")


def assert_edge_count(root: ET.Element) -> None:
    flows = bpmn_elements(root, "sequenceFlow")
    edges = root.findall(f".//{{{BPMNDI_NS}}}BPMNEdge")
    if len(edges) < max(1, len(flows) - 1):
        fail(
            "expected BPMN DI edges for sequence flows, "
            f"found {len(edges)} for {len(flows)} flows"
        )


def find_task_for_dependency(tasks: list[ET.Element], dependency: Dependency) -> ET.Element:
    tasks_with_key = [
        task
        for task in tasks
        if context_inputs(task).get("ReleaseKey") == dependency.process_key
    ]
    if not tasks_with_key:
        seen = sorted(
            {
                value
                for task in tasks
                for value in [context_inputs(task).get("ReleaseKey")]
                if value
            }
        )
        fail(f"missing service task for {dependency.name}; seen ReleaseKey values: {seen}")

    typed = [task for task in tasks_with_key if activity_type(task) == dependency.wrapper_type]
    if len(typed) != 1:
        seen_types = [activity_type(task) for task in tasks_with_key]
        fail(
            f"{dependency.name} should use {dependency.wrapper_type}; "
            f"found wrapper types {seen_types}"
        )
    return typed[0]


def assert_dependency_task(root: ET.Element, tasks: list[ET.Element], dependency: Dependency) -> None:
    task = find_task_for_dependency(tasks, dependency)
    context = context_inputs(task)

    expected_context = {
        "ReleaseKey": dependency.process_key,
        "FolderKey": FOLDER_KEY,
        "FolderPath": FOLDER_PATH,
        "Name": dependency.name,
    }
    if dependency.require_folder_id:
        expected_context["folderId"] = FOLDER_ID

    for field, expected_value in expected_context.items():
        if context.get(field) != expected_value:
            fail(
                f"{dependency.name} context {field} should be {expected_value!r}; "
                f"found {context.get(field)!r}"
            )

    if not direct_activity_inputs(task):
        fail(f"{dependency.name} should map dependency input arguments")

    outputs = activity_outputs(task)
    if not outputs:
        fail(f"{dependency.name} should map dependency outputs")

    declared = variable_ids(root)
    output_targets = {
        output.attrib.get("var") or output.attrib.get("target")
        for output in outputs
        if output.attrib.get("var") or output.attrib.get("target")
    }
    undeclared = sorted(target for target in output_targets if target not in declared)
    if undeclared:
        fail(f"{dependency.name} outputs target undeclared variables: {undeclared}")

    assert_shape(root, task.attrib.get("id", ""))


def assert_no_wrong_coded_function_wrapper(tasks: list[ET.Element]) -> None:
    for task in tasks:
        context = context_inputs(task)
        if context.get("ReleaseKey") != "33333333-3333-3333-3333-333333333333":
            continue
        if activity_type(task) == "Orchestrator.StartAgentJob":
            fail("coded Function dependency was modeled as an Agent job")


def assert_package_metadata(root: ET.Element) -> None:
    project = load_json(PROJECT / "project.uiproj")
    operate = load_json(PROJECT / "operate.json")
    entry_points = load_json(PROJECT / "entry-points.json")
    descriptor = load_json(PROJECT / "package-descriptor.json")
    bindings = load_json(PROJECT / "bindings_v2.json")

    if project.get("main") != BPMN_NAME:
        fail("project.uiproj main does not reference the BPMN file")
    if operate.get("main") != BPMN_NAME:
        fail("operate.json main does not reference the BPMN file")
    if operate.get("contentType") != "ProcessOrchestration":
        fail("operate.json contentType must be ProcessOrchestration")

    starts = bpmn_elements(root, "startEvent")
    if not starts:
        fail("missing start event")
    start_ids = {start.attrib.get("id") for start in starts}
    entry_file_paths = {
        entry.get("filePath") for entry in entry_points.get("entryPoints", [])
    }
    if not any(
        f"/content/{BPMN_NAME}#{start_id}" in entry_file_paths for start_id in start_ids
    ):
        fail("entry-points.json does not point at a BPMN start event")

    content = set(descriptor.get("content") or [])
    for required in (
        f"content/{BPMN_NAME}",
        "content/bindings_v2.json",
        "content/entry-points.json",
        "content/operate.json",
    ):
        if required not in content:
            fail(f"package-descriptor.json missing {required}")

    if bindings.get("version") != "2.0":
        fail("bindings_v2.json must use version 2.0")
    resources = bindings.get("resources")
    if not isinstance(resources, list):
        fail("bindings_v2.json resources must be an array")

    resource_text = json.dumps(resources)
    missing_names = [
        dependency.name for dependency in EXPECTED if dependency.name not in resource_text
    ]
    if missing_names:
        fail(f"bindings_v2.json missing dependency resource entries for: {missing_names}")


def main() -> None:
    root = parse_bpmn()
    raw_xml = (PROJECT / BPMN_NAME).read_text(encoding="utf-8")
    for token in ("invoiceId", "amount", "riskLevel", "requestedBy"):
        if token not in raw_xml:
            fail(f"missing start/input variable token: {token}")

    tasks = bpmn_elements(root, "serviceTask")
    if len(tasks) < 4:
        fail(f"expected at least four service tasks for dependencies, found {len(tasks)}")

    for dependency in EXPECTED:
        assert_dependency_task(root, tasks, dependency)

    assert_no_wrong_coded_function_wrapper(tasks)
    assert_edge_count(root)
    assert_package_metadata(root)
    print(
        "OK: dependency invocation wrappers, mappings, DI, "
        "and package metadata are present"
    )


if __name__ == "__main__":
    main()
