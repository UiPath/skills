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
_porting/BATCH1-ADDENDUM.md "Where connector node values live in BPMN".

The skill's Data Service connector emits TWO valid activity shapes for the
same operation (confirmed against a real CI artifact, 2026-09):

  - The curated per-operation form: ``objectName`` is one of the catalog's
    spellings for the operation -- plain, ``*Curated``/``*V2``, or ``*_V3``
    (``CreateEntityRecord``, ``CreateEntityRecordCurated``,
    ``CreateEntityRecord_V3``, ...). ``uip is activities list`` serves all
    three; the plain one is what codex authored on 2026-09-23.
  - The generic entity-CRUD form: ``objectName`` is the entity name itself
    (``FlowCodeEvalEntity``) on every node, and the verb lives in
    ``operation``/``method`` instead (``Create``/``POST``,
    ``Retrieve``/``GETBYID`` with an ``id`` path input, or
    ``List``/``GET`` with a ``where``/``id`` filter and/or an
    ``expansionLevel`` query input -- the skill retrieves-by-Id through List
    when Retrieve does not accept expansionLevel). Both forms are accepted;
    the task description notes this to the grading reader.

Checks performed:
  1. BPMN file exists and is well-formed XML.
  2. >=2 bpmn:sendTask nodes carry Intsvc.ActivityExecution with
     connectorKey uipath-uipath-dataservice and mention FlowCodeEvalEntity
     somewhere in their inputs, classified as a Create (curated objectName, or
     generic objectName + Create/POST verb).
  3. >=4 such nodes classified as a retrieval (curated Get objectName, or
     generic objectName + Retrieve/GETBYID, or generic objectName + List/GET
     carrying an expansionLevel input or an Id filter).
  4. The union of expansionLevel values read off those retrieval nodes covers
     {1, 2, 3} -- from an input named `expansionLevel` at any depth under the
     activity, or a body JSON key of the same name.

Assertion map (Flow -> BPMN):
  F check_integration_create_get.py:35  creates >= 2                     -> `creates < 2` check
  F check_integration_create_get.py:38  gets >= 4                        -> `gets < 4` check
  F check_integration_create_get.py:41-44 expansionLevel union {1,2,3}   -> `missing` expansionLevel check
  I                                     locate/parse .bpmn               -> parse_bpmn()
  T                                     curated|generic classification   -> is_create_node()/is_retrieval_node()
  T                                     entity name anywhere in inputs   -> mentions_entity()
  T                                     GETBYID/GET(List) equivalence    -> is_retrieval_node() List/GET branch
  T                                     expression/body JSON at any depth -> expansion_level() query-or-body read
  DROPPED  require_no_private_connector_values  (not in Flow grader)
  DROPPED  require_sequence_integrity            (not in Flow grader; `validate` criterion covers structure)
  DROPPED  require_di_for_visible_elements       (not in Flow grader; `validate` criterion covers structure)
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
    context_value,
    elements,
    fail,
    has_typed_uipath_extension,
    parse_bpmn,
)

ENTITY = "FlowCodeEvalEntity"
CONNECTOR_KEY = "uipath-uipath-dataservice"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
CREATE_CURATED_NAMES = {"CreateEntityRecord", "CreateEntityRecordCurated", "CreateEntityRecord_V3"}
GET_CURATED_NAMES = {
    "GetEntityRecord",
    "GetEntityRecordById",
    "GetEntityRecordByIdCurated",
    "GetEntityRecord_V3",
}
REQUIRED_EXPANSION = {1, 2, 3}

_CREATE_OP_RE = re.compile(r"^create$", re.IGNORECASE)
_RETRIEVE_OP_RE = re.compile(r"^retrieve$", re.IGNORECASE)
_LIST_OP_RE = re.compile(r"^list$", re.IGNORECASE)


def node_inputs(task: ET.Element) -> list[ET.Element]:
    return task.findall(".//uipath:input", NS)


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


def has_id_filter(task: ET.Element) -> bool:
    """An `id` input at any target, or a `where`/`filter` input mentioning Id.

    Covers a Retrieve-by-Id done through List/GET: either a direct `id` query
    param, or a `where` expression filtering on the Id field (the shape a real
    CI artifact used: `=js:"'Id' = '" + vars.X.Id + "'"`).
    """
    for inp in node_inputs(task):
        name = (inp.attrib.get("name") or "").lower()
        if name == "id":
            return True
        if name in ("where", "filter"):
            text = (inp.attrib.get("value") or "") + (inp.text or "")
            if re.search(r"\bid\b", text, re.IGNORECASE):
                return True
    return False


def is_generic_entity_object(object_name: str, entity: str) -> bool:
    return object_name.strip().lower() == entity.strip().lower()


def is_create_node(task: ET.Element, object_name: str) -> bool:
    if object_name in CREATE_CURATED_NAMES:
        return True
    if not is_generic_entity_object(object_name, ENTITY):
        return False
    operation = context_value(task, "operation").strip()
    method = context_value(task, "method").strip().upper()
    return bool(_CREATE_OP_RE.match(operation)) or method == "POST"


def is_retrieval_node(task: ET.Element, object_name: str) -> bool:
    if object_name in GET_CURATED_NAMES:
        return True
    if not is_generic_entity_object(object_name, ENTITY):
        return False
    operation = context_value(task, "operation").strip()
    method = context_value(task, "method").strip().upper()
    if _RETRIEVE_OP_RE.match(operation) or method == "GETBYID":
        return True
    if _LIST_OP_RE.match(operation) or method == "GET":
        return expansion_level(task) is not None or has_id_filter(task)
    return False


def main() -> None:
    path, root = parse_bpmn()

    creates = 0
    gets = 0
    expansion_levels: set[int] = set()

    for task in connector_nodes(root):
        if not mentions_entity(task, ENTITY):
            continue
        object_name = context_value(task, "objectName")
        if is_create_node(task, object_name):
            creates += 1
        elif is_retrieval_node(task, object_name):
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

    print(f"OK: {path} has {creates} creates, {gets} gets, expansionLevels={sorted(expansion_levels)}")


if __name__ == "__main__":
    main()
