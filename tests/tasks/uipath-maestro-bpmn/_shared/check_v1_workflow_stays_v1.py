#!/usr/bin/env python3
"""An existing V1 workflow stays V1 when a connector node is added to it.

The fixture is a workflow with configured V1 connector nodes and no
`<uipath:intsvcActivityConfig version="v2" />`; Studio Web keeps editing such a
workflow with the V1 component, so every node the agent adds must be V1 too.

Checks performed:
  1. The process still has no V2 marker.
  2. No connector node is V2: no `activityConfigurationVersion` v2 and no
     design-time `activityPropertyConfiguration` in its metadata.
  3. The original nodes (`Start_Trigger`, `Task_CreateRecord`) are still there.
  4. A new Data Service `Intsvc.ActivityExecution` reads a record back
     (object containing `GetEntityRecord`), wired after `Task_CreateRecord`.
"""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    NS,
    context_value,
    elements,
    fail,
    has_typed_uipath_extension,
    parse_bpmn,
)

CONNECTOR_TYPES = ("Intsvc.ActivityExecution", "Intsvc.EventTrigger", "Intsvc.WaitForEvent")


def connector_nodes(root: ET.Element) -> list[ET.Element]:
    nodes = []
    for local in ("sendTask", "serviceTask", "receiveTask", "startEvent", "intermediateCatchEvent", "boundaryEvent"):
        for element in elements(root, local):
            for tag in ("activity", "event"):
                if any(has_typed_uipath_extension(element, tag, t) for t in CONNECTOR_TYPES):
                    nodes.append(element)
                    break
    return nodes


def is_v2(node: ET.Element) -> bool:
    if context_value(node, "activityConfigurationVersion") == "v2":
        return True
    try:
        metadata = json.loads(context_value(node, "metadata") or "{}")
    except ValueError:
        return False
    return isinstance(metadata, dict) and "activityPropertyConfiguration" in metadata


def main() -> None:
    path, root = parse_bpmn("OrdersV1")
    markers = [m.attrib.get("version") for m in root.findall(".//uipath:intsvcActivityConfig", NS)]
    if "v2" in markers:
        fail(f"{path}: the existing V1 workflow was given the V2 marker")

    nodes = connector_nodes(root)
    ids = {n.attrib.get("id") for n in nodes}
    for original in ("Start_Trigger", "Task_CreateRecord"):
        if original not in ids:
            fail(f"{path}: the original connector node {original} is gone")
    v2 = [n.attrib.get("id") for n in nodes if is_v2(n)]
    if v2:
        fail(f"{path}: V2 connector node(s) {v2} in a V1 workflow")

    added = [
        n for n in nodes
        if n.attrib.get("id") not in ("Start_Trigger", "Task_CreateRecord")
        and "GetEntityRecord" in context_value(n, "objectName")
    ]
    if not added:
        seen = sorted(context_value(n, "objectName") for n in nodes)
        fail(f"{path}: no new Data Service node reads a record back (objects: {seen})")
    new_id = added[0].attrib.get("id")
    flows = [
        f for f in elements(root, "sequenceFlow")
        if f.attrib.get("sourceRef") == "Task_CreateRecord" and f.attrib.get("targetRef") == new_id
    ]
    if not flows:
        fail(f"{path}: {new_id} is not wired after Task_CreateRecord")
    print(f"OK: {path}: V1 workflow kept V1; added V1 node {new_id} after Task_CreateRecord")


if __name__ == "__main__":
    main()
