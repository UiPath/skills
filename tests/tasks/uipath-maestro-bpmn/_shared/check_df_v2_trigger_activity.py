#!/usr/bin/env python3
"""Data Fabric V2 trigger -> activity (BPMN): both connector nodes are the V2
elements Studio Web saves, pick the entity `_setup/ensure_folder_entity.py`
recorded, and `refresh` wrote the trigger's package resources.

Checks performed:
  1. The process declares `<uipath:intsvcActivityConfig version="v2" />`.
  2. A bpmn:startEvent carries Intsvc.EventTrigger on uipath-uipath-dataservice
     for EntityTriggers_V3 / UPDATED_V3, with `activityConfigurationVersion`
     v2, a V2 `connection` (not V1 `connectionId`), a `uipath:entryPointId`,
     design-time metadata, and the entity on `folderEntityName`.
  3. A bpmn:sendTask carries Intsvc.ActivityExecution on the same connector
     for CreateEntityRecord_V3, V2 the same way, picking the
     entity and setting `title` to `V2Test`.
  4. `bindings_v2.json` beside the .bpmn has an EventTrigger resource whose
     EntryPointUniqueId is the trigger's entry point id, and the entity
     resource; `entry-points.json` lists the trigger start.
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
    root_bindings,
)
from _shared.check_df_picker_folder_entity import (  # noqa: E402
    picker_values,
    title_of,
)

CONNECTOR_KEY = "uipath-uipath-dataservice"
ACTIVITY_OBJECT = "CreateEntityRecord_V3"
TITLE = "V2Test"


def require_v2(path: str, node: ET.Element, label: str) -> None:
    version = context_value(node, "activityConfigurationVersion")
    if version != "v2":
        fail(f"{path}: {label} activityConfigurationVersion is {version!r}, not 'v2'")
    if not context_value(node, "connection").startswith("=bindings."):
        fail(f"{path}: {label} has no V2 `connection` context input bound to a root binding")
    try:
        metadata = json.loads(context_value(node, "metadata") or "{}")
    except ValueError:
        fail(f"{path}: {label} metadata is not JSON")
    configuration = metadata.get("activityPropertyConfiguration") or {}
    if not configuration.get("uiPathActivityTypeId") or not configuration.get("configuration"):
        fail(f"{path}: {label} metadata has no activityPropertyConfiguration from the design-time client")
    if not (metadata.get("activityMetadata") or {}).get("activity"):
        fail(f"{path}: {label} metadata has no activityMetadata.activity (the catalog entry)")


def one(path: str, nodes: list[ET.Element], label: str) -> ET.Element:
    if len(nodes) != 1:
        fail(f"{path}: expected one {label}, found {len(nodes)}")
    return nodes[0]


def read_json(path: str) -> dict:
    if not os.path.isfile(path):
        fail(f"{path} is missing; run `uip maestro bpmn refresh`")
    with open(path) as f:
        return json.load(f)


def main() -> None:
    with open(os.path.join("_setup", "picker_entity.json")) as f:
        fixture = json.load(f)
    entity = {fixture["name"].lower(), fixture["key"].lower()}

    path, root = parse_bpmn()
    markers = root.findall(".//uipath:intsvcActivityConfig", NS)
    if not any(m.attrib.get("version") == "v2" for m in markers):
        fail(f'{path}: the process does not declare <uipath:intsvcActivityConfig version="v2" />')
    bindings = root_bindings(root)

    trigger = one(
        path,
        [
            e
            for e in elements(root, "startEvent")
            if has_typed_uipath_extension(e, "event", "Intsvc.EventTrigger")
            and context_value(e, "connectorKey") == CONNECTOR_KEY
        ],
        f"Intsvc.EventTrigger start event on {CONNECTOR_KEY}",
    )
    if (context_value(trigger, "objectName"), context_value(trigger, "operation")) != ("EntityTriggers_V3", "UPDATED_V3"):
        fail(f"{path}: the trigger is not EntityTriggers_V3 / UPDATED_V3")
    require_v2(path, trigger, "trigger")
    if context_value(trigger, "connectionId"):
        fail(f"{path}: the trigger keeps the V1 `connectionId` context input")
    entry = trigger.find("./bpmn:extensionElements/uipath:entryPointId", NS)
    entry_point_id = (entry.attrib.get("value") or "") if entry is not None else ""
    if not entry_point_id:
        fail(f"{path}: the trigger start has no uipath:entryPointId")
    if not picker_values(trigger, bindings) & entity:
        fail(f"{path}: the trigger does not pick {fixture['name']} on folderEntityName")

    activity = one(
        path,
        [
            t
            for t in elements(root, "sendTask")
            if has_typed_uipath_extension(t, "activity", "Intsvc.ActivityExecution")
            and context_value(t, "connectorKey") == CONNECTOR_KEY
        ],
        f"Intsvc.ActivityExecution send task on {CONNECTOR_KEY}",
    )
    if context_value(activity, "objectName") != ACTIVITY_OBJECT:
        fail(f"{path}: the activity is {context_value(activity, 'objectName')!r}, not {ACTIVITY_OBJECT}")
    require_v2(path, activity, "activity")
    if not picker_values(activity, bindings) & entity:
        fail(f"{path}: the activity does not pick {fixture['name']} on folderEntityName")
    if title_of(activity) != TITLE:
        fail(f"{path}: the activity sets title to {title_of(activity)!r}, not {TITLE!r}")

    project = os.path.dirname(path)
    resources = read_json(os.path.join(project, "bindings_v2.json")).get("resources") or []
    triggers = [
        r
        for r in resources
        if r.get("resource") == "EventTrigger"
        and ((r.get("value") or {}).get("EntryPointUniqueId") or {}).get("defaultValue") == entry_point_id
    ]
    if not triggers:
        fail(f"{project}/bindings_v2.json has no EventTrigger resource for the trigger's entry point {entry_point_id}")
    if not any(r.get("resource") == "entity" and str(r.get("key", "")).lower() == fixture["key"].lower() for r in resources):
        fail(f"{project}/bindings_v2.json has no entity resource for {fixture['name']}")
    trigger_id = trigger.attrib.get("id", "")
    entry_points = read_json(os.path.join(project, "entry-points.json")).get("entryPoints") or []
    if not any(str(e.get("filePath", "")).endswith(f"#{trigger_id}") for e in entry_points):
        fail(f"{project}/entry-points.json does not list the trigger start {trigger_id}")

    print(f"OK: {path}: V2 trigger and activity on {fixture['name']}, trigger packaged as an entry point")


if __name__ == "__main__":
    main()
