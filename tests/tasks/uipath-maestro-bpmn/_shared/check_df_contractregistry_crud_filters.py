#!/usr/bin/env python3
"""ContractRegistryCrudFilters (BPMN): Data Service CRUD/filter/variable wiring.

Ported from Flow
`connector_features/datafabric_connector/contractregistry_crud_filters.yaml`'s
``check_contractregistry_crud_filters.py``: same ContractRegistry scenario
(create all six fields, two filtered/limited queries, a variable-bound title
update, a Get-by-Id wired to the update's own output, and output mapping),
translated from a JSON node/``inputs.detail`` walk to an XML walk over the
registry-driven ``Intsvc.ActivityExecution`` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3-4 and
skills/uipath-maestro-bpmn/references/structural-bpmn.md on public outputs).
Conventions (``context_value``/``all_node_values``/``bpmn_check.body_object``
request body/entity-anywhere) match this batch's sibling ports
(``check_df_integration_create_get.py``, ``check_df_smoke_create_all_types.py``)
for consistency.

Re-homing decisions vs the Flow grader:
  - ``node.type`` suffix matching (``.create-entity-record`` etc.) becomes an
    ``Intsvc.ActivityExecution`` sendTask matched on ``objectName`` against
    the Data Service catalog: both the curated and ``_V3`` spelling are
    accepted for every operation (``CreateEntityRecordCurated|
    CreateEntityRecord_V3``, ``QueryEntityRecordsCurated|
    QueryEntityRecords_V3``, ``UpdateEntityRecordV2|UpdateEntityRecord_V3``,
    ``GetEntityRecordByIdCurated|GetEntityRecord_V3`` -- from
    ``dataservice-activities.json`` in _porting/BATCH1-ADDENDUM.md), since Flow's node
    types did not distinguish them. The connector also exposes a GENERIC
    entity-CRUD form (``objectName`` is the entity name itself, e.g.
    "ContractRegistry", on every node; the operation is read off the context
    ``operation``/``method`` fields instead) -- a real CI-graded solution used
    this form, so both are accepted (``is_kind``/``GENERIC_OP_PATTERNS``).
  - Flow's ``pathParameters.entityName == "ContractRegistry"`` (with a
    variable-global-default carve-out) becomes: the literal string appears as
    the value of ANY ``uipath:input`` of that node (path/query/body) or
    inside its context ``path`` field -- the registry does not pin where
    ``entityName`` lands, and no BPMN ``<uipath:variables>`` declaration
    documents a literal-default attribute to trace a variable reference back
    to (only ``<uipath:binding>`` carries `default`, per registry-workflow.md
    §4), so the variable-indirection branch is dropped rather than guessed;
    this also matches how the batch's other Data Fabric checkers resolved the
    same rule.
  - Flow's ``bodyParameters`` dict becomes the dict
    ``bpmn_check.body_object()`` decodes from the node's ONE
    ``target="body"`` CDATA JSON object (registry-workflow.md §3); several
    ``target="body"`` inputs fail, because the runtime does not merge them.
  - Flow's ``queryParameters.queryExpression`` / ``.limit`` have no fixed
    field name in the Data Service registry contract available here (no
    local Data Service connection to ``describe`` request fields against --
    _porting/BATCH1-ADDENDUM.md), so filter and limit checks scan every attribute
    value / text blob reachable from a query node's inputs instead of one
    named field. The limit check requires the standalone token ``100``
    (digit-boundary matched) rather than a bare substring, so a coincidental
    "100" inside a larger number never counts.
  - Flow's loose ``"$vars." in title_value or "random"/"title" in
    title_value`` check for the Update node's contractTitle becomes a real
    variable-binding assertion: the value must be a pure ``=vars.<id>``
    expression where ``<id>`` is declared in ``<uipath:variables>``. BPMN's
    own variable contract makes the intended check (title held in a declared
    variable, not a literal) exactly expressible, so Flow's keyword-matching
    proxy is not carried forward as-is.
  - Flow's Get-by-Id ``record_id`` keyword heuristic (``"update"``/``"record"``
    in the value) becomes an exact reference to the Update node's own
    ``<uipath:output var=...>`` id (a ``vars.<VarId>`` reference in place of
    Flow's node-id-shaped reference) -- the BPMN output/variable contract
    makes the real producer identifiable, where Flow could only guess from a
    keyword. No ordering/reachability check is added: Flow's assertion is a
    data-reference check, not a sequence assertion, so this port does not
    require Update to precede Get on a sequence-flow path either.
  - Flow's "any End node has any ``outputs``" check becomes: a completion
    ``bpmn:endEvent`` carries a ``BPMN.Variables`` mapping whose
    ``<uipath:output>`` ``source`` expression references at least one of the
    graded CRUD nodes' own output variables -- as loose as Flow's (not
    requiring all four to be mapped), but tied to the nodes under test
    instead of any arbitrary output. A real CI-graded solution routes each
    CRUD response through its own copy step first (a ``BPMN.Variables``
    mapping task reading ``=vars.Var_CreateResponse`` into e.g.
    ``Var_CreatedRecord``, which the end event then maps out) instead of the
    end event referencing the CRUD node's output var directly, so the check
    follows the variable-write chain (any ``<uipath:output var=... source=...>``
    in the document) up to 3 hops looking for a CRUD output var at the root,
    rather than requiring a single direct hop.
  - Added (not present in Flow's grader, but Flow does check for a manual
    trigger node -- ``core.trigger.manual`` -- so this is a direct
    translation, not a new assertion): a manual root start (a
    ``bpmn:startEvent`` with no event definition and no ``uipath:event``
    extension -- structural-bpmn.md's own manual-start derivation rule).
  - NOT ported: a per-node connection-binding requirement
    (``=bindings.<id>`` resolving to a declared ``resource="Connection"``
    binding) and a hard failure when a node carries no ``target="body"``
    input. Neither has a Flow counterpart -- Flow's grader has no concept of
    connections, and Flow reads ``bodyParameters`` as a plain dict (empty
    when absent). ``body_object`` mirrors that: zero ``target="body"``
    inputs yields an empty body (fields report as missing, same failure
    Flow would produce). More than one fails, because the runtime does not
    merge them.
  - NOT ported: a non-null-value check on the Create body's six fields.
    Flow only asserts the keys are present (``FIELDS - set(body)``); it
    never inspects the values, so requiring non-null values is stricter
    than Flow and is dropped.

Checks performed:
  1. BPMN file exists and is well-formed XML.
  2. A root-level manual start event (no event definition / uipath:event).
  3. One ContractRegistry Create Entity Record sendTask whose decoded
     ``target="body"`` request body holds all six fields.
  4. >=2 ContractRegistry Query Entity Records sendTasks, each carrying a
     standalone ``100`` limit token; across them, a dueDate < 2026-08-04
     filter and a contractTitle-is-null filter.
  5. One ContractRegistry Update Entity Record sendTask whose contractTitle
     is a ``=vars.<id>`` reference to a declared process variable.
  6. One ContractRegistry Get Entity Record by ID sendTask referencing the
     Update node's own output variable.
  7. A completion end event maps out at least one of the CRUD nodes' output
     variables.

Assertion map (Flow -> BPMN):
  F check_contractregistry_crud_filters.py:50-53  manual trigger node present        -> has_manual_root_start()
  F check_contractregistry_crud_filters.py:76-80   Create body has all six fields     -> FIELDS - set(create_body)
  F check_contractregistry_crud_filters.py:81-83   >=2 Query nodes                    -> `len(queries) < 2` check
  F check_contractregistry_crud_filters.py:86-88   dueDate < 2026-08-04 filter        -> matches_due_date_filter()
  F check_contractregistry_crud_filters.py:89-91   contractTitle-null filter          -> matches_null_title_filter()
  F check_contractregistry_crud_filters.py:92-96   each Query limited to 100          -> has_standalone_token(q, "100")
  F check_contractregistry_crud_filters.py:98-104  Update sets contractTitle          -> "contractTitle" not in update_body
  F check_contractregistry_crud_filters.py:105-108 contractTitle is variable-bound    -> UPDATE_TITLE_VAR_RE + variable_declared()
  F check_contractregistry_crud_filters.py:113-116 Get-by-Id wired to Update output   -> wired_var lookup against update_out_vars
  F check_contractregistry_crud_filters.py:118-120 an End node has mapped outputs     -> derives_from_crud() end-event walk
  I                                                locate/parse .bpmn                 -> parse_bpmn()
  T  curated|generic entity-CRUD node classification -> is_kind()
  T  entity name anywhere in inputs/objectName/path   -> entity_ok()
  T  inputs at any depth                              -> all_node_values()/body_object()
  T  body must be one target="body" JSON object → bpmn_check.body_object()  (several inputs fail: the runtime does not merge them)
  T  expression strings (=...) passing type checks    -> UPDATE_TITLE_VAR_RE match on `=vars.<id>`
  T  vars.<VarId> references in place of Flow node-id refs -> Get-by-Id wired_var check
  T  transitive variable derivation through BPMN.Variables copy tasks -> derives_from_crud()
  DROPPED  require_no_private_connector_values  (not in Flow grader)
  DROPPED  require_sequence_integrity            (not in Flow grader; `validate` criterion covers structure)
  DROPPED  require_di_for_visible_elements       (not in Flow grader; `validate` criterion covers structure)
  DROPPED  connection-binding requirement (=bindings.<id>)  (Flow grader has no connection concept)
  DROPPED  hard-fail on zero target="body" inputs (Flow reads bodyParameters as a plain dict; absent is empty)
  DROPPED  Update-precedes-Get `graph.reaches` ordering check (Flow's record_id check is a data reference, not an order assertion)
  DROPPED  non-null-value check on Create body fields (Flow only checks key presence, not values -- stricter than F)
"""

from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    NS,
    BodyShapeError,
    all_node_values,
    body_object,
    context_value,
    elements,
    fail,
    has_typed_uipath_extension,
    parse_bpmn,
)

CONNECTOR_KEY = "uipath-uipath-dataservice"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
ENTITY = "ContractRegistry"
FIELDS = {"contractTitle", "status", "priority", "dueDate", "value", "isUrgent"}

CREATE_OBJECTS = {"CreateEntityRecordCurated", "CreateEntityRecord_V3"}
QUERY_OBJECTS = {"QueryEntityRecordsCurated", "QueryEntityRecords_V3"}
UPDATE_OBJECTS = {"UpdateEntityRecordV2", "UpdateEntityRecord_V3"}
GET_OBJECTS = {"GetEntityRecordByIdCurated", "GetEntityRecord_V3"}

# The Data Service connector also has a GENERIC entity-CRUD form: objectName
# is the entity name itself ("ContractRegistry") on every node, and the
# operation is distinguished by the context `operation`/`method` fields
# instead of a curated per-op objectName. Accept either form -- the skill
# does not mandate the curated one. Checked against `operation` OR `method`
# (either field matching is enough).
GENERIC_OP_PATTERNS = {
    "create": re.compile(r"^(create|post)$", re.IGNORECASE),
    "query": re.compile(r"^(list|get)$", re.IGNORECASE),
    "update": re.compile(r"^(update|replace|put|patch)$", re.IGNORECASE),
    "get": re.compile(r"^(retrieve|getbyid)$", re.IGNORECASE),
}

# An expression (leading "=") that reads a declared variable: `=vars.X` or
# `=js:... vars.X ...`. A literal string title is the regression this catches.
UPDATE_TITLE_VAR_RE = re.compile(r"\bvars\.([A-Za-z0-9_]+)")


def output_vars(task: ET.Element) -> list[str]:
    return [out.attrib["var"] for out in task.findall(".//uipath:output", NS) if out.attrib.get("var")]


def entity_ok(task: ET.Element) -> bool:
    if context_value(task, "objectName").strip().lower() == ENTITY.lower():
        return True
    values = all_node_values(task) + [context_value(task, "path")]
    return any(v and ENTITY in v for v in values)


def is_kind(task: ET.Element, curated_objects: set[str], kind: str) -> bool:
    obj = context_value(task, "objectName")
    if obj in curated_objects:
        return True
    if obj.strip().lower() != ENTITY.lower():
        return False
    op = context_value(task, "operation")
    method = context_value(task, "method")
    pattern = GENERIC_OP_PATTERNS[kind]
    return bool(pattern.match(op) or pattern.match(method))


def has_standalone_token(task: ET.Element, token: str) -> bool:
    pattern = re.compile(rf"(?<![\w.]){re.escape(token)}(?![\w.])")
    return any(pattern.search(v) for v in all_node_values(task))


def node_blob(task: ET.Element) -> str:
    return " ".join(all_node_values(task)).lower()


LESS_THAN_RE = re.compile(r"<|lessthan|\blt\b")
NULL_RE = re.compile(r"\bnull\b|isnull")


def matches_due_date_filter(task: ET.Element) -> bool:
    # The Data Service registry body shape for a comparison filter is not
    # documented here (no local connection to `describe` it against -- see
    # _porting/BATCH1-ADDENDUM.md), so both a raw expression string (Flow's own
    # `dueDate < '2026-08-04'` shape, literal `<`) and a structured
    # filterGroup/operator encoding (`"operator": "LessThan"`, or the OData
    # `lt` token) are accepted -- either still proves the field + comparison
    # + threshold date are all present.
    blob = node_blob(task)
    return "duedate" in blob and "2026-08-04" in blob and bool(LESS_THAN_RE.search(blob))


def matches_null_title_filter(task: ET.Element) -> bool:
    blob = node_blob(task)
    return "contracttitle" in blob and bool(NULL_RE.search(blob))


def connector_nodes(root: ET.Element) -> list[ET.Element]:
    return [
        task
        for task in elements(root, "sendTask")
        if has_typed_uipath_extension(task, "activity", ACTIVITY_TYPE)
        and context_value(task, "connectorKey") == CONNECTOR_KEY
    ]


def has_manual_root_start(root: ET.Element) -> bool:
    process = root.find("bpmn:process", NS)
    if process is None:
        return False
    for start in process.findall("bpmn:startEvent", NS):
        has_event_def = any(
            child.tag.startswith(f"{{{NS['bpmn']}}}") and child.tag.endswith("EventDefinition")
            for child in start.iter()
            if child is not start
        )
        ext = start.find("bpmn:extensionElements", NS)
        has_uipath_event = ext is not None and ext.find("uipath:event", NS) is not None
        if not has_event_def and not has_uipath_event:
            return True
    return False


def variable_declared(root: ET.Element, var_id: str) -> bool:
    variables = root.find(".//uipath:variables", NS)
    if variables is None:
        return False
    return any(child.attrib.get("id") == var_id for child in variables)


def main() -> None:
    path, root = parse_bpmn("ContractRegistryCrudFilters")

    if not has_manual_root_start(root):
        fail("no root-level manual start event (a bpmn:startEvent with no event definition) found")
    print("OK: manual start event present")

    df_nodes = [task for task in connector_nodes(root) if entity_ok(task)]

    creates = [t for t in df_nodes if is_kind(t, CREATE_OBJECTS, "create")]
    queries = [t for t in df_nodes if is_kind(t, QUERY_OBJECTS, "query")]
    updates = [t for t in df_nodes if is_kind(t, UPDATE_OBJECTS, "update")]
    gets = [t for t in df_nodes if is_kind(t, GET_OBJECTS, "get")]

    if not creates:
        fail(f"no {ENTITY} Create Entity Record sendTask found")
    create = creates[0]
    try:
        create_body = body_object(create)
    except BodyShapeError as exc:
        fail(f"Create node body: {exc}")
    missing = FIELDS - set(create_body)
    if missing:
        fail(f"Create body missing fields: {sorted(missing)}")
    print(f"OK: Create Entity Record node populates all six {ENTITY} fields")

    if len(queries) < 2:
        fail(f"expected 2 {ENTITY} Query Entity Records nodes, found {len(queries)}")
    for q in queries:
        if not has_standalone_token(q, "100"):
            fail(f"Query node {q.attrib.get('id')!r} is not limited to 100 records")
    if not any(matches_due_date_filter(q) for q in queries):
        fail("no Query filter for dueDate < 2026-08-04 found across the Query nodes")
    if not any(matches_null_title_filter(q) for q in queries):
        fail("no Query filter for contractTitle null found across the Query nodes")
    print(f"OK: {len(queries)} Query Entity Records nodes, both limited to 100, filters present")

    if not updates:
        fail(f"no {ENTITY} Update Entity Record sendTask found")
    update = updates[0]
    try:
        update_body = body_object(update)
    except BodyShapeError as exc:
        fail(f"Update node body: {exc}")
    if "contractTitle" not in update_body:
        fail("Update body does not update contractTitle")
    title_value = update_body["contractTitle"]
    referenced = (
        UPDATE_TITLE_VAR_RE.findall(title_value)
        if isinstance(title_value, str) and title_value.startswith("=")
        else []
    )
    if not referenced:
        fail(f"Update contractTitle is not an expression reading a process variable: {title_value!r}")
    declared = [v for v in referenced if variable_declared(root, v)]
    if not declared:
        fail(f"Update contractTitle references vars.{referenced[0]}, which is not declared in <uipath:variables>")
    title_var = declared[0]
    print(f"OK: Update Entity Record contractTitle is bound to declared variable vars.{title_var}")

    if not gets:
        fail(f"no {ENTITY} Get Entity Record by ID sendTask found")
    get = gets[0]
    update_out_vars = output_vars(update)
    if not update_out_vars:
        fail("Update node has no <uipath:output var=...> for the Get node to reference")
    get_values = all_node_values(get)
    wired_var = next(
        (v for v in update_out_vars if any(f"vars.{v}" in value for value in get_values)),
        None,
    )
    if wired_var is None:
        fail(
            f"Get-by-Id node does not reference any Update output variable "
            f"(vars.{{{', '.join(update_out_vars)}}}); found values: {get_values}"
        )
    print(f"OK: Get-by-Id node references Update output vars.{wired_var}")

    crud_vars: set[str] = set()
    for t in (create, *queries, update, get):
        crud_vars.update(output_vars(t))
    # A CRUD node's response is often not exposed directly: a separate
    # BPMN.Variables mapping task first copies it into another process
    # variable (e.g. Var_CreatedRecord <- =vars.Var_CreateResponse), and the
    # end event maps out THAT copy instead. Build a var -> source map from
    # every <uipath:output var=... source=...> in the document (mapping
    # tasks and the CRUD nodes' own activity outputs alike) and follow the
    # chain up to 3 hops looking for a CRUD output var at the root.
    var_sources: dict[str, str] = {}
    for out in root.findall(".//uipath:output", NS):
        var = out.attrib.get("var")
        source = out.attrib.get("source")
        if var and source and var not in var_sources:
            var_sources[var] = source

    def derives_from_crud(var_id: str, hops: int) -> bool:
        if var_id in crud_vars:
            return True
        if hops <= 0:
            return False
        source = var_sources.get(var_id, "")
        return any(
            derives_from_crud(ref, hops - 1) for ref in re.findall(r"vars\.([A-Za-z0-9_]+)", source)
        )

    mapped = False
    for end in elements(root, "endEvent"):
        if not has_typed_uipath_extension(end, "mapping", "BPMN.Variables"):
            continue
        for out in end.findall(".//uipath:output", NS):
            source = out.attrib.get("source", "")
            if any(derives_from_crud(v, 3) for v in re.findall(r"vars\.([A-Za-z0-9_]+)", source)):
                mapped = True
                break
        if mapped:
            break
    if not mapped:
        fail(
            "no completion end event maps a CRUD node output variable "
            f"(vars.{{{', '.join(sorted(crud_vars))}}}) to a process output"
        )
    print("OK: a completion end event maps a CRUD output variable to a process output")

    print(
        f"OK: {path} — {len(creates)} create, {len(queries)} query, {len(updates)} update, "
        f"{len(gets)} get {ENTITY} node(s); filters, variable binding, and output mapping present"
    )


if __name__ == "__main__":
    main()
