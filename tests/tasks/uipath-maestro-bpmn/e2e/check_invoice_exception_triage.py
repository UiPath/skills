#!/usr/bin/env python3
"""Check the synthetic InvoiceExceptionTriage BPMN eval output."""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BPMN_NAME = "InvoiceExceptionTriage.bpmn"
BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - test helper should report concise failure
        fail(f"{path} is not valid JSON: {exc}")


def resolve_project() -> Path:
    # Grade the project wherever the agent placed it (top level or nested under
    # a `<Name>Solution/` wrapper — `uip maestro bpmn init` creates the wrapper
    # unless --skip-solution-registration is passed), but pick the real project
    # unambiguously: exactly one InvoiceExceptionTriage.bpmn with project.uiproj
    # beside it, so a stray draft copy is never graded.
    candidates = [
        p for p in Path.cwd().rglob(BPMN_NAME) if (p.parent / "project.uiproj").is_file()
    ]
    if len(candidates) != 1:
        fail(
            f"expected exactly one {BPMN_NAME} with project.uiproj beside it, "
            f"found {[str(p) for p in candidates]}"
        )
    return candidates[0].parent


def main() -> int:
    project = resolve_project()
    bpmn = project / BPMN_NAME

    required_files = [
        "project.uiproj",
        "bindings_v2.json",
        "entry-points.json",
        "operate.json",
        "package-descriptor.json",
    ]
    for name in required_files:
        if not (project / name).is_file():
            fail(f"{name} is missing")

    try:
        root = ET.parse(bpmn).getroot()
    except ET.ParseError as exc:
        fail(f"BPMN XML does not parse: {exc}")

    if local(root.tag) != "definitions":
        fail("BPMN root is not definitions")

    process = root.find(f"{{{BPMN_NS}}}process")
    if process is None:
        fail("BPMN process is missing")

    elements = list(process)
    element_types = {local(elem.tag) for elem in elements}
    for expected in ["startEvent", "scriptTask", "exclusiveGateway", "userTask", "endEvent"]:
        if expected not in element_types:
            fail(f"missing BPMN element type {expected}")

    ids = {elem.attrib.get("id", "") for elem in elements}
    id_blob = " ".join(sorted(ids)).lower()
    for token in ["classify", "risk", "review"]:
        if token not in id_blob:
            fail(f"expected readable element id containing {token!r}")

    sequence_flows = [elem for elem in elements if local(elem.tag) == "sequenceFlow"]
    if len(sequence_flows) < 4:
        fail("expected at least four sequence flows")
    if not any(
        flow.attrib.get("sourceRef", "").lower().find("route") >= 0 for flow in sequence_flows
    ):
        fail("gateway outgoing sequence flows should use a readable routeByRisk id")

    shapes = root.findall(f".//{{{BPMNDI_NS}}}BPMNShape")
    edges = root.findall(f".//{{{BPMNDI_NS}}}BPMNEdge")
    if len(shapes) < 5:
        fail("expected BPMN DI shapes for visible elements")
    if len(edges) < 4:
        fail("expected BPMN DI edges for sequence flows")

    entry_points = load_json(project / "entry-points.json")
    entry_text = json.dumps(entry_points)
    if "InvoiceExceptionTriage.bpmn" not in entry_text:
        fail("entry-points.json must reference InvoiceExceptionTriage.bpmn")

    operate = load_json(project / "operate.json")
    if "InvoiceExceptionTriage.bpmn" not in json.dumps(operate):
        fail("operate.json must reference InvoiceExceptionTriage.bpmn")

    package_descriptor = load_json(project / "package-descriptor.json")
    package_text = json.dumps(package_descriptor)
    for name in ["InvoiceExceptionTriage.bpmn", "entry-points.json", "operate.json"]:
        if name not in package_text:
            fail(f"package-descriptor.json must include {name}")

    print("InvoiceExceptionTriage BPMN project structure is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
