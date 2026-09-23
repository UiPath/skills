#!/usr/bin/env python3
"""Data Fabric smoke_error (BPMN): Create against a non-existent entity;
two Queries against FlowCodeEvalEntity are unaffected by the failure.

Ported from Flow `connector_features/datafabric_connector/smoke_error.yaml`'s
``check_smoke_error.py``: same scenario and the same entity-binding-only
check (Flow's own docstring: "entity-binding check only; topology [the
parallel branch] is not parsed -- the prompt-driven shape plus entity split
already blocks the common wrong-reason paths"), translated from a JSON
node/`inputs.detail` walk to an XML walk over the registry-driven
``Intsvc.ActivityExecution`` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3-4).

BPMN has no fixed home for `entityName`: the registry does not pin it to a
path param, query param, or JSON body key, and a node may also carry it only
as the generic-form `objectName` when the skill emits the generic
entity-CRUD shape instead of the curated per-operation one -- see
BATCH1-ADDENDUM.md "Where connector node values live in BPMN" and its "CI
run 35488848026" section on the two valid activity shapes. Both forms are
accepted here, exactly as `check_df_integration_create_get.py` and
`check_df_smoke_query_filter.py` already do for this connector.

Assertion map (Flow -> BPMN):
  F check_smoke_error.py:29-31  entity_of(node) == NonExistentEntity on a
                                 `.create-entity-record` node              -> is_create_node() + mentions_entity()
  F check_smoke_error.py:32-34  entity_of(node) == FlowCodeEvalEntity on
                                 `.query-entity-records` nodes             -> is_query_node() + mentions_entity()
  F check_smoke_error.py:37-39  `not error_creates` -> fail                -> `error_creates < 1` check
  F check_smoke_error.py:40-42  `len(good_queries) < 2` -> fail            -> `good_queries < 2` check
  I                             locate/parse .bpmn                        -> parse_bpmn()
  T                             curated|generic entity-CRUD classification -> is_create_node()/is_query_node()
  T                             entity name anywhere in inputs             -> mentions_entity()
  DROPPED  topology/parallel-branch parsing    (Flow's own grader does not parse it either -- see its docstring)
  DROPPED  require_no_private_connector_values (not in Flow)
  DROPPED  require_sequence_integrity          (not in Flow; `bpmn validate` criterion covers structure)
  DROPPED  require_di_for_visible_elements     (not in Flow; `bpmn validate` criterion covers structure)

Checks performed:
  1. BPMN file exists and is well-formed XML.
  2. >=1 bpmn:sendTask carries Intsvc.ActivityExecution with connectorKey
     uipath-uipath-dataservice, classified as a Create (curated objectName,
     or generic objectName + Create/POST verb), and mentions
     NonExistentEntity somewhere in its inputs.
  3. >=2 such nodes classified as a Query (curated Query Entity Records
     objectName, or generic objectName + List/GET verb), and mention
     FlowCodeEvalEntity somewhere in their inputs.
"""

from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    NS,
    context_inputs,
    context_value,
    elements,
    fail,
    has_typed_uipath_extension,
    parse_bpmn,
)

CONNECTOR_KEY = "uipath-uipath-dataservice"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
CREATE_ENTITY = "NonExistentEntity"
QUERY_ENTITY = "FlowCodeEvalEntity"
CREATE_CURATED_NAMES = {"createentityrecordcurated", "createentityrecord_v3"}
QUERY_CURATED_NAMES = {"queryentityrecordscurated", "queryentityrecords_v3"}

_CREATE_OP_RE = re.compile(r"^create$", re.IGNORECASE)
_LIST_OP_RE = re.compile(r"^list$", re.IGNORECASE)


def mentions_entity(task: ET.Element, entity: str) -> bool:
    for inp in context_inputs(task):
        value = inp.attrib.get("value") or ""
        text = inp.text or ""
        if entity in value or entity in text:
            return True
    return False


def is_generic_entity_object(object_name: str, entity: str) -> bool:
    return object_name.strip().lower() == entity.strip().lower()


def connector_nodes(root: ET.Element) -> list[ET.Element]:
    return [
        task
        for task in elements(root, "sendTask")
        if has_typed_uipath_extension(task, "activity", ACTIVITY_TYPE)
        and context_value(task, "connectorKey") == CONNECTOR_KEY
    ]


def is_create_node(task: ET.Element, object_name: str, entity: str) -> bool:
    if object_name.strip().lower() in CREATE_CURATED_NAMES:
        return True
    if not is_generic_entity_object(object_name, entity):
        return False
    operation = context_value(task, "operation").strip()
    method = context_value(task, "method").strip().upper()
    return bool(_CREATE_OP_RE.match(operation)) or method == "POST"


def is_query_node(task: ET.Element, object_name: str, entity: str) -> bool:
    if object_name.strip().lower() in QUERY_CURATED_NAMES:
        return True
    if not is_generic_entity_object(object_name, entity):
        return False
    operation = context_value(task, "operation").strip()
    method = context_value(task, "method").strip().upper()
    return bool(_LIST_OP_RE.match(operation)) or method == "GET"


def main() -> None:
    path, root = parse_bpmn()

    error_creates = 0
    good_queries = 0

    for task in connector_nodes(root):
        object_name = context_value(task, "objectName")
        if is_create_node(task, object_name, CREATE_ENTITY) and mentions_entity(task, CREATE_ENTITY):
            error_creates += 1
        if is_query_node(task, object_name, QUERY_ENTITY) and mentions_entity(task, QUERY_ENTITY):
            good_queries += 1

    if error_creates < 1:
        fail(f"no Create Entity Record node targeting {CREATE_ENTITY!r}")
    print(f"OK: {error_creates} Create Entity Record node(s) on {CREATE_ENTITY}")

    if good_queries < 2:
        fail(
            f"expected >=2 Query Entity Records node(s) on {QUERY_ENTITY!r}, "
            f"found {good_queries}"
        )
    print(f"OK: {good_queries} Query Entity Records node(s) on {QUERY_ENTITY}")

    print(
        f"OK: {path} -- create on {CREATE_ENTITY}, {good_queries} query on {QUERY_ENTITY}"
    )


if __name__ == "__main__":
    main()
