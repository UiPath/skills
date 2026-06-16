#!/usr/bin/env python3
"""Assert the StartJob node was authored from the registry template.

Verifies the core registry-driven loop: the node carries the
Orchestrator.StartJob registry-template payload, its process resource is bound
via the template's bindingInfo (releaseKey), the diagram is present, and no
real-looking GUID was fabricated for the release key.
"""

from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_assertions import (  # noqa: E402
    BPMN_NS,
    UIPATH_NS,
    assert_has_shape,
    assert_package_lifecycle,
    elements,
    fail,
    load_bpmn,
    one_element,
)

PROJECT = Path("RunJobFromRegistry/RunJobFromRegistry")
BPMN_NAME = "RunJobFromRegistry.bpmn"

# A real Orchestrator releaseKey is a GUID. The skill forbids fabricating one,
# so a placeholder is expected instead. Flag a concrete GUID as a fabricated ID.
GUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")


def main() -> None:
    root = load_bpmn(str(PROJECT / BPMN_NAME))

    # The job node must be a serviceTask (Orchestrator.StartJob registry
    # bpmnElement) carrying the registry-template uipath:activity payload.
    job_tasks = []
    for task in elements(root, "serviceTask"):
        activity = task.find(f"{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}activity")
        if activity is None:
            continue
        type_elem = activity.find(f"{{{UIPATH_NS}}}type")
        if type_elem is not None and type_elem.attrib.get("value") == "Orchestrator.StartJob":
            job_tasks.append((task, activity))
    if not job_tasks:
        fail("missing bpmn:serviceTask with Orchestrator.StartJob uipath:activity (registry template)")
    task, activity = job_tasks[0]

    # The template's uipath:context must carry the releaseKey input.
    context = activity.find(f"{{{UIPATH_NS}}}context")
    if context is None:
        fail("Orchestrator.StartJob activity missing uipath:context from the template")
    context_inputs = {
        inp.attrib.get("name"): inp.attrib.get("value")
        for inp in context.findall(f"{{{UIPATH_NS}}}input")
    }
    if "releaseKey" not in context_inputs:
        fail("Orchestrator.StartJob context missing the releaseKey input from the template")

    # bindingInfo: a uipath:Bindings entry must exist for the process resource.
    bindings = root.findall(f".//{{{UIPATH_NS}}}Bindings")
    if not bindings:
        fail("missing uipath:Bindings — process resource must be bound from the template bindingInfo")

    # No fabricated GUID anywhere in the file (placeholders only).
    xml_text = ET.tostring(root, encoding="unicode")
    guids = GUID_RE.findall(xml_text)
    if guids:
        fail(f"fabricated real-looking GUID(s) found (use synthetic placeholders): {sorted(set(guids))}")

    # Structure + diagram + package lifecycle.
    assert_has_shape(root, task.attrib["id"])
    start = one_element(root, "startEvent")
    assert_package_lifecycle(PROJECT, BPMN_NAME, start.attrib["id"])
    print("OK: StartJob authored from registry template with bindingInfo binding and diagram")


if __name__ == "__main__":
    main()
