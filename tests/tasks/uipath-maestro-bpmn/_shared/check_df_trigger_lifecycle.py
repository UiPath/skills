#!/usr/bin/env python3
"""DataFabricTriggerRegression (BPMN): connector-trigger lifecycle coverage.

Ported from Flow
`connector_features/datafabric_connector/trigger_lifecycle.yaml`'s
``check_trigger_lifecycle.py``: same two-branch scenario (a Record Created
trigger on ContractRegistry with a dueDate filter feeding a filtered/limited
Query, and a Record Updated trigger on FileUploadVerify_20260618 feeding a
Get-by-Id and a Delete both wired to the trigger's own output), translated
from a JSON node/``inputs.detail`` walk to an XML walk over the
registry-driven ``Intsvc.EventTrigger`` startEvent shell and the
``Intsvc.ActivityExecution`` connector sendTask shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3-4 on connector
enrichment and bindings). Conventions (``context_value``/``all_node_values``/
entity-anywhere/curated-or-generic objectName) match this batch's sibling
Data Fabric ports (``check_df_contractregistry_crud_filters.py`` etc.) for
consistency.

Re-homing decisions vs the Flow grader:
  - Flow's two separate ``.flow`` files (one Flow project per trigger) become
    two ``bpmn:startEvent`` entries in ONE ``bpmn:process``. BPMN has no
    multi-file "solution" concept the way Flow does.
  - Flow's ``node.type`` suffix matching (``.record-created`` /
    ``.record-updated`` / ``.query-entity-records`` / ``.get-entity-record-
    by-id`` / ``.delete-entity-record``) becomes: for the two trigger starts,
    an ``Intsvc.EventTrigger`` startEvent (with ``bpmn:messageEventDefinition``)
    whose context ``operation`` field contains "creat"/"updat" (a live
    Data Service connection has no local ``describe`` access here to pin the
    exact operation string the registry enrichment writes -- see
    BATCH1-ADDENDUM.md -- so operation is matched by substring, tolerant of
    any casing/spelling the enrichment produces); for the downstream
    activities, the same curated-or-generic ``objectName`` classification as
    the batch's CRUD checkers (``QueryEntityRecordsCurated|
    QueryEntityRecords_V3``, ``GetEntityRecordByIdCurated|
    GetEntityRecord_V3``, ``DeleteEntityRecordCurated|
    DeleteEntityRecord_V3``, or the generic entity-object form with a
    matching ``operation``/``method``).
  - Flow's ``entityName``/``objectName`` equality becomes "the entity string
    appears as the value of ANY ``uipath:input`` of that node/trigger (any
    target) or inside its context ``path`` field" -- the registry does not
    pin where ``entityName`` lands (BATCH1-ADDENDUM.md).
  - Flow's trigger-side ``filterExpression``/``filter``/``configuration``
    blob scan for "duedate" + "2026-08-04" + "<" becomes the same blob scan
    over every ``uipath:input`` reachable at any depth under the trigger's
    ``uipath:event`` payload (the registry's ``filter`` context field is an
    object; its structured or literal-expression shape is not pinned here
    either, so both forms are accepted).
  - Flow's node-id binding between the Record Updated trigger and the Get/
    Delete nodes (``trigger_ids`` matched against ``queryParameters.recordId``)
    becomes: the Get node's inputs reference the trigger's own
    ``<uipath:output var=...>`` id as ``vars.<id>``, and the Delete node's
    inputs reference either that same trigger output var OR the Get node's
    own output var -- each traced transitively (<=3 hops) through any
    ``<uipath:output var=... source=...>`` in the document, in case the agent
    routes the value through an intermediate ``BPMN.Variables`` copy task.

Checks performed:
  1. BPMN file exists and is well-formed XML.
  2. A ContractRegistry Record Created trigger start event with a
     dueDate < 2026-08-04 filter.
  3. A ContractRegistry Query Entity Records sendTask, limited to 100,
     carrying the same dueDate filter.
  4. A FileUploadVerify_20260618 Record Updated trigger start event.
  5. A FileUploadVerify_20260618 Get Entity Record by ID sendTask referencing
     the Updated trigger's own output variable.
  6. A FileUploadVerify_20260618 Delete Entity Record sendTask referencing
     the trigger or Get output variable.

Assertion map (Flow -> BPMN):
  F check_trigger_lifecycle.py:59-65   Record Created trigger for CONTRACT_ENTITY + dueDate filter -> is_trigger_of(CREATED_RE) + has_due_filter()
  F check_trigger_lifecycle.py:67-80   Query on CONTRACT_ENTITY, dueDate filter, limit==100        -> is_kind(query)+entity_ok() + has_due_filter() + has_standalone_token(query, "100")
  F check_trigger_lifecycle.py:82-85   Record Updated trigger for FILE_ENTITY                       -> is_trigger_of(UPDATED_RE)
  F check_trigger_lifecycle.py:87-96   Get/Delete on FILE_ENTITY exist                               -> is_kind(get)/is_kind(delete) + entity_ok()
  F check_trigger_lifecycle.py:92-96   Get recordId bound to trigger output (trigger_ids substring) -> references_var(get value, trigger_out_var)
  F check_trigger_lifecycle.py:97-99   Delete recordId bound to trigger/Get output                   -> references_var(delete value, trigger_out_var or get_out_var)
  I                                     locate/parse .bpmn                                            -> parse_bpmn()
  T                                     curated|generic objectName classification                     -> is_kind()
  T                                     entity name anywhere in node inputs/objectName/path            -> entity_ok()
  T                                     vars.<VarId> substring reference, transitive through BPMN.Variables copies, in place of Flow node-id reference -> references_var() / var_sources_map()
  DROPPED  require_no_private_connector_values  (not in Flow; `validate` criterion already covers structure)
  DROPPED  require_sequence_integrity            (not in Flow; `validate` criterion already covers structure)
  DROPPED  require_di_for_visible_elements       (not in Flow; `validate` criterion already covers structure)
  DROPPED  "no non-trigger (manual) start event coexists" / "exactly 2 trigger starts"  (Flow never asserted this; Flow's two flows just each contain their own trigger)
  DROPPED  require_process_entry (no inbound flow / has outgoing flow) for each trigger start  (not in Flow)
  DROPPED  Created->Query / Updated->Get / Get->Delete graph.reaches reachability  (Flow's grader has no edge/order check at all -- it only matches recordId substrings, a data reference, not sequence order)
  DROPPED  connection-binding checks (binding_ids/require_connection_binding, `connectionId`/`connection` field resolving to a declared resource="Connection" binding)  (Flow graders never checked connections)
"""

from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    has_typed_uipath_extension,
    parse_bpmn,
)

BPMN_NS = NS["bpmn"]
CONNECTOR_KEY = "uipath-uipath-dataservice"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
TRIGGER_TYPE = "Intsvc.EventTrigger"

CONTRACT_ENTITY = "ContractRegistry"
FILE_ENTITY = "FileUploadVerify_20260618"

QUERY_OBJECTS = {"QueryEntityRecordsCurated", "QueryEntityRecords_V3"}
GET_OBJECTS = {"GetEntityRecordByIdCurated", "GetEntityRecord_V3"}
DELETE_OBJECTS = {"DeleteEntityRecordCurated", "DeleteEntityRecord_V3"}

# The Data Service connector also has a GENERIC entity-CRUD form: objectName
# is the entity name itself, and the operation is distinguished by the
# context `operation`/`method` fields instead of a curated per-op objectName.
GENERIC_OP_PATTERNS = {
    "query": re.compile(r"^(list|get)$", re.IGNORECASE),
    "get": re.compile(r"^(retrieve|getbyid)$", re.IGNORECASE),
    "delete": re.compile(r"^(delete)$", re.IGNORECASE),
}

CREATED_RE = re.compile(r"creat", re.IGNORECASE)
UPDATED_RE = re.compile(r"updat", re.IGNORECASE)
LESS_THAN_RE = re.compile(r"<|lessthan|\blt\b", re.IGNORECASE)


def node_inputs(el: ET.Element) -> list[ET.Element]:
    return el.findall(".//uipath:input", NS)


def context_value(el: ET.Element, name: str) -> str:
    for inp in node_inputs(el):
        if inp.attrib.get("name") == name:
            return inp.attrib.get("value") or (inp.text or "")
    return ""


def all_node_values(el: ET.Element) -> list[str]:
    values: list[str] = []
    for inp in node_inputs(el):
        v = inp.attrib.get("value")
        if v:
            values.append(v)
        if inp.text and inp.text.strip():
            values.append(inp.text.strip())
    return values


def node_blob(el: ET.Element) -> str:
    return " ".join(all_node_values(el)).lower()


def output_vars(el: ET.Element) -> list[str]:
    return [o.attrib["var"] for o in el.findall(".//uipath:output", NS) if o.attrib.get("var")]


def entity_ok(el: ET.Element, entity: str) -> bool:
    if context_value(el, "objectName").strip().lower() == entity.lower():
        return True
    values = all_node_values(el) + [context_value(el, "path")]
    return any(v and entity.lower() in v.lower() for v in values)


def has_standalone_token(el: ET.Element, token: str) -> bool:
    pattern = re.compile(rf"(?<![\w.]){re.escape(token)}(?![\w.])")
    return any(pattern.search(v) for v in all_node_values(el))


def has_due_filter(el: ET.Element) -> bool:
    blob = node_blob(el)
    return "duedate" in blob and "2026-08-04" in blob and bool(LESS_THAN_RE.search(blob))


def is_kind(task: ET.Element, entity: str, curated_objects: set[str], kind: str) -> bool:
    obj = context_value(task, "objectName")
    if obj in curated_objects:
        return True
    if obj.strip().lower() != entity.lower():
        return False
    op = context_value(task, "operation")
    method = context_value(task, "method")
    pattern = GENERIC_OP_PATTERNS[kind]
    return bool(pattern.match(op) or pattern.match(method))


def is_trigger_of(start: ET.Element, entity: str, op_re: re.Pattern) -> bool:
    if not entity_ok(start, entity):
        return False
    op = context_value(start, "operation")
    if op:
        return bool(op_re.search(op))
    return bool(op_re.search(node_blob(start)))


def sendtask_nodes(root: ET.Element) -> list[ET.Element]:
    return [
        task
        for task in elements(root, "sendTask")
        if has_typed_uipath_extension(task, "activity", ACTIVITY_TYPE)
        and context_value(task, "connectorKey") == CONNECTOR_KEY
    ]


def trigger_start_events(root: ET.Element) -> list[ET.Element]:
    return [
        s
        for s in elements(root, "startEvent")
        if has_typed_uipath_extension(s, "event", TRIGGER_TYPE)
        and s.find(f"{{{BPMN_NS}}}messageEventDefinition") is not None
    ]


def var_sources_map(root: ET.Element) -> dict[str, str]:
    m: dict[str, str] = {}
    for out in root.findall(".//uipath:output", NS):
        var = out.attrib.get("var")
        source = out.attrib.get("source")
        if var and source and var not in m:
            m[var] = source
    return m


def references_var(value: str, target_var: str, var_sources: dict[str, str], hops: int = 3) -> bool:
    for ref in re.findall(r"vars\.([A-Za-z0-9_]+)", value):
        if ref == target_var:
            return True
        if hops > 0:
            source = var_sources.get(ref, "")
            if source and references_var(source, target_var, var_sources, hops - 1):
                return True
    return False


def main() -> None:
    path, root = parse_bpmn("DataFabricTriggerRegression")

    trig_starts = trigger_start_events(root)
    if not trig_starts:
        fail("no connector-trigger start event found")

    created_candidates = [s for s in trig_starts if is_trigger_of(s, CONTRACT_ENTITY, CREATED_RE)]
    if not created_candidates:
        fail(f"no Record Created trigger start event for {CONTRACT_ENTITY}")
    created = created_candidates[0]

    updated_candidates = [s for s in trig_starts if is_trigger_of(s, FILE_ENTITY, UPDATED_RE)]
    if not updated_candidates:
        fail(f"no Record Updated trigger start event for {FILE_ENTITY}")
    updated = updated_candidates[0]

    for start, label in ((created, "Record Created trigger"), (updated, "Record Updated trigger")):
        key = context_value(start, "connectorKey")
        if key != CONNECTOR_KEY:
            fail(f"{label} connectorKey is not {CONNECTOR_KEY!r} (found {key!r})")

    if not has_due_filter(created):
        fail(f"{CONTRACT_ENTITY} Record Created trigger lacks dueDate < 2026-08-04 filter")
    print("OK: ContractRegistry Record Created trigger carries the dueDate filter")

    sendtasks = sendtask_nodes(root)
    queries = [
        t for t in sendtasks if is_kind(t, CONTRACT_ENTITY, QUERY_OBJECTS, "query") and entity_ok(t, CONTRACT_ENTITY)
    ]
    if not queries:
        fail(f"no {CONTRACT_ENTITY} Query Entity Records sendTask found")
    query = queries[0]
    if not has_standalone_token(query, "100"):
        fail("Query Entity Records node is not limited to 100 records")
    if not has_due_filter(query):
        fail(f"Query Entity Records node lacks dueDate < 2026-08-04 filter")
    print("OK: ContractRegistry Query Entity Records node is filtered and limited to 100")

    gets = [t for t in sendtasks if is_kind(t, FILE_ENTITY, GET_OBJECTS, "get") and entity_ok(t, FILE_ENTITY)]
    deletes = [
        t for t in sendtasks if is_kind(t, FILE_ENTITY, DELETE_OBJECTS, "delete") and entity_ok(t, FILE_ENTITY)
    ]
    if not gets:
        fail(f"no {FILE_ENTITY} Get Entity Record by ID sendTask found")
    if not deletes:
        fail(f"no {FILE_ENTITY} Delete Entity Record sendTask found")
    get = gets[0]
    delete = deletes[0]

    trigger_out_vars = output_vars(updated)
    if not trigger_out_vars:
        fail("Record Updated trigger has no <uipath:output var=...> for downstream nodes to reference")
    var_sources = var_sources_map(root)

    get_values = all_node_values(get)
    if not any(references_var(v, tv, var_sources) for v in get_values for tv in trigger_out_vars):
        fail(
            f"Get Entity Record node does not reference the Record Updated trigger's output "
            f"variable (vars.{{{', '.join(trigger_out_vars)}}}); found values: {get_values}"
        )
    print("OK: Get Entity Record node is wired to the Record Updated trigger output")

    get_out_vars = output_vars(get)
    candidates = trigger_out_vars + get_out_vars
    delete_values = all_node_values(delete)
    if not any(references_var(v, c, var_sources) for v in delete_values for c in candidates):
        fail(
            "Delete Entity Record node does not reference the trigger or Get output variable "
            f"(vars.{{{', '.join(candidates)}}}); found values: {delete_values}"
        )
    print("OK: Delete Entity Record node is wired to the trigger/Get output")

    print(
        f"OK: {path} — ContractRegistry Record Created+Query and "
        f"{FILE_ENTITY} Record Updated+Get+Delete are fully bound"
    )


if __name__ == "__main__":
    main()
