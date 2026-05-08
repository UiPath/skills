#!/usr/bin/env python3
"""CEQL where: verify the agent's planned `--detail` JSON in
``where_detail.json`` carries a canonical CEQL filter tree per
``skills/uipath-platform/references/integration-service/activities.md``
— section "Filter Trees (CEQL)" — and that the .flow file references
the registered Microsoft Entra (Azure AD) connector with the List
Groups operation, plus Decision and Terminate nodes for routing.

Why we grade ``where_detail.json`` and not the .flow file's
``inputs.detail``:
  The task prompt forbids ``uip flow node configure`` (no live tenant),
  which is the command that populates ``inputs.detail``. The CLI's own
  ``uip maestro flow validate`` accepts a connector node with empty
  ``inputs: {}``, so requiring a fully-expanded ``inputs.detail`` here
  would test something the prompt forbids and the CLI doesn't enforce.
  ``where_detail.json`` is the artifact the prompt asks the agent to
  plan, so that is the artifact we grade.
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _shared.flow_check import assert_flow_has_node_type  # noqa: E402

CONNECTOR_KEY = "uipath-microsoft-azureactivedirectory"
FLOW_GLOB = "**/CeqlWhereTest*.flow"
EXPECTED_FIELD = "displayname"
EXPECTED_VALUE = "active"


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
    if not os.path.exists("where_detail.json"):
        sys.exit("FAIL: where_detail.json not found")
    try:
        plan = json.load(open("where_detail.json"))
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: where_detail.json is not valid JSON: {e}")

    filter_tree = plan.get("filter")
    if not isinstance(filter_tree, dict):
        sys.exit(
            "FAIL: where_detail.json missing top-level `filter` object — "
            "the prompt requires a structured filter tree under that key"
        )
    _assert_filter_tree_shape(filter_tree, source="where_detail.json.filter")


def _find_flow() -> str:
    flows = glob.glob(FLOW_GLOB, recursive=True)
    if not flows:
        sys.exit(f"FAIL: No flow file matching {FLOW_GLOB}")
    return flows[0]


def _check_flow_structure() -> None:
    flow_path = _find_flow()
    raw = open(flow_path).read()
    try:
        flow = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {flow_path} is not valid JSON: {e}")
    if "nodes" not in flow or "edges" not in flow:
        sys.exit("FAIL: Flow missing 'nodes' or 'edges'")

    if CONNECTOR_KEY not in raw:
        sys.exit(
            f"FAIL: Flow does not reference the registered Azure AD / Entra "
            f"connector key {CONNECTOR_KEY!r}. Display names like 'Microsoft "
            "Entra' or 'Microsoft Entra ID' are NOT registry keys — confirm "
            "the registered key with `uip maestro flow registry search`."
        )

    found_groups = False
    for node in flow.get("nodes", []):
        node_type = node.get("type", "")
        if CONNECTOR_KEY in node_type and "group" in node_type.lower():
            found_groups = True
            break
    if not found_groups:
        sys.exit(
            f"FAIL: No connector node of type "
            f"`uipath.connector.{CONNECTOR_KEY}.list-groups` (or similar) found"
        )

    assert_flow_has_node_type(["decision", "terminate"])


def main() -> None:
    _check_where_detail()
    _check_flow_structure()
    print(
        f"OK: where_detail.json carries canonical CEQL filter tree on "
        f"displayName='{EXPECTED_VALUE}'; flow targets {CONNECTOR_KEY} "
        "List Groups; Decision and Terminate nodes present"
    )


if __name__ == "__main__":
    main()
