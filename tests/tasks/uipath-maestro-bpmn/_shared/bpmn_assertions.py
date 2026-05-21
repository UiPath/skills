#!/usr/bin/env python3
"""Shared assertions for Maestro BPMN eval sidecar checks."""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
UIPATH_NS = "http://uipath.org/schema/bpmn"


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def load_bpmn(path: str) -> ET.Element:
    bpmn_path = Path(path)
    if not bpmn_path.is_file():
        fail(f"missing BPMN file: {path}")
    try:
        return ET.parse(bpmn_path).getroot()
    except ET.ParseError as exc:
        fail(f"{path} is not parseable XML: {exc}")


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing JSON file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path} is not parseable JSON: {exc}")


def elements(root: ET.Element, kind: str) -> list[ET.Element]:
    return root.findall(f".//{{{BPMN_NS}}}{kind}")


def one_element(root: ET.Element, kind: str) -> ET.Element:
    matches = elements(root, kind)
    if len(matches) != 1:
        fail(f"expected exactly one bpmn:{kind}, found {len(matches)}")
    return matches[0]


def activity_type(element: ET.Element) -> str | None:
    type_elem = element.find(
        f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}activity/{{{UIPATH_NS}}}type"
    )
    return type_elem.attrib.get("value") if type_elem is not None else None


def mapping_outputs(element: ET.Element) -> list[ET.Element]:
    return element.findall(
        f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}mapping/{{{UIPATH_NS}}}output"
    )


def mapping_inputs(element: ET.Element) -> list[ET.Element]:
    return element.findall(
        f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}mapping/{{{UIPATH_NS}}}input"
    )


def variable_names(root: ET.Element) -> set[str]:
    names: set[str] = set()
    for var in root.findall(f".//{{{UIPATH_NS}}}variables/*"):
        name = var.attrib.get("name")
        if name:
            names.add(name)
    return names


def variable_ids(root: ET.Element) -> set[str]:
    ids: set[str] = set()
    for var in root.findall(f".//{{{UIPATH_NS}}}variables/*"):
        variable_id = var.attrib.get("id")
        if variable_id:
            ids.add(variable_id)
    return ids


def assert_has_shape(root: ET.Element, bpmn_id: str) -> None:
    shape = root.find(f".//{{{BPMNDI_NS}}}BPMNShape[@bpmnElement='{bpmn_id}']")
    if shape is None:
        fail(f"missing BPMN DI shape for {bpmn_id}")


def assert_package_lifecycle(project_dir: Path, bpmn_name: str, start_id: str) -> None:
    project = load_json(project_dir / "project.uiproj")
    operate = load_json(project_dir / "operate.json")
    entry_points = load_json(project_dir / "entry-points.json")
    descriptor = load_json(project_dir / "package-descriptor.json")
    load_json(project_dir / "bindings_v2.json")

    if project.get("main") != bpmn_name:
        fail("project.uiproj main does not reference the BPMN file")
    if operate.get("main") != bpmn_name:
        fail("operate.json main does not reference the BPMN file")
    if operate.get("contentType") != "ProcessOrchestration":
        fail("operate.json contentType must be ProcessOrchestration")

    content = set(descriptor.get("content") or [])
    for required in (
        f"content/{bpmn_name}",
        "content/bindings_v2.json",
        "content/entry-points.json",
        "content/operate.json",
    ):
        if required not in content:
            fail(f"package-descriptor.json missing {required}")

    expected_file_path = f"/content/{bpmn_name}#{start_id}"
    if not any(
        ep.get("filePath") == expected_file_path
        for ep in entry_points.get("entryPoints", [])
    ):
        fail(f"entry-points.json missing filePath {expected_file_path}")
