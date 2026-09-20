#!/usr/bin/env python3
"""Data Fabric integration_create_get (BPMN): Create/Get round-trip + expansionLevel coverage.

Ported from Flow `connector_features/datafabric_connector/integration_create_get.yaml`'s
``check_integration_create_get.py``: same scenario (two Create-then-Get(s) chains
against FlowCodeEvalEntity, with the second chain comparing expansionLevel across
1/2/3), translated from a JSON node/inputs.detail walk to an XML walk over the
registry-driven ``Intsvc.ActivityExecution`` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3-4).

Flow's grader matched node `type` suffixes (``.create-entity-record`` /
``.get-entity-record-by-id``) and read ``pathParameters.entityName`` /
``queryParameters.expansionLevel`` out of ``inputs.detail``. BPMN has no fixed
home for those fields: the registry does not pin where ``entityName`` or
``expansionLevel`` land on the activity (path param, query param, or a JSON
body key), so this checker accepts any of those homes -- see
BATCH1-ADDENDUM.md "Where connector node values live in BPMN".

Checks performed:
  1. BPMN file exists, is well-formed XML, DI and sequence-flow integrity hold.
  2. >=2 bpmn:sendTask nodes carry Intsvc.ActivityExecution with
     connectorKey uipath-uipath-dataservice and objectName naming Create Entity
     Record (Curated or _V3), and mention FlowCodeEvalEntity somewhere in their
     inputs.
  3. >=4 such nodes with objectName naming Get Entity Record By Id (Curated or
     _V3), same entity-mention rule.
  4. The union of expansionLevel values read off those Get nodes covers
     {1, 2, 3} -- from a query input named `expansionLevel`, or a body JSON key
     of the same name.
"""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    NS,
    elements,
    fail,
    has_typed_uipath_extension,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)

ENTITY = "FlowCodeEvalEntity"
CONNECTOR_KEY = "uipath-uipath-dataservice"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
CREATE_NAMES = {"CreateEntityRecordCurated", "CreateEntityRecord_V3"}
GET_NAMES = {"GetEntityRecordByIdCurated", "GetEntityRecord_V3"}
REQUIRED_EXPANSION = {1, 2, 3}


def node_inputs(task: ET.Element) -> list[ET.Element]:
    return task.findall(".//uipath:input", NS)


def context_value(task: ET.Element, name: str) -> str:
    for inp in node_inputs(task):
        if inp.attrib.get("name") == name:
            return inp.attrib.get("value") or (inp.text or "")
    return ""


def mentions_entity(task: ET.Element, entity: str) -> bool:
    for inp in node_inputs(task):
        value = inp.attrib.get("value") or ""
        text = inp.text or ""
        if entity in value or entity in text:
            return True
    return False


def expansion_level(task: ET.Element) -> int | None:
    # A `target="query"` input named expansionLevel (sibling of <uipath:context>).
    for inp in node_inputs(task):
        if inp.attrib.get("name") != "expansionLevel":
            continue
        raw = inp.attrib.get("value")
        if raw is None:
            raw = (inp.text or "").strip()
        try:
            return int(raw)
        except (TypeError, ValueError):
            match = re.search(r"\d+", raw or "")
            if match:
                return int(match.group())
    # Or a key inside the single `target="body"` JSON blob.
    for inp in node_inputs(task):
        if inp.attrib.get("name") != "body" or inp.attrib.get("target") != "body":
            continue
        text = (inp.text or "").strip()
        if not text:
            continue
        try:
            body = json.loads(text)
        except json.JSONDecodeError:
            fail(f"body input on a connector node is not valid JSON: {text[:200]!r}")
        if isinstance(body, dict) and "expansionLevel" in body:
            try:
                return int(body["expansionLevel"])
            except (TypeError, ValueError):
                return None
    return None


def connector_nodes(root: ET.Element) -> list[ET.Element]:
    return [
        task
        for task in elements(root, "sendTask")
        if has_typed_uipath_extension(task, "activity", ACTIVITY_TYPE)
        and context_value(task, "connectorKey") == CONNECTOR_KEY
    ]


def main() -> None:
    path, root = parse_bpmn()

    creates = 0
    gets = 0
    expansion_levels: set[int] = set()

    for task in connector_nodes(root):
        if not mentions_entity(task, ENTITY):
            continue
        object_name = context_value(task, "objectName")
        if object_name in CREATE_NAMES:
            creates += 1
        elif object_name in GET_NAMES:
            gets += 1
            level = expansion_level(task)
            if level is not None:
                expansion_levels.add(level)

    if creates < 2:
        fail(f"expected >=2 Create Entity Record nodes on {ENTITY}, found {creates}")
    print(f"OK: {creates} Create Entity Record node(s) on {ENTITY}")

    if gets < 4:
        fail(f"expected >=4 Get Entity Record By Id nodes on {ENTITY}, found {gets}")
    print(f"OK: {gets} Get Entity Record By Id node(s) on {ENTITY}")

    missing = REQUIRED_EXPANSION - expansion_levels
    if missing:
        fail(
            f"Get nodes missing expansionLevel(s) {sorted(missing)} "
            f"(found: {sorted(expansion_levels)})"
        )
    print(f"OK: Get nodes cover expansionLevel {sorted(expansion_levels)}")

    require_no_private_connector_values(root)
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} has {creates} creates, {gets} gets, expansionLevels={sorted(expansion_levels)}")


if __name__ == "__main__":
    main()
