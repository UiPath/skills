#!/usr/bin/env python3
"""DF smoke_create_all_types (BPMN): Data Service Create Entity Record node
covers all 8 supported field types with correct JSON literal shapes.

Ported from Flow `connector_features/datafabric_connector/smoke_create_all_types.yaml`'s
``check_smoke_create_all_types.py``: same scenario (a single Create node on
FlowCodeEvalEntity binding all 8 field types), translated from a JSON
`bodyParameters` walk to an XML walk over the registry-driven
``Intsvc.ActivityExecution`` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3-4). Flow's task
names no project, so this grader locates the BPMN file with no name hint
(`parse_bpmn()` prefers the one with `project.uiproj` beside it).

Assertion map (Flow → BPMN):
  F check_smoke_create_all_types.py:75      node type suffix `.create-entity-record`     → T: curated|generic entity-CRUD objectName classification (find_create_tasks)
  F check_smoke_create_all_types.py:80-83   bodyParameters covers all 8 fields            → target="body" JSON covers all 8 fields
  F check_smoke_create_all_types.py:84-86   pathParameters.entityName == ENTITY           → T: entity name anywhere in node's inputs/objectName/path
  F check_smoke_create_all_types.py:90-98   per-field type check, `=js:` expression skip  → T: expression strings (=…) passing type checks
  F check_smoke_create_all_types.py:102-103 fail if no create-entity-record node found    → fail if find_create_tasks() empty
  I                locate/parse .bpmn (file exists, well-formed XML, no name hint)         → parse_bpmn()
  I                parse target="body" CDATA as JSON (Flow read bodyParameters)            → json.loads(body_inputs[0].text)
  T                curated|generic entity-CRUD node classification                        → find_create_tasks() / _is_generic_create_form()
  T                inputs at any depth                                                    → node_inputs() walks `.//uipath:input`
  T                entity name anywhere in node's inputs/objectName/path                  → entity_values check
  T                expression strings (=…) passing type checks                            → _is_expression()
  DROPPED          "exactly one Create node" hard failure   (Flow returns on the first match in node order; no uniqueness assertion)
  DROPPED          "exactly one target=body input" hard failure   (Flow read bodyParameters structurally; parsing it is I, enforcing single-body is not)
  DROPPED          require_no_private_connector_values      (not in Flow)
  DROPPED          require_sequence_integrity               (not in Flow; `bpmn validate` criterion covers structure)
  DROPPED          require_di_for_visible_elements           (not in Flow; `bpmn validate` criterion covers structure)

Where Flow's grader read `node.inputs.detail.bodyParameters` as a JSON object
already embedded in the .flow file, this grader reads a
`<uipath:input target="body">` CDATA payload on the sendTask and
`json.loads`s it -- the BPMN registry shell puts the whole request body in one
JSON blob instead of Flow's structured `bodyParameters` map. Flow accepted a
`=js:`-prefixed string as an expression binding for any field (grading wiring,
not literal choice); the BPMN skill's expression prefix is a bare `=`
(`=vars.X`, `=js:...`), so any string starting with `=` is accepted here,
which is a superset that still covers `=js:`.

Entity-name check: the skill does not pin where `entityName`/`path` lands
(context `path`, a sibling `target="path"` input, or a `target="query"`
input), so this grader accepts the entity string appearing as the value of
ANY `uipath:input` on the node, or inside its context `path` field -- same
looseness the batch addendum specifies for the Data Fabric ports.

Two connector-node shapes are accepted for step 2, both observed from real
skill output (CI run skill-bpmn-datafabric-smoke-create-all-types, 2026-09):

  * Curated/preview form: objectName is literally
    CreateEntityRecordCurated or CreateEntityRecord_V3.
  * Generic entity-CRUD form: the skill's registry discoveryNotes steer some
    agents to the entity-typed generic verb instead -- objectName equals the
    entity name itself (FlowCodeEvalEntity, case-insensitive) and either
    operation is "Create" (case-insensitive) or method is POST. This is the
    real shape CI's passing run produced: objectName="FlowCodeEvalEntity",
    operation="Create", method="POST", path="/FlowCodeEvalEntity".

`uipath:input` elements are collected at ANY depth under the sendTask (not
just directly under `uipath:context`), since some agents nest the body/query
inputs inside `uipath:context` instead of as siblings of it.

Checks performed:
  1. BPMN file exists and is well-formed XML.
  2. At least one bpmn:sendTask carries Intsvc.ActivityExecution with
     connectorKey uipath-uipath-dataservice and an objectName matching either
     accepted Create Entity Record shape (see above); the first match is
     graded.
  3. That node targets entity FlowCodeEvalEntity.
  4. That node has a target="body" input whose CDATA is valid JSON and
     covers all 8 fields with Flow's literal-shape checks.
"""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import NS, elements, fail, parse_bpmn  # noqa: E402

CONNECTOR_KEY = "uipath-uipath-dataservice"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
ENTITY = "FlowCodeEvalEntity"
OBJECT_NAME_RE = re.compile(r"^(CreateEntityRecordCurated|CreateEntityRecord_V3)$")
OPERATION_CREATE_RE = re.compile(r"^create$", re.IGNORECASE)

UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?")


def _is_expression(v):
    # BPMN expression prefix is bare `=` (`=vars.X`, `=js:...`); Flow's
    # grader accepted only `=js:` -- this is a superset that still covers it.
    return isinstance(v, str) and v.startswith("=")


def _check_str(v):
    return isinstance(v, str)


def _check_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _check_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _check_bool(v):
    return isinstance(v, bool)


def _check_date(v):
    return isinstance(v, str) and bool(DATE_RE.match(v))


def _check_datetime(v):
    return isinstance(v, str) and bool(DATETIME_RE.match(v))


def _check_uuid(v):
    return isinstance(v, str) and bool(UUID_RE.match(v))


EXPECTED = {
    "title":        ("STRING",         _check_str),
    "description":  ("MULTILINE_TEXT", _check_str),
    "score":        ("DECIMAL",        _check_number),
    "viewCount":    ("INTEGER",        _check_int),
    "active":       ("BOOLEAN",        _check_bool),
    "releaseDate":  ("DATE",           _check_date),
    "lastUpdated":  ("DATETIME",       _check_datetime),
    "externalId":   ("UUID",           _check_uuid),
}


def has_type(el: ET.Element, token: str) -> bool:
    return token in ET.tostring(el, encoding="unicode")


def node_inputs(task: ET.Element) -> list[ET.Element]:
    # `.//` walks every descendant of the sendTask, so this already covers
    # both layouts seen in practice: context/body inputs as direct children
    # of uipath:activity, or body/query inputs nested inside uipath:context.
    return task.findall(".//uipath:input", NS)


def context_value(task: ET.Element, name: str) -> str:
    for inp in node_inputs(task):
        if inp.attrib.get("name") == name:
            return inp.attrib.get("value") or (inp.text or "")
    return ""


def all_node_values(task: ET.Element) -> list[str]:
    values: list[str] = []
    for inp in node_inputs(task):
        v = inp.attrib.get("value")
        if v:
            values.append(v)
        if inp.text and inp.text.strip():
            values.append(inp.text.strip())
    return values


def _is_generic_create_form(object_name: str, operation: str, method: str) -> bool:
    """Entity-typed generic verb: objectName IS the entity name, and either
    operation says Create or method is POST (skill discoveryNotes steer some
    agents to this form instead of the curated/preview verb)."""
    if object_name.strip().lower() != ENTITY.lower():
        return False
    return bool(OPERATION_CREATE_RE.match(operation.strip())) or method.strip().upper() == "POST"


def find_create_tasks(root: ET.Element) -> list[ET.Element]:
    found = []
    for task in elements(root, "sendTask"):
        if not has_type(task, ACTIVITY_TYPE):
            continue
        if context_value(task, "connectorKey") != CONNECTOR_KEY:
            continue
        object_name = context_value(task, "objectName")
        operation = context_value(task, "operation")
        method = context_value(task, "method")
        if OBJECT_NAME_RE.match(object_name) or _is_generic_create_form(object_name, operation, method):
            found.append(task)
    return found


def main() -> None:
    path, root = parse_bpmn()

    create_tasks = find_create_tasks(root)
    if not create_tasks:
        fail(
            f"no bpmn:sendTask carrying {ACTIVITY_TYPE} for connector key "
            f"{CONNECTOR_KEY!r} matching Create Entity Record -- neither the "
            f"curated/preview objectName (CreateEntityRecordCurated|"
            f"CreateEntityRecord_V3) nor the generic entity-CRUD form "
            f"(objectName={ENTITY!r} with operation=Create or method=POST)"
        )
    task = create_tasks[0]
    print(f"OK: {CONNECTOR_KEY} Create Entity Record sendTask present")

    entity_values = all_node_values(task) + [context_value(task, "path")]
    if not any(v and ENTITY in v for v in entity_values):
        fail(
            f"entity name {ENTITY!r} not found in any input value or context "
            f"path of the Create node (checked: {[v for v in entity_values if v]})"
        )
    print(f"OK: node targets entity {ENTITY!r}")

    body_inputs = [inp for inp in node_inputs(task) if inp.attrib.get("target") == "body"]
    if not body_inputs:
        fail('no target="body" input found on the Create node')
    raw = body_inputs[0].text or ""
    try:
        body = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f'target="body" input is not valid JSON: {exc}\n  raw={raw!r}')

    if not isinstance(body, dict):
        fail(f'target="body" JSON must be an object, got {type(body).__name__}')

    missing = set(EXPECTED) - set(body.keys())
    if missing:
        fail(f"Create body JSON missing fields: {sorted(missing)}")

    type_errors = []
    for field, (label, check) in EXPECTED.items():
        v = body[field]
        if _is_expression(v):
            continue
        if not check(v):
            type_errors.append((field, label, type(v).__name__, v))
    if type_errors:
        lines = "\n".join(f"  {f} ({lbl}): got {got}={val!r}" for f, lbl, got, val in type_errors)
        fail(f"type mismatches in Create body:\n{lines}")

    print(f"OK: {path} — Create body covers all 8 fields on {ENTITY} with matching JSON-literal shapes")


if __name__ == "__main__":
    main()
