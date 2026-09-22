#!/usr/bin/env python3
"""E2eContractIntakePipeline (BPMN): ContractRegistry CRUD chain + connector shape.

Ported from Flow
`connector_features/datafabric_connector/e2e_contract_intake_pipeline.yaml`'s
``check_e2e_contract_intake_pipeline.py`` (CRUD chain) and the shared
``_shared/check_connector_node_shape.py`` (connector-shape criterion),
translated from a JSON node/``inputs.detail`` walk to an XML walk over the
registry-driven ``Intsvc.ActivityExecution`` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3-4). Node
classification helpers are copied from the passing sibling port
``connector_features/datafabric_connector/contractregistry_crud_filters/``'s
``check_df_contractregistry_crud_filters.py`` for this batch's consistency.

Two modes, one file (kept together per _porting/BATCH1-ADDENDUM.md's "no new shared
modules" rule):

  - default: the CRUD-chain criterion (Flow's ``check_e2e_contract_intake_pipeline.py``).
  - ``--shape``: the connector-shape criterion (Flow's
    ``_shared/check_connector_node_shape.py``).

CRUD-chain re-homing decisions vs the Flow grader:
  - ``node.type`` suffix matching (``.create-entity-record`` etc.) becomes an
    ``Intsvc.ActivityExecution`` sendTask matched on ``objectName`` against
    the Data Service catalog: both the curated and ``_V3``/``V2`` spellings
    are accepted for every operation, since Flow's node types did not
    distinguish them. The connector also exposes a GENERIC entity-CRUD form
    (``objectName`` is the entity name itself, operation read off context
    ``operation``/``method``) -- accepted alongside the curated form,
    matching this batch's other Data Fabric checkers.
  - Flow's ``pathParameters.entityName``/``queryParameters`` fields have no
    fixed home in the registry contract, so entity membership, the recordId
    wiring, and the priority-DESC sort are all scanned across every
    ``uipath:input`` value/text reachable from a node (``entity_ok``/
    ``all_node_values``/``has_priority_desc_sort``), not one named field --
    matching the batch's sibling checkers.
  - Flow's ``bodyParameters`` dict becomes every ``target="body"`` input's
    JSON, merged into one dict (registry-workflow.md §3 documents ONE
    `target="body"` input as the canonical shape, but Flow's own grader never
    penalized node shape -- only body *content* -- so more than one such
    input is not itself a chain-criterion failure here; see ``--shape`` mode
    below for the shape assertion Flow actually never made either).
  - Flow's ``wired_to_create`` (``recordId`` expr is ``=js:`` and contains a
    create node id) becomes a real variable-binding assertion: the consuming
    node's inputs must contain ``vars.<V>`` where ``V`` is one of the Create
    sendTask's own ``<uipath:output var=...>`` ids.
  - Flow's grader is intentionally narrower than its own prompt (see its
    module docstring: "Loop / branch / multi-node orchestration is
    intentionally NOT enforced"). It never actually graded the Query's
    contractTitle-equality filter, nor the create body's non-contractTitle
    fields (status/priority/dueDate/value/isUrgent), nor the update's
    "In Review" value, nor any sequence-flow ordering between Create and its
    consumers -- only that the create body contains contractTitle, the query
    is sorted by priority DESC, and the update body's only key is `status`.
    This port keeps that exact scope: it does not add checks Flow never
    graded, even though the prompt asks for more.

Connector-shape re-homing (the ``--shape`` mode): Flow's
``_shared/check_connector_node_shape.py`` fetches each node's live manifest
(``uip maestro flow registry get <type> --output json``) and diffs
``inputs.detail`` against it (endpoint URL match, parameter-section
placement, required-parameter coverage). Checking its actual assertions
against what has a network-free BPMN analog:
  - "endpoint == manifest.path": needs a live registry enrichment call
    against a real connection; _porting/BATCH1-ADDENDUM.md forbids running that from a
    grader. NOT PORTED.
  - "param-in-wrong-section": same live-manifest dependency. NOT PORTED.
  - "required-param-missing": WARN-only in Flow itself (never fails the
    check), and also depends on the live per-operation manifest. NOT PORTED.
  - "node has connectorMethodInfo" (i.e. `manifest(ntype)` resolves at all --
    the node's type is a real, known connector operation): the BPMN analog
    that needs no live call is that the sendTask actually carries the
    ``Intsvc.ActivityExecution`` typed wrapper it claims via its
    ``connectorKey`` context input. PORTED.
  Connection-binding validity (`=bindings.<id>` resolving to a declared
  `resource="Connection"` binding) and "at most one target=body input" are
  BOTH dropped from this mode: neither is a check Flow's
  ``check_connector_node_shape.py`` ever performed (it does not look at
  connections at all, and its body-shape check is about *parameter-section*
  placement per the live manifest, not input *count*), so neither traces to
  an F assertion.

Checks performed (default mode):
  1. BPMN file exists and is well-formed XML.
  2. One ContractRegistry Create Entity Record sendTask with a body
     containing `contractTitle`.
  3. One ContractRegistry Get Entity Record by ID sendTask wired to the
     Create node's own output variable.
  4. One ContractRegistry Query Entity Records sendTask sorted by priority
     DESC.
  5. One ContractRegistry Update Entity Record sendTask whose body's only
     key is `status`, wired to the Create node's output variable.
  6. One ContractRegistry Delete Entity Record sendTask wired to the Create
     node's output variable.

Checks performed (`--shape` mode):
  1. BPMN file exists and is well-formed XML.
  2. Every sendTask carrying a `connectorKey` context input also carries the
     `Intsvc.ActivityExecution` typed `<uipath:activity>` extension.

Assertion map (Flow -> BPMN):
  F check_e2e_contract_intake_pipeline.py:97-101   >=1 create on ENTITY, body has contractTitle       -> creates[0] + "contractTitle" in merged body_json(create)
  F check_e2e_contract_intake_pipeline.py:106-111  get recordId wired to create output                -> wired_to_create(get, create_vars)
  F check_e2e_contract_intake_pipeline.py:113-118  >=1 query on ENTITY sorted priority DESC            -> has_priority_desc_sort(query)
  F check_e2e_contract_intake_pipeline.py:120-132  update body keys=={"status"}, wired to create output -> body_json(update)=={"status"} + wired_to_create(update, create_vars)
  F check_e2e_contract_intake_pipeline.py:134-139  delete recordId wired to create output              -> wired_to_create(delete, create_vars)
  F _shared/check_connector_node_shape.py:48-51    manifest(ntype) resolves (node type is real)        -> has_typed_uipath_extension(task, "activity", ACTIVITY_TYPE) in --shape mode
  I                                                 locate/parse .bpmn                                  -> parse_bpmn()
  T                                                 curated|generic objectName classification           -> is_kind()
  T                                                 entity name anywhere in node inputs/objectName/path  -> entity_ok()
  T                                                 vars.<VarId> substring reference in place of Flow node-id reference -> wired_to_create()
  T                                                 merge every target="body" input instead of requiring exactly one (chain criterion only) -> body_json()
  DROPPED  require_no_private_connector_values  (not in Flow; `validate` criterion already covers structure)
  DROPPED  require_sequence_integrity            (not in Flow; `validate` criterion already covers structure)
  DROPPED  require_di_for_visible_elements       (not in Flow; `validate` criterion already covers structure)
  DROPPED  Create->Get / Create->Update / Create->Delete graph.reaches reachability (chain criterion)  (Flow's grader has no edge/order check at all -- it only checks the recordId expression string)
  DROPPED  --shape mode: connection-binding validity (`=bindings.<id>` resolves to a declared resource="Connection" binding)  (Flow's check_connector_node_shape.py never checks connections)
  DROPPED  --shape mode: "at most one target=body input" hard failure  (Flow's check_connector_node_shape.py never asserts input count; its body-shape check is about live-manifest parameter-section placement)
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
    all_node_values,
    context_value,
    elements,
    fail,
    has_typed_uipath_extension,
    parse_bpmn,
)

CONNECTOR_KEY = "uipath-uipath-dataservice"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
ENTITY = "ContractRegistry"

CREATE_OBJECTS = {"CreateEntityRecordCurated", "CreateEntityRecord_V3"}
GET_OBJECTS = {"GetEntityRecordByIdCurated", "GetEntityRecord_V3"}
QUERY_OBJECTS = {"QueryEntityRecordsCurated", "QueryEntityRecords_V3"}
UPDATE_OBJECTS = {"UpdateEntityRecordV2", "UpdateEntityRecord_V3"}
DELETE_OBJECTS = {"DeleteEntityRecordCurated", "DeleteEntityRecord_V3"}

# The Data Service connector also has a GENERIC entity-CRUD form: objectName
# is the entity name itself ("ContractRegistry") on every node, and the
# operation is distinguished by the context `operation`/`method` fields
# instead of a curated per-op objectName. Checked against `operation` OR
# `method` (either field matching is enough) -- matches
# check_df_contractregistry_crud_filters.py's GENERIC_OP_PATTERNS, extended
# with a `delete` kind for this pipeline's Delete step.
GENERIC_OP_PATTERNS = {
    "create": re.compile(r"^(create|post)$", re.IGNORECASE),
    "get": re.compile(r"^(retrieve|getbyid)$", re.IGNORECASE),
    "query": re.compile(r"^(list|get)$", re.IGNORECASE),
    "update": re.compile(r"^(update|replace|put|patch)$", re.IGNORECASE),
    "delete": re.compile(r"^(delete|remove)$", re.IGNORECASE),
}

DESC_TOKEN_RE = re.compile(r"\bdesc(ending)?\b", re.IGNORECASE)

# A curated Query node carries the sort field and direction as two SEPARATE
# named inputs (e.g. `_sortFieldName`="priority", `isAscending`="false"), so
# neither name nor value alone proves DESC-by-priority -- unlike a raw
# expression/metadata blob where both tokens appear together in one string.
# Check named inputs first; fall back to blob-text scanning (Flow's own dual
# tolerance) only for the js:/metadata-embedded shape where both live in one
# expression string.
SORT_FIELD_NAMES = {"sortfieldname", "_sortfieldname", "sortfield", "sortby", "orderby"}
SORT_DIR_NAMES = {"isascending", "sortdirection", "sortorder", "direction"}


# --------------------------------------------------------------------------
# Shared node-reading helpers (copied from check_df_contractregistry_crud_filters.py)
# --------------------------------------------------------------------------


def node_inputs(task: ET.Element) -> list[ET.Element]:
    return task.findall(".//uipath:input", NS)


def node_blob(task: ET.Element) -> str:
    return " ".join(all_node_values(task)).lower()


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


def body_json(task: ET.Element, label: str) -> dict:
    """Merge every target="body" input's JSON into one dict.

    Flow's grader reads a single `bodyParameters` dict and never penalized
    node *shape* -- only body *content* (see module docstring). A
    hand-authored BPMN file may carry more than one `target="body"` input
    without that being a chain-criterion failure Flow ever asserted, so this
    merges rather than hard-failing on the count.
    """
    merged: dict = {}
    found_any = False
    for inp in node_inputs(task):
        if inp.attrib.get("target") != "body":
            continue
        raw = inp.text or ""
        if not raw.strip():
            continue
        found_any = True
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            fail(f'{label} node target="body" input is not valid JSON: {exc}\n  raw={raw!r}')
        if not isinstance(parsed, dict):
            fail(f'{label} node target="body" JSON must be an object, got {type(parsed).__name__}')
        merged.update(parsed)
    if not found_any:
        fail(f'no target="body" input found on the {label} node')
    return merged


def connector_nodes(root: ET.Element) -> list[ET.Element]:
    return [
        task
        for task in elements(root, "sendTask")
        if has_typed_uipath_extension(task, "activity", ACTIVITY_TYPE)
        and context_value(task, "connectorKey") == CONNECTOR_KEY
    ]


def wired_to_create(task: ET.Element, create_vars: list[str]) -> bool:
    values = all_node_values(task)
    return any(f"vars.{v}" in value for value in values for v in create_vars)


def named_inputs(task: ET.Element) -> list[tuple[str, str]]:
    pairs = []
    for inp in node_inputs(task):
        name = (inp.attrib.get("name") or "").strip().lower()
        value = (inp.attrib.get("value") or inp.text or "").strip()
        pairs.append((name, value))
    return pairs


def has_priority_desc_sort(task: ET.Element) -> bool:
    pairs = named_inputs(task)
    field_hit = any(name in SORT_FIELD_NAMES and "priority" in value.lower() for name, value in pairs)
    dir_hit = False
    for name, value in pairs:
        if name not in SORT_DIR_NAMES:
            continue
        v = value.lower()
        if v.startswith("=js:"):
            dir_hit = True  # lenient, matches Flow's own leniency for js: expressions
        elif name == "isascending" and v == "false":
            dir_hit = True
        elif v in ("desc", "descending"):
            dir_hit = True
    if field_hit and dir_hit:
        return True
    # Fallback: a single expression/metadata string carrying both tokens
    # together (e.g. a `=js:` sort expression, or a metadata JSON blob).
    blob = node_blob(task)
    return "priority" in blob and bool(DESC_TOKEN_RE.search(blob))


# --------------------------------------------------------------------------
# Default mode: CRUD-chain criterion
# --------------------------------------------------------------------------


def main() -> None:
    path, root = parse_bpmn()

    df_nodes = [task for task in connector_nodes(root) if entity_ok(task)]

    creates = [t for t in df_nodes if is_kind(t, CREATE_OBJECTS, "create")]
    gets = [t for t in df_nodes if is_kind(t, GET_OBJECTS, "get")]
    queries = [t for t in df_nodes if is_kind(t, QUERY_OBJECTS, "query")]
    updates = [t for t in df_nodes if is_kind(t, UPDATE_OBJECTS, "update")]
    deletes = [t for t in df_nodes if is_kind(t, DELETE_OBJECTS, "delete")]

    if not creates:
        fail(f"no {ENTITY} Create Entity Record sendTask found")
    create = creates[0]
    create_body = body_json(create, "Create")
    if "contractTitle" not in create_body:
        fail("Create body missing contractTitle")
    print(f"OK: Create Entity Record node on {ENTITY} populates contractTitle")

    create_vars = output_vars(create)
    if not create_vars:
        fail("Create node has no <uipath:output var=...> for Get/Update/Delete to reference")

    if not gets:
        fail(f"no {ENTITY} Get Entity Record by ID sendTask found")
    if not any(wired_to_create(g, create_vars) for g in gets):
        fail(f"no Get node's recordId is wired to Create output vars.{{{', '.join(create_vars)}}}")
    print("OK: Get-by-Id node wired to Create output")

    if not queries:
        fail(f"no {ENTITY} Query Entity Records sendTask found")
    if not any(has_priority_desc_sort(q) for q in queries):
        fail("no Query node sorted by priority DESC")
    print(f"OK: Query Entity Records node sorted by priority DESC")

    if not updates:
        fail(f"no {ENTITY} Update Entity Record sendTask found")
    update_candidates = [u for u in updates if set(body_json(u, "Update").keys()) == {"status"}]
    if not update_candidates:
        keys_seen = [sorted(body_json(u, "Update").keys()) for u in updates]
        fail(f"no Update node whose body is exactly {{'status'}} (found: {keys_seen})")
    if not any(wired_to_create(u, create_vars) for u in update_candidates):
        fail(f"no status-only Update node's recordId is wired to Create output vars.{{{', '.join(create_vars)}}}")
    print("OK: Update node (status only) wired to Create output")

    if not deletes:
        fail(f"no {ENTITY} Delete Entity Record sendTask found")
    if not any(wired_to_create(d, create_vars) for d in deletes):
        fail(f"no Delete node's recordId is wired to Create output vars.{{{', '.join(create_vars)}}}")
    print("OK: Delete node wired to Create output")

    print(
        f"OK: {path} — Create → Get, Query(priority DESC), Update(status only) → "
        f"Delete, all on {ENTITY}, recordId chained from Create output"
    )


# --------------------------------------------------------------------------
# --shape mode: connector node shape criterion
# --------------------------------------------------------------------------


def shape_main() -> int:
    path, root = parse_bpmn()

    findings: list[tuple[str, str, str]] = []
    connector_like = [task for task in elements(root, "sendTask") if context_value(task, "connectorKey")]

    for task in connector_like:
        nid = task.attrib.get("id", "?")
        if not has_typed_uipath_extension(task, "activity", ACTIVITY_TYPE):
            findings.append(
                (
                    nid,
                    "missing-activity-type",
                    f"sendTask has connectorKey={context_value(task, 'connectorKey')!r} but no "
                    f"{ACTIVITY_TYPE} typed <uipath:activity> extension",
                )
            )

    if not findings:
        print(
            f"OK: {path} — {len(connector_like)} connector sendTask(s), 0 shape defects "
            f"({ACTIVITY_TYPE} wrapper present)"
        )
        return 0

    for nid, check, msg in findings:
        print(f"FAIL  {nid:30}  {check:28}  {msg}", file=sys.stderr)
    print(f"---\n{len(findings)} shape defect(s) across {len(connector_like)} connector sendTask(s)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    if "--shape" in sys.argv[1:]:
        sys.exit(shape_main())
    main()
