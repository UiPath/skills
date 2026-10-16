#!/usr/bin/env python3
"""Data Fabric folder-entity picker (BPMN): the connector task creates a record
in the entity `_setup/ensure_folder_entity.py` recorded, with `title` set.

Checks performed:
  1. BPMN file exists and is well-formed XML.
  2. A bpmn:sendTask carries Intsvc.ActivityExecution with connectorKey
     uipath-uipath-dataservice and a `folderEntityName` input naming the
     entity, by name or by key.
  3. That task sets `title` to `PickerTest`, as a `title` input or as a key of
     its `target="body"` JSON.
"""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    BodyShapeError,
    body_object,
    context_inputs,
    context_value,
    elements,
    fail,
    has_typed_uipath_extension,
    parse_bpmn,
)

CONNECTOR_KEY = "uipath-uipath-dataservice"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
TITLE = "PickerTest"


def connector_nodes(root: ET.Element) -> list[ET.Element]:
    return [
        task
        for task in elements(root, "sendTask")
        if has_typed_uipath_extension(task, "activity", ACTIVITY_TYPE)
        and context_value(task, "connectorKey") == CONNECTOR_KEY
    ]


def title_of(task: ET.Element) -> str:
    title = context_value(task, "title")
    if title:
        return title
    try:
        return str(body_object(task).get("title") or "")
    except BodyShapeError as err:
        fail(f"connector task body: {err}")
    return ""


def main() -> None:
    with open(os.path.join("_setup", "picker_entity.json")) as f:
        fixture = json.load(f)
    entity = {fixture["name"].lower(), fixture["key"].lower()}

    path, root = parse_bpmn()
    nodes = connector_nodes(root)
    if not nodes:
        fail(f"{path}: no {ACTIVITY_TYPE} sendTask on {CONNECTOR_KEY}")

    picked = [t for t in nodes if context_value(t, "folderEntityName").lower() in entity]
    if not picked:
        seen = sorted({context_value(t, "folderEntityName") for t in nodes})
        fail(f"{path}: no {CONNECTOR_KEY} task picks {fixture['name']} on folderEntityName (seen: {seen})")

    titles = [title_of(t) for t in picked]
    if TITLE not in titles:
        names = [i.attrib.get("name") for t in picked for i in context_inputs(t)]
        fail(f"{path}: the {fixture['name']} task does not set title to {TITLE!r} (titles: {titles}, inputs: {names})")

    print(f"OK: {path}: {CONNECTOR_KEY} task creates a {fixture['name']} record with title {TITLE!r}")


if __name__ == "__main__":
    main()
