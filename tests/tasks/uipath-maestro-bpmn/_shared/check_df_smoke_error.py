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

BPMN has no fixed home for `entityName` (BATCH1-ADDENDUM.md "Where connector
node values live in BPMN" and its "CI run 35488848026" section on the two
valid activity shapes). A node names its entity when any one of these
equals it: the generic-form `objectName`, any input's value (path, query,
body or untargeted), or a `/`-separated segment of the context `path` field.

Assertion map (Flow -> BPMN):
  F check_smoke_error.py:29-31  entity_of(node) == NonExistentEntity on a
                                 `.create-entity-record` node              -> is_create_node() + mentions_entity()
  F check_smoke_error.py:32-34  entity_of(node) == FlowCodeEvalEntity on
                                 `.query-entity-records` nodes             -> is_query_node() + mentions_entity()
  F check_smoke_error.py:37-39  `not error_creates` -> fail                -> `error_creates < 1` check
  F check_smoke_error.py:40-42  `len(good_queries) < 2` -> fail            -> `good_queries < 2` check
  F check_smoke_error.py:21     `for path in glob("**/*.flow")`: the first  -> candidate_files(): every .bpmn under
                                 file satisfying the shape passes, else fail    the sandbox, first satisfying file passes
  I                             parse each .bpmn                          -> ET.parse()
  T                             curated|generic entity-CRUD classification -> is_create_node()/is_query_node()
  T                             entity as the generic objectName, an exact -> mentions_entity()
                                 input value on any target, or an exact
                                 context `path` segment
  DROPPED  topology/parallel-branch parsing    (Flow's own grader does not parse it either -- see its docstring)
  DROPPED  require_no_private_connector_values (not in Flow)
  DROPPED  require_sequence_integrity          (not in Flow; `bpmn validate` criterion covers structure)
  DROPPED  require_di_for_visible_elements     (not in Flow; `bpmn validate` criterion covers structure)

Checks performed:
  1. BPMN file exists and is well-formed XML.
  2. >=1 bpmn:sendTask carries Intsvc.ActivityExecution with connectorKey
     uipath-uipath-dataservice, classified as a Create (curated objectName,
     or generic objectName + Create/POST verb), and names
     NonExistentEntity (see mentions_entity above).
  3. >=2 such nodes classified as a Query (curated Query Entity Records
     objectName, or generic objectName + List/GET verb), and name
     FlowCodeEvalEntity.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    NS,
    context_inputs,
    context_value,
    elements,
    fail,
    has_typed_uipath_extension,
)

CONNECTOR_KEY = "uipath-uipath-dataservice"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
CREATE_ENTITY = "NonExistentEntity"
QUERY_ENTITY = "FlowCodeEvalEntity"
CREATE_CURATED_NAMES = {"createentityrecord", "createentityrecordcurated", "createentityrecord_v3"}
QUERY_CURATED_NAMES = {"queryentityrecords", "queryentityrecordscurated", "queryentityrecords_v3"}

_CREATE_OP_RE = re.compile(r"^create$", re.IGNORECASE)
_LIST_OP_RE = re.compile(r"^list$", re.IGNORECASE)


def mentions_entity(task: ET.Element, entity: str) -> bool:
    if is_generic_entity_object(context_value(task, "objectName"), entity):
        return True
    if entity in context_value(task, "path").strip().split("/"):
        return True
    return any(
        (inp.attrib.get("value") or inp.text or "").strip() == entity
        for inp in context_inputs(task)
    )


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


SKIP_PARTS = {"node_modules", ".npm-prefix", ".venv"}


def candidate_files() -> list[Path]:
    """Every .bpmn under the sandbox, as Flow's grader globbed every .flow.

    The agent may split the error path into its own file beside the main
    process (smoke run 36357685718 left DataFabricSmokeError.bpmn and
    DataFabricSmokeError_error.bpmn in one project); Flow passes when ANY
    file satisfies the shape, so the port does the same.
    """
    return sorted(
        p for p in Path.cwd().rglob("*.bpmn") if not (SKIP_PARTS & set(p.parts))
    )


def shape_of(root: ET.Element) -> tuple[int, int]:
    error_creates = 0
    good_queries = 0
    for task in connector_nodes(root):
        object_name = context_value(task, "objectName")
        if is_create_node(task, object_name, CREATE_ENTITY) and mentions_entity(task, CREATE_ENTITY):
            error_creates += 1
        if is_query_node(task, object_name, QUERY_ENTITY) and mentions_entity(task, QUERY_ENTITY):
            good_queries += 1
    return error_creates, good_queries


def main() -> None:
    files = candidate_files()
    if not files:
        fail("no BPMN file found")

    for path in files:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            print(f"FAIL: {path} is not well-formed XML: {exc}", file=sys.stderr)
            continue
        error_creates, good_queries = shape_of(root)
        if error_creates < 1:
            print(
                f"FAIL: {path} -- no Create Entity Record node targeting {CREATE_ENTITY!r}",
                file=sys.stderr,
            )
            continue
        if good_queries < 2:
            print(
                f"FAIL: {path} -- expected >=2 Query Entity Records node(s) on "
                f"{QUERY_ENTITY!r}, found {good_queries}",
                file=sys.stderr,
            )
            continue
        print(f"OK: {error_creates} Create Entity Record node(s) on {CREATE_ENTITY}")
        print(f"OK: {good_queries} Query Entity Records node(s) on {QUERY_ENTITY}")
        print(f"OK: {path} -- create on {CREATE_ENTITY}, {good_queries} query on {QUERY_ENTITY}")
        return

    fail("no .bpmn satisfies the error-path shape")


if __name__ == "__main__":
    main()
