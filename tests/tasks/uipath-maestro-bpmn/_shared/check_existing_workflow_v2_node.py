#!/usr/bin/env python3
"""A connector node added to an existing V1 workflow is V2.

The fixture is a workflow with configured V1 connector nodes and no
`<uipath:intsvcActivityConfig version="v2" />`. Studio Web opens a node that
declares `activityConfigurationVersion` v2 with the V2 component whatever the
workflow says, so the new node is V2, and the marker is never added (it would
make Studio Web read the existing unversioned V1 nodes as V2).

Checks performed:
  1. The process still has no V2 marker.
  2. The original nodes (`Start_Trigger`, `Task_CreateRecord`) are still
     there and still V1.
  3. A new Data Service `Intsvc.ActivityExecution` reads a record back
     (object containing `GetEntityRecord`), is V2 (version v2 and design-time
     `activityPropertyConfiguration`), and is wired after `Task_CreateRecord`.
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
    if context_value(node, "activityConfigurationVersion") != "v2":
        return False
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
    changed = [
        n.attrib.get("id") for n in nodes
        if n.attrib.get("id") in ("Start_Trigger", "Task_CreateRecord")
        and context_value(n, "activityConfigurationVersion") == "v2"
    ]
    if changed:
        fail(f"{path}: existing V1 node(s) {changed} were rewritten as V2; the task asked to keep them as they are")

    added = [
        n for n in nodes
        if n.attrib.get("id") not in ("Start_Trigger", "Task_CreateRecord")
        and "GetEntityRecord" in context_value(n, "objectName")
    ]
    if not added:
        seen = sorted(context_value(n, "objectName") for n in nodes)
        fail(f"{path}: no new Data Service node reads a record back (objects: {seen})")
    new_id = added[0].attrib.get("id")
    if not is_v2(added[0]):
        fail(f"{path}: the new node {new_id} is not a V2 element (no activityConfigurationVersion v2 with design-time metadata)")
    flows = [
        f for f in elements(root, "sequenceFlow")
        if f.attrib.get("sourceRef") == "Task_CreateRecord" and f.attrib.get("targetRef") == new_id
    ]
    if not flows:
        fail(f"{path}: {new_id} is not wired after Task_CreateRecord")
    print(f"OK: {path}: added V2 node {new_id} after Task_CreateRecord; no marker, V1 nodes kept")


if __name__ == "__main__":
    main()
