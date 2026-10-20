#!/usr/bin/env python3
"""Data Fabric folder-entity picker (BPMN): the connector task creates a record
in the entity `_setup/ensure_folder_entity.py` recorded, with `title` set.

Checks performed:
  1. BPMN file exists and is well-formed XML.
  2. A bpmn:sendTask carries Intsvc.ActivityExecution with connectorKey
     uipath-uipath-dataservice and a `folderEntityName` value naming the
     entity, by name or by key: a V1 `folderEntityName` input, or the
     `folderEntityName` key of a V2 `queryParameters` JSON input, either one
     literal or a `=bindings.<id>` read of a root `entity` binding.
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


def root_bindings(root: ET.Element) -> dict[str, dict[str, str]]:
    return {
        b.attrib["id"]: dict(b.attrib)
        for b in root.iter("{http://uipath.org/schema/bpmn}binding")
        if b.attrib.get("id")
    }


def json_input(task: ET.Element, target: str) -> dict:
    """The JSON object of ``task``'s ``uipath:input`` with ``target``, else ``{}``."""
    for inp in context_inputs(task):
        if inp.attrib.get("target") == target:
            try:
                parsed = json.loads((inp.text or "").strip() or "{}")
            except ValueError:
                return {}
            return parsed if isinstance(parsed, dict) else {}
    return {}


def resolved(value: str, bindings: dict[str, dict[str, str]]) -> set[str]:
    """``value`` itself, and for ``=bindings.<id>`` what that binding points at."""
    values = {value.lower()}
    if value.startswith("=bindings."):
        binding = bindings.get(value[len("=bindings.") :], {})
        values |= {binding.get(k, "").lower() for k in ("default", "resourceKey")}
    return values - {""}


def picker_values(task: ET.Element, bindings: dict[str, dict[str, str]], field: str = "folderEntityName") -> set[str]:
    """Every value ``task`` gives ``field``, V1 input or V2 JSON input, bindings resolved."""
    raw = [
        context_value(task, field),
        str(json_input(task, "queryParameters").get(field) or ""),
        str((body_parameters(task)).get(field) or ""),
    ]
    return set().union(*(resolved(v, bindings) for v in raw if v))


def body_parameters(task: ET.Element) -> dict:
    try:
        body = body_object(task)
    except BodyShapeError:
        return {}
    parameters = body.get("parameters")
    return parameters if isinstance(parameters, dict) else {}


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

    bindings = root_bindings(root)
    picked = [t for t in nodes if picker_values(t, bindings) & entity]
    if not picked:
        seen = sorted(set().union(*(picker_values(t, bindings) for t in nodes)))
        fail(f"{path}: no {CONNECTOR_KEY} task picks {fixture['name']} on folderEntityName (seen: {seen})")

    titles = [title_of(t) for t in picked]
    if TITLE not in titles:
        names = [i.attrib.get("name") for t in picked for i in context_inputs(t)]
        fail(f"{path}: the {fixture['name']} task does not set title to {TITLE!r} (titles: {titles}, inputs: {names})")

    print(f"OK: {path}: {CONNECTOR_KEY} task creates a {fixture['name']} record with title {TITLE!r}")


if __name__ == "__main__":
    main()
