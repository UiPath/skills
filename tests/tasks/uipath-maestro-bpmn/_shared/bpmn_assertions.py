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
    # The canonical wrapper for service-task / businessRuleTask payloads is
    # `<uipath:activity>` per the registry `xmlTemplate`s. `<uipath:mapping>`
    # is used by `BPMN.Variables` and `BPMN.ScriptTask`. Match either so the
    # same helper covers both wrapper families.
    return element.findall(
        f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}activity/{{{UIPATH_NS}}}output"
    ) + element.findall(
        f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}mapping/{{{UIPATH_NS}}}output"
    )


def mapping_inputs(element: ET.Element) -> list[ET.Element]:
    # The canonical wrapper is `<uipath:activity>`; `<uipath:mapping>` is
    # the script-task / variables shape. Match either. Only top-level
    # inputs count — fields inside `<uipath:context>` are wrapper-identity
    # metadata, not request inputs.
    return element.findall(
        f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}activity/{{{UIPATH_NS}}}input"
    ) + element.findall(
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


def descriptor_file_names(descriptor: dict) -> set[str]:
    # Two descriptor shapes are legal. `uip maestro bpmn init` and
    # `uip maestro bpmn update-metadata` write a `files` name -> path map
    # (`"bindings.json": "bindings_v2.json"`); hand-authored synthetic metadata
    # uses a top-level `content` array of `content/<file>` paths. Compare
    # basenames so either shape satisfies the same requirement.
    names: set[str] = set()
    content = descriptor.get("content")
    if isinstance(content, list):
        names.update(Path(str(item)).name for item in content)
    files = descriptor.get("files")
    if isinstance(files, dict):
        for key, value in files.items():
            names.add(Path(str(key)).name)
            names.add(Path(str(value)).name)
    return names


def assert_package_lifecycle(project_dir: Path, bpmn_name: str, start_id: str) -> None:
    project = load_json(project_dir / "project.uiproj")
    operate = load_json(project_dir / "operate.json")
    entry_points = load_json(project_dir / "entry-points.json")
    descriptor = load_json(project_dir / "package-descriptor.json")
    load_json(project_dir / "bindings_v2.json")

    if project.get("ProjectType") != "ProcessOrchestration":
        fail("project.uiproj must declare ProjectType ProcessOrchestration")
    # The CLI never writes `main` into project.uiproj, but it preserves one
    # authored by hand. Only check it when present, and then only for drift.
    if project.get("main") not in (None, bpmn_name):
        fail("project.uiproj main does not reference the BPMN file")

    # `update-metadata` always rewrites operate.json `main` to the entry-point
    # path `/content/<file>#<start-event-id>`; hand-authored metadata uses the
    # bare filename. Accept both.
    operate_main = str(operate.get("main") or "")
    if Path(operate_main.split("#", 1)[0]).name != bpmn_name:
        fail("operate.json main does not reference the BPMN file")
    if operate.get("contentType") != "ProcessOrchestration":
        fail("operate.json contentType must be ProcessOrchestration")

    content = descriptor_file_names(descriptor)
    for required in (
        bpmn_name,
        "bindings_v2.json",
        "entry-points.json",
        "operate.json",
    ):
        if required not in content:
            fail(f"package-descriptor.json missing {required}")

    expected_file_path = f"/content/{bpmn_name}#{start_id}"
    if not any(
        ep.get("filePath") == expected_file_path for ep in entry_points.get("entryPoints", [])
    ):
        fail(f"entry-points.json missing filePath {expected_file_path}")


def assert_generated_project_scaffold(
    project_dir: Path,
    project_name: str,
    bpmn_name: str,
    start_id: str,
    *,
    entry_point_id: str | None = None,
    expected_resource_count: int | None = None,
) -> None:
    """Assert the current CLI-owned Process Orchestration metadata contract."""

    project = load_json(project_dir / "project.uiproj")
    operate = load_json(project_dir / "operate.json")
    entry_points = load_json(project_dir / "entry-points.json")
    bindings = load_json(project_dir / "bindings_v2.json")
    descriptor = load_json(project_dir / "package-descriptor.json")

    if project.get("Name") != project_name:
        fail(f"project.uiproj Name must be {project_name}")
    if project.get("ProjectType") != "ProcessOrchestration":
        fail("project.uiproj ProjectType must be ProcessOrchestration")
    # The CLI never writes `main` into project.uiproj but it preserves a
    # hand-authored one (#2774). Tolerate a preserved key that points at the
    # BPMN file; only a wrong target is a defect.
    for key in ("main", "Main"):
        if key in project and project[key] not in (bpmn_name, f"/content/{bpmn_name}"):
            fail(
                f"project.uiproj {key} must be absent or reference {bpmn_name}, "
                f"found {project[key]!r}"
            )

    expected_main = f"/content/{bpmn_name}#{start_id}"
    if operate.get("main") != expected_main:
        fail(f"operate.json main must be {expected_main}")
    if operate.get("contentType") != "ProcessOrchestration":
        fail("operate.json contentType must be ProcessOrchestration")

    entries = entry_points.get("entryPoints")
    if not isinstance(entries, list) or len(entries) != 1:
        fail("entry-points.json must contain exactly one manual entry point")
    entry = entries[0]
    if entry.get("filePath") != expected_main:
        fail(f"entry-points.json filePath must be {expected_main}")
    if entry.get("type") != "ProcessOrchestration":
        fail("entry-points.json type must be ProcessOrchestration")
    if entry_point_id is not None and entry.get("uniqueId") != entry_point_id:
        fail("entry-points.json uniqueId must match uipath:entryPointId")

    if bindings.get("version") != "2.0":
        fail('bindings_v2.json version must be "2.0"')
    resources = bindings.get("resources")
    if not isinstance(resources, list):
        fail("bindings_v2.json resources must be a list")
    if expected_resource_count is not None and len(resources) != expected_resource_count:
        fail(
            "bindings_v2.json must contain "
            f"{expected_resource_count} resources, found {len(resources)}"
        )

    expected_files = {
        "operate.json": "operate.json",
        "entry-points.json": "entry-points.json",
        "bindings.json": "bindings_v2.json",
        bpmn_name: bpmn_name,
    }
    if descriptor.get("files") != expected_files:
        fail("package-descriptor.json must preserve the current CLI root files map")
