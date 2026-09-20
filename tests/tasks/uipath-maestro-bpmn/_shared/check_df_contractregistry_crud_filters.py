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
Conventions (``context_value``/``all_node_values``/one ``target="body"``
input/entity-anywhere) match this batch's sibling ports
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
    ``dataservice-activities.json`` in BATCH1-ADDENDUM.md), since Flow's node
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
  - Flow's ``bodyParameters`` dict becomes the ONE ``target="body"`` CDATA
    JSON object (registry-workflow.md §3); more than one ``target="body"``
    input on a node is treated as a failure (the runtime does not merge them
    -- the last one silently wins), not just ignored.
  - Flow's ``queryParameters.queryExpression`` / ``.limit`` have no fixed
    field name in the Data Service registry contract available here (no
    local Data Service connection to ``describe`` request fields against --
    BATCH1-ADDENDUM.md), so filter and limit checks scan every attribute
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
    ``<uipath:output var=...>`` id, plus a sequence-flow reachability check
    (``_shared/graph.reaches``) that Update precedes Get -- stronger than
    Flow's keyword guess because the BPMN output/variable contract makes the
    real producer identifiable.
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
  - Added (not present in Flow's grader, but implied by the ported
    prompt/skill and cheap to check from the same XML walk): a manual root
    start (a ``bpmn:startEvent`` with no event definition and no
    ``uipath:event`` extension -- structural-bpmn.md's own manual-start
    derivation rule), and that every graded Data Service node carries a
    connection binding (``=bindings.<id>`` resolving to a declared
    ``resource="Connection"`` binding, per registry-workflow.md §4).

Checks performed:
  1. BPMN file exists, is well-formed XML, DI and sequence-flow integrity hold.
  2. A root-level manual start event (no event definition / uipath:event).
  3. One ContractRegistry Create Entity Record sendTask with a single
     ``target="body"`` JSON holding all six fields, all non-null.
  4. >=2 ContractRegistry Query Entity Records sendTasks, each carrying a
     standalone ``100`` limit token; across them, a dueDate < 2026-08-04
     filter and a contractTitle-is-null filter.
  5. One ContractRegistry Update Entity Record sendTask whose contractTitle
     is a ``=vars.<id>`` reference to a declared process variable.
  6. One ContractRegistry Get Entity Record by ID sendTask referencing the
     Update node's own output variable, with Update reachable-before Get on
     a sequence-flow path.
  7. Every graded node references a declared connection binding.
  8. A completion end event maps out at least one of the CRUD nodes' output
     variables.
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
from _shared.graph import reaches  # noqa: E402

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


def node_inputs(task: ET.Element) -> list[ET.Element]:
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
    # BATCH1-ADDENDUM.md), so both a raw expression string (Flow's own
    # `dueDate < '2026-08-04'` shape, literal `<`) and a structured
    # filterGroup/operator encoding (`"operator": "LessThan"`, or the OData
    # `lt` token) are accepted -- either still proves the field + comparison
    # + threshold date are all present.
    blob = node_blob(task)
    return "duedate" in blob and "2026-08-04" in blob and bool(LESS_THAN_RE.search(blob))


def matches_null_title_filter(task: ET.Element) -> bool:
    blob = node_blob(task)
    return "contracttitle" in blob and bool(NULL_RE.search(blob))


def body_json(task: ET.Element, label: str) -> dict:
    body_inputs = [inp for inp in node_inputs(task) if inp.attrib.get("target") == "body"]
    if len(body_inputs) != 1:
        fail(f'expected exactly one target="body" input on the {label} node, found {len(body_inputs)}')
    raw = body_inputs[0].text or ""
    try:
        body = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f'{label} node target="body" input is not valid JSON: {exc}\n  raw={raw!r}')
    if not isinstance(body, dict):
        fail(f'{label} node target="body" JSON must be an object, got {type(body).__name__}')
    return body


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


def binding_ids(root: ET.Element) -> set[str]:
    return {
        b.attrib.get("id", "")
        for b in root.findall(".//uipath:bindings/uipath:binding", NS)
        if b.attrib.get("resource") == "Connection"
    }


def require_connection_binding(task: ET.Element, bindings: set[str], label: str) -> None:
    connection = context_value(task, "connection")
    match = re.match(r"^=bindings\.(\S+)$", connection)
    if not match:
        fail(f"{label} node has no `=bindings.<id>` connection reference (found connection={connection!r})")
    binding_id = match.group(1)
    if binding_id not in bindings:
        fail(
            f"{label} node references binding {binding_id!r} with no matching "
            f'<uipath:binding resource="Connection"> in the process-level <uipath:bindings> block'
        )


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
    create_body = body_json(create, "Create")
    missing = FIELDS - set(create_body)
    if missing:
        fail(f"Create body missing fields: {sorted(missing)}")
    nullish = [f for f in FIELDS if create_body[f] is None]
    if nullish:
        fail(f"Create body has null values for fields: {sorted(nullish)}")
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
    update_body = body_json(update, "Update")
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
    update_id = update.attrib.get("id", "")
    get_id = get.attrib.get("id", "")
    if not reaches(root, update_id, get_id):
        fail(f"Update node {update_id!r} does not precede Get node {get_id!r} on a sequence-flow path")
    print(f"OK: Get-by-Id node references Update output vars.{wired_var}, reachable from Update")

    bindings = binding_ids(root)
    if not bindings:
        fail('no process-level <uipath:binding resource="Connection"> declared')
    for label, tasks in (("Create", creates), ("Query", queries), ("Update", updates), ("Get", gets)):
        for t in tasks:
            require_connection_binding(t, bindings, f"{label} ({t.attrib.get('id')})")
    print("OK: every graded Data Service node references a declared connection binding")

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

    require_no_private_connector_values(root)
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(
        f"OK: {path} — {len(creates)} create, {len(queries)} query, {len(updates)} update, "
        f"{len(gets)} get {ENTITY} node(s); filters, variable binding, and output mapping present"
    )


if __name__ == "__main__":
    main()
