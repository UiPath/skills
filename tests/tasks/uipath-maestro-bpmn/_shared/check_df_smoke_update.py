#!/usr/bin/env python3
"""Data Fabric smoke_update (BPMN): Create -> partial Update -> Get -> Delete.

Ported from Flow `connector_features/datafabric_connector/smoke_update.yaml`'s
two checkers, ``check_ops_present.py`` (generic op-presence walk) and
``check_smoke_update_partial.py`` (Update body-shape walk), combined into one
script with a ``--ops`` / ``--partial`` mode flag (see BATCH1-ADDENDUM.md
"Batch 2 notes": "Flow `check_ops_present.py <Entity> <op-suffix>...` -> a
grader step asserting one classified node per op (curated OR generic form)").

Node classification is copied from ``check_df_integration_create_get.py``
(the passing pilot for this connector): a connector node is any
``bpmn:sendTask`` carrying ``Intsvc.ActivityExecution`` with connectorKey
``uipath-uipath-dataservice`` that mentions FlowCodeEvalEntity in a
``uipath:input`` collected at ANY depth under the activity (BATCH1-ADDENDUM.md
Lesson: agents sometimes nest body/query/path inputs inside ``uipath:context``).
Each node is then classified Create / Update / Get / Delete by curated
``objectName`` OR by the generic entity-CRUD form (``objectName`` == entity,
verb read off ``operation``/``method``) -- never by ``objectName`` alone.

Flow's ``check_ops_present.py`` read ``pathParameters.entityName`` out of
``inputs.detail``; BPMN has no fixed home for the entity name (path input,
query input, or a JSON body key), so this checker accepts any of those homes,
same as ``check_df_integration_create_get.py``.

Modes:
  --ops     Assert >=1 classified node per {create, update, get, delete} on
            FlowCodeEvalEntity. Mirrors Flow's ``check_ops_present.py``.
  --partial Assert the classified Update node's ``target="body"`` JSON has
            only the key ``score``, with value 9.0 -- OR an ``=`` expression,
            which passes any type check the same way Flow's grader waves
            through ``=js:...`` (see BATCH1-ADDENDUM.md "Grader rule for body
            fields"). Mirrors Flow's ``check_smoke_update_partial.py``.

Assertion map (Flow -> BPMN):
  F check_ops_present.py (required.issubset(seen))       op present per {create,update,get,delete} -> classify() buckets + `missing` check in check_ops()
  F check_smoke_update_partial.py (keys == {"score"})    Update body has only key 'score'            -> check_partial() keys check
  F check_smoke_update_partial.py (score in ("9.0","9")) Update body.score == 9.0                    -> check_partial() score check
  I                                                       locate/parse .bpmn                          -> parse_bpmn()
  T  curated|generic entity-CRUD node classification -> is_create_node()/is_update_node()/is_delete_node()/is_retrieval_node()
  T  entity name anywhere in node's inputs            -> mentions_entity()
  T  inputs at any depth                              -> node_inputs() (`.//uipath:input`)
  T  GETBYID/GET equivalence                          -> is_retrieval_node() List/GET + has_id_filter() branch
  T  expression strings (=...) passing type checks    -> check_partial() `score.startswith("=")` branch
  DROPPED  require_no_private_connector_values  (not in Flow grader)
  DROPPED  require_sequence_integrity            (not in Flow grader; `validate` criterion covers structure)
  DROPPED  require_di_for_visible_elements       (not in Flow grader; `validate` criterion covers structure)
  DROPPED  hard-fail on other-than-exactly-one target="body" input on Update node (Flow reads bodyParameters as a plain dict; no such limit)
"""

from __future__ import annotations

import argparse
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
)

ENTITY = "FlowCodeEvalEntity"
CONNECTOR_KEY = "uipath-uipath-dataservice"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"

CREATE_CURATED_NAMES = {"CreateEntityRecordCurated", "CreateEntityRecord_V3"}
GET_CURATED_NAMES = {"GetEntityRecordByIdCurated", "GetEntityRecord_V3"}
UPDATE_CURATED_NAMES = {"UpdateEntityRecordV2", "UpdateEntityRecord_V3"}
DELETE_CURATED_NAMES = {"DeleteEntityRecordCurated", "DeleteEntityRecord_V3"}

EXPECTED_SCORE = "9.0"

_CREATE_OP_RE = re.compile(r"^create$", re.IGNORECASE)
_RETRIEVE_OP_RE = re.compile(r"^retrieve$", re.IGNORECASE)
_LIST_OP_RE = re.compile(r"^list$", re.IGNORECASE)
_UPDATE_OP_RE = re.compile(r"^(update|replace)$", re.IGNORECASE)
_DELETE_OP_RE = re.compile(r"^delete$", re.IGNORECASE)


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


def body_inputs(task: ET.Element) -> list[ET.Element]:
    return [
        inp
        for inp in node_inputs(task)
        if inp.attrib.get("name") == "body" and inp.attrib.get("target") == "body"
    ]


def connector_nodes(root: ET.Element) -> list[ET.Element]:
    return [
        task
        for task in elements(root, "sendTask")
        if has_typed_uipath_extension(task, "activity", ACTIVITY_TYPE)
        and context_value(task, "connectorKey") == CONNECTOR_KEY
    ]


def has_id_filter(task: ET.Element) -> bool:
    """An `id` input at any target, or a `where`/`filter` input mentioning Id.

    Covers a Get-by-Id done through List/GET (the shape a real CI artifact
    used: `=js:"'Id' = '" + vars.X.Id + "'"`).
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


def is_update_node(task: ET.Element, object_name: str) -> bool:
    if object_name in UPDATE_CURATED_NAMES:
        return True
    if not is_generic_entity_object(object_name, ENTITY):
        return False
    operation = context_value(task, "operation").strip()
    method = context_value(task, "method").strip().upper()
    return bool(_UPDATE_OP_RE.match(operation)) or method in ("PUT", "PATCH")


def is_delete_node(task: ET.Element, object_name: str) -> bool:
    if object_name in DELETE_CURATED_NAMES:
        return True
    if not is_generic_entity_object(object_name, ENTITY):
        return False
    operation = context_value(task, "operation").strip()
    method = context_value(task, "method").strip().upper()
    return bool(_DELETE_OP_RE.match(operation)) or method == "DELETE"


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
        return has_id_filter(task)
    return False


def classify(root: ET.Element) -> dict[str, list[ET.Element]]:
    """Bucket every FlowCodeEvalEntity connector node by CRUD verb.

    Order matters: Create/Update/Delete are checked before the List/GET
    fallback inside `is_retrieval_node`, so a generic Update (method=PUT) or
    Delete (method=DELETE) node is never miscounted as a Get.
    """
    buckets: dict[str, list[ET.Element]] = {"create": [], "update": [], "get": [], "delete": []}
    for task in connector_nodes(root):
        if not mentions_entity(task, ENTITY):
            continue
        object_name = context_value(task, "objectName")
        if is_create_node(task, object_name):
            buckets["create"].append(task)
        elif is_update_node(task, object_name):
            buckets["update"].append(task)
        elif is_delete_node(task, object_name):
            buckets["delete"].append(task)
        elif is_retrieval_node(task, object_name):
            buckets["get"].append(task)
    return buckets


def check_ops() -> None:
    path, root = parse_bpmn()
    buckets = classify(root)
    missing = [op for op in ("create", "update", "get", "delete") if not buckets[op]]
    counts = {k: len(v) for k, v in buckets.items()}
    if missing:
        fail(f"{path}: no classified node for {missing} on {ENTITY} (found: {counts})")

    print(f"OK: {path} has Create/Update/Get/Delete on {ENTITY} ({counts})")


def check_partial() -> None:
    path, root = parse_bpmn()
    buckets = classify(root)
    updates = buckets["update"]
    if not updates:
        fail(f"{path}: no Update Entity Record node found on {ENTITY}")

    task = updates[0]
    # Flow reads bodyParameters as a plain dict (`{}` when absent) -- no Flow
    # equivalent polices a node's target="body" input count. Zero inputs is
    # an empty body (fails the key check below with a clear message); more
    # than one takes the last (the runtime does not merge them -- the last
    # one silently wins), rather than treating either shape as a hard error.
    bodies = body_inputs(task)
    if not bodies:
        body: dict = {}
    else:
        text = (bodies[-1].text or "").strip()
        if not text:
            body = {}
        else:
            try:
                body = json.loads(text)
            except json.JSONDecodeError as exc:
                fail(f"{path}: Update node's body is not valid JSON: {text[:200]!r} ({exc})")
            if not isinstance(body, dict):
                fail(f"{path}: Update node's body is not a JSON object: {text[:200]!r}")

    keys = set(body.keys())
    if keys != {"score"}:
        fail(f"{path}: Update body has {sorted(keys)}, expected only 'score'")

    score = body["score"]
    if isinstance(score, str) and score.strip().startswith("="):
        print(f"OK: {path} update body = {{'score': {score!r}}} (expression)")
        return
    if str(score) not in (EXPECTED_SCORE, "9"):
        fail(f"{path}: update body.score={score!r}, expected {EXPECTED_SCORE}")
    print(f"OK: {path} update body = {{'score': {score}}}")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--ops", action="store_true", help="assert Create/Update/Get/Delete nodes all present"
    )
    mode.add_argument(
        "--partial", action="store_true", help="assert Update body carries only 'score'"
    )
    args = parser.parse_args()
    if not args.ops and not args.partial:
        fail("no mode flag given, expected --ops or --partial")
    if args.ops:
        check_ops()
    else:
        check_partial()


if __name__ == "__main__":
    main()
