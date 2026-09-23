#!/usr/bin/env python3
"""CEQL where (BPMN): verify the agent's planned filter JSON in
``where_detail.json`` carries a canonical CEQL filter tree per
``skills/uipath-platform/references/integration-service/activities.md``
— section "Filter Trees (CEQL)" — and that the .bpmn file references the
registered Microsoft Entra (Azure AD) connector with the List Groups
operation, plus a Terminate end event for routing.

Ported from Flow `connector_features/ceql_where.yaml`'s
``check_ceql_where_flow.py``: same scenario (plan a structured CEQL filter
tree for Entra's List Groups operation; build a connector node + Terminate
routing), translated from a JSON node/edge walk to an XML walk over the
registry-driven ``Intsvc.ActivityExecution`` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3-4) and a
Terminate end event (see skills/uipath-maestro-bpmn/references/
structural-bpmn.md, "Terminate (end events only)").

Why we still grade ``where_detail.json`` and not the node's live inputs:
  The prompt forbids live node/connection configuration (no tenant in the
  sandbox), which is what would populate the enriched `where`/`queryExpression`
  input on the `Intsvc.ActivityExecution` node (registry-workflow.md §3 —
  enrichment requires a live `--connection-id`). `uip maestro bpmn validate`
  accepts a connector node with an empty/draft body, so requiring a fully
  enriched body here would test something the prompt forbids and the CLI
  doesn't enforce. This is the same rationale the Flow grader documents, and
  it holds identically for BPMN: `where_detail.json` is the artifact the
  prompt asks the agent to plan, so that is the artifact we grade.

Assertion map (Flow → BPMN):
  F check_ceql_where_flow.py:116-133  where_detail.json filter-tree shape   → _check_where_detail() (verbatim: format-agnostic JSON check)
  F check_ceql_where_flow.py:167-173  CONNECTOR_KEY referenced in flow     → connector_task(root, CONNECTOR_KEY) present
  F check_ceql_where_flow.py:140-154  _is_groups_operation node match      → _is_groups_operation(task)
  F check_ceql_where_flow.py:182      assert_flow_has_node_type(["terminate"]) → _has_terminate_end_event(root)
  I                                    locate/parse .bpmn                   → parse_bpmn()
  T                                    curated vs generic connector form    → _is_groups_operation() accepts objectName containing "group" (any
                                                                              curated spelling) OR objectName=="groups" with method GET / operation
                                                                              List/list-groups (the generic form; confirmed live against the
                                                                              uipath-microsoft-azureactivedirectory connector's `groups` object,
                                                                              whose only describable object name is "groups" — the curated name
                                                                              "ListGroups" is never a valid --object-name on its own)
  DROPPED  require_no_private_connector_values   (not in Flow)
  DROPPED  require_sequence_integrity            (not in Flow; `bpmn validate` is not graded here either, matching Flow)
  DROPPED  require_di_for_visible_elements       (not in Flow)
  DROPPED  connection-binding check              (Flow never checked connections; node is expected to stay draft, no live tenant)
"""

from __future__ import annotations

import glob
import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import NS, elements, fail, parse_bpmn  # noqa: E402

CONNECTOR_KEY = "uipath-microsoft-azureactivedirectory"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
WHERE_DETAIL_GLOB = "**/where_detail.json"
EXPECTED_FIELD = "displayname"
EXPECTED_VALUE = "active"


# --- where_detail.json filter-tree checks (verbatim from Flow's
# check_ceql_where_flow.py — this artifact is a standalone JSON planning file
# unrelated to the .flow/.bpmn format, so the check does not change at all) ---


def _walk(node):
    """Yield every dict in a nested filter tree (groups + leaves)."""
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


def _leaf_field(n: dict):
    return n.get("id") or n.get("fieldName") or n.get("field") or n.get("name")


def _leaf_value(n: dict):
    v = n.get("value")
    if isinstance(v, dict):
        return v.get("value")
    return v


def _looks_like_filter_tree(node) -> bool:
    """A canonical filter-tree dict carries a numeric ``groupOperator`` and a
    list of ``filters``. Used to locate the tree regardless of the key the
    agent stored it under (e.g. top-level ``filter``, ``filterTree``, or
    nested under ``plannedDetail.filter``)."""
    return (
        isinstance(node, dict)
        and isinstance(node.get("groupOperator"), (int, float))
        and isinstance(node.get("filters"), list)
    )


def _find_filter_tree(plan):
    """Return the first filter-tree-shaped dict found anywhere in ``plan``.
    The prompt asks the agent to capture a filter for review but does not pin
    the JSON key, so accept the tree under any key."""
    for node in _walk(plan):
        if _looks_like_filter_tree(node):
            return node
    return None


def _assert_filter_tree_shape(tree, *, source: str) -> None:
    """Per Filter Trees (CEQL) doc: structured tree with numeric
    groupOperator (0 = And, 1 = Or), at least one leaf with PascalCase
    operator referencing displayName='active'. Leaves use ``id`` (canonical)
    or fall back to ``fieldName``/``field``/``name`` for older shapes."""
    if not isinstance(tree, dict):
        sys.exit(f"FAIL: {source} must be a filter-tree object")

    if not isinstance(tree.get("groupOperator"), (int, float)):
        sys.exit(
            f"FAIL: {source}.groupOperator must be a number "
            "(0 = And, 1 = Or) — see Filter Trees (CEQL) doc"
        )

    filters = tree.get("filters")
    if not isinstance(filters, list) or not filters:
        sys.exit(f"FAIL: {source}.filters must be a non-empty list")

    leaves = [n for n in _walk(tree) if isinstance(n.get("operator"), str)]
    if not leaves:
        sys.exit(f"FAIL: {source} has no leaf filter with `operator`")

    fields = [_leaf_field(n) for n in leaves]
    if not any(isinstance(f, str) and EXPECTED_FIELD in f.lower() for f in fields):
        sys.exit(
            f"FAIL: {source} leaves do not reference the displayName field "
            f"(found fields: {[f for f in fields if f]})"
        )

    values = [_leaf_value(n) for n in leaves]
    if not any(isinstance(v, str) and v.strip().lower() == EXPECTED_VALUE for v in values):
        sys.exit(
            f"FAIL: {source} has no leaf with value '{EXPECTED_VALUE}' "
            f"(found values: {[v for v in values if v is not None]})"
        )


def _check_where_detail() -> None:
    matches = glob.glob(WHERE_DETAIL_GLOB, recursive=True)
    if not os.path.exists("where_detail.json") and not matches:
        sys.exit("FAIL: where_detail.json not found")
    path = "where_detail.json" if os.path.exists("where_detail.json") else matches[0]
    try:
        plan = json.load(open(path))
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")

    filter_tree = _find_filter_tree(plan)
    if filter_tree is None:
        sys.exit(
            "FAIL: where_detail.json has no filter-tree object (a dict with a "
            "numeric `groupOperator` and a `filters` list) under any key — "
            "the prompt requires a structured CEQL filter tree"
        )
    _assert_filter_tree_shape(filter_tree, source="where_detail.json filter tree")


# --- .bpmn structural checks ---


def context_inputs(task: ET.Element) -> list[ET.Element]:
    return task.findall(".//uipath:input", NS)


def context_value(task: ET.Element, name: str) -> str:
    for inp in context_inputs(task):
        if inp.attrib.get("name") == name:
            return inp.attrib.get("value") or (inp.text or "")
    return ""


def has_type(el: ET.Element, token: str) -> bool:
    return token in ET.tostring(el, encoding="unicode")


def connector_task(root: ET.Element, connector_key: str) -> ET.Element | None:
    for task in elements(root, "sendTask"):
        if has_type(task, ACTIVITY_TYPE) and context_value(task, "connectorKey") == connector_key:
            return task
    return None


def _is_groups_operation(task: ET.Element) -> bool:
    """Match either connector form (see BATCH1-ADDENDUM "Lessons from batch 1
    CI"): a curated objectName that names the group (contains "group"), or
    the generic object form — objectName=="groups" with method GET / an
    operation naming List — confirmed live against the connector's
    enrichment (`uip is activities list uipath-microsoft-azureactivedirectory
    --output json`: ListGroups -> ObjectName "groups", MethodName "GET";
    `uip maestro bpmn registry get Intsvc.ActivityExecution --object-name
    groups --operation List` -> Operation.Name "List", Curated "List Groups").
    """
    if context_value(task, "connectorKey") != CONNECTOR_KEY:
        return False

    object_name = (context_value(task, "objectName") or "").lower()
    if "group" in object_name:
        return True

    method = (context_value(task, "method") or "").upper()
    operation = (context_value(task, "operation") or "").lower()
    path = (context_value(task, "path") or "").rstrip("/").lower()
    return (
        object_name == "groups"
        and (method == "GET" or "list" in operation)
        and (not path or path.endswith("/groups"))
    )


def _has_terminate_end_event(root: ET.Element) -> bool:
    for end in elements(root, "endEvent"):
        if end.find("bpmn:terminateEventDefinition", NS) is not None:
            return True
    return False


def _check_bpmn_structure() -> None:
    path, root = parse_bpmn("CeqlWhereTest")

    task = connector_task(root, CONNECTOR_KEY)
    if task is None:
        fail(
            f"BPMN does not reference the registered Azure AD / Entra connector "
            f"key {CONNECTOR_KEY!r} on a bpmn:sendTask carrying {ACTIVITY_TYPE}. "
            "Display names like 'Microsoft Entra' or 'Microsoft Entra ID' are "
            "NOT registry keys — confirm the registered key with "
            "`uip maestro bpmn registry search`."
        )

    if not _is_groups_operation(task):
        fail(
            f"connector sendTask does not target the List Groups operation "
            f"(objectName={context_value(task, 'objectName')!r}, "
            f"method={context_value(task, 'method')!r}, "
            f"operation={context_value(task, 'operation')!r})"
        )
    print(f"OK: {CONNECTOR_KEY} sendTask targets List Groups")

    if not _has_terminate_end_event(root):
        fail("no bpmn:endEvent with bpmn:terminateEventDefinition found")
    print(f"OK: {path} has a Terminate end event")


def main() -> None:
    _check_where_detail()
    _check_bpmn_structure()
    print(
        f"OK: where_detail.json carries canonical CEQL filter tree on "
        f"displayName='{EXPECTED_VALUE}'; BPMN targets {CONNECTOR_KEY} "
        "List Groups; Terminate end event present"
    )


if __name__ == "__main__":
    main()
