#!/usr/bin/env python3
"""CEQL where: verify the flow targets the Microsoft Entra (Azure AD)
connector's "List Groups" operation, has Decision + Terminate nodes for
the success/failure routing, and has the connector node configured with a
``where`` CEQL filter on ``displayName = "active"`` — persisted both as a
``queryParameters.where`` expression and as a structured
``savedFilterTrees.where`` tree inside the connector ``configuration`` blob
(same Studio Web contract used for connector-trigger filter trees)."""

import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _shared.flow_check import assert_flow_has_node_type  # noqa: E402

CONNECTOR_KEYS = (
    "uipath-microsoft-azureactivedirectory",
)
FLOW_GLOB = "**/CeqlWhereTest*.flow"
EXPECTED_FIELD = "displayname"
EXPECTED_VALUE = "active"


def _find_flow() -> str:
    flows = glob.glob(FLOW_GLOB, recursive=True)
    if not flows:
        sys.exit(f"FAIL: No flow file matching {FLOW_GLOB}")
    return flows[0]


def _find_connector_node(flow: dict) -> dict:
    for node in flow.get("nodes") or []:
        node_type = node.get("type", "")
        if not node_type.startswith("uipath.connector."):
            continue
        if any(key in node_type for key in CONNECTOR_KEYS):
            return node
    sys.exit(
        f"FAIL: No connector node with type containing one of {CONNECTOR_KEYS} found"
    )


def _assert_list_groups_operation(node: dict) -> None:
    """The operation key/path must reference groups (List Groups)."""
    node_type = node.get("type", "")
    detail = (node.get("inputs") or {}).get("detail") or {}
    haystack_parts = [node_type]
    if isinstance(detail, dict):
        for key in ("operationId", "operation", "method", "path", "resource"):
            v = detail.get(key)
            if isinstance(v, str):
                haystack_parts.append(v)
    elif isinstance(detail, str):
        haystack_parts.append(detail)
    haystack = " ".join(haystack_parts).lower()
    if "group" not in haystack:
        sys.exit(
            "FAIL: connector node does not appear to target the List Groups "
            f"operation (no 'group' token found in type/operation: {haystack!r})"
        )


def _parse_configuration(detail: dict) -> dict:
    """``inputs.detail.configuration`` is stored as ``=jsonString:{...}``.
    Strip the prefix and parse the JSON payload."""
    raw = detail.get("configuration")
    if not isinstance(raw, str) or not raw.strip():
        sys.exit("FAIL: connector node inputs.detail.configuration is missing or empty")
    payload = re.sub(r"^\s*=jsonString:\s*", "", raw)
    try:
        return json.loads(payload)
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: inputs.detail.configuration is not valid JSON: {e}")


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
    return n.get("fieldName") or n.get("field") or n.get("id") or n.get("name")


def _leaf_value(n: dict):
    v = n.get("value")
    if isinstance(v, dict):
        return v.get("value")
    return v


def _assert_filter_tree_shape(where_tree) -> None:
    """Same shape contract trigger_with_filter.yaml enforces: a structured
    tree with a numeric groupOperator, a non-empty filters array, at least
    one leaf referencing the displayName field, and the value 'active'."""
    if not isinstance(where_tree, dict):
        sys.exit(
            "FAIL: savedFilterTrees.where is missing — the CEQL filter must be "
            "persisted in the structured filter builder tree, not only as a "
            "raw expression string"
        )

    if not isinstance(where_tree.get("groupOperator"), (int, float)):
        sys.exit(
            "FAIL: savedFilterTrees.where.groupOperator must be a number "
            "(0 = And, 1 = Or) — Studio Web's persisted shape"
        )

    filters = where_tree.get("filters")
    if not isinstance(filters, list) or not filters:
        sys.exit(
            "FAIL: savedFilterTrees.where.filters is empty — "
            "add at least one filter entry on displayName"
        )

    leaves = [n for n in _walk(where_tree) if isinstance(n.get("operator"), str)]
    if not leaves:
        sys.exit("FAIL: savedFilterTrees.where contains no leaf filter with an `operator`")

    fields = [_leaf_field(n) for n in leaves]
    if not any(isinstance(f, str) and EXPECTED_FIELD in f.lower() for f in fields):
        sys.exit(
            f"FAIL: filter tree does not reference the `displayName` field "
            f"(found fields: {[f for f in fields if f]})"
        )

    values = [_leaf_value(n) for n in leaves]
    if not any(isinstance(v, str) and v.strip().lower() == EXPECTED_VALUE for v in values):
        sys.exit(
            f"FAIL: no leaf has value '{EXPECTED_VALUE}' "
            f"(found values: {[v for v in values if v is not None]})"
        )


def assert_where_configured(node: dict) -> None:
    detail = (node.get("inputs") or {}).get("detail") or {}
    if not detail:
        sys.exit("FAIL: connector node is missing inputs.detail")

    if isinstance(detail, str):
        # `=js:` expression form — the whole detail object is computed at
        # runtime, so structural fields (queryParameters, savedFilterTrees)
        # live inside the expression string. Accept iff the where filter
        # is referenced lexically and mentions displayName + active.
        for token, label in (
            ("queryParameters", "'queryParameters'"),
            (r"\bwhere\b", "a 'where' filter"),
            ("displayName", "the displayName field"),
            ("active", "the value 'active'"),
        ):
            if not re.search(token, detail, flags=re.IGNORECASE):
                sys.exit(
                    f"FAIL: connector node inputs.detail is a JS expression "
                    f"but does not reference {label}"
                )
        return

    query_params = detail.get("queryParameters") or {}
    where_value = query_params.get("where")
    if not isinstance(where_value, str) or not where_value.strip():
        sys.exit(
            "FAIL: connector node inputs.detail.queryParameters.where "
            "must be a non-empty string"
        )
    if "displayname" not in where_value.lower() or EXPECTED_VALUE not in where_value.lower():
        sys.exit(
            "FAIL: queryParameters.where must reference displayName and 'active' "
            f"(got: {where_value!r})"
        )

    config = _parse_configuration(detail)
    essential = config.get("essentialConfiguration") or {}
    saved_trees = essential.get("savedFilterTrees") or {}
    _assert_filter_tree_shape(saved_trees.get("where"))


def main():
    flow_path = _find_flow()
    with open(flow_path) as f:
        raw = f.read()
    flow = json.loads(raw)
    if "nodes" not in flow or "edges" not in flow:
        sys.exit("FAIL: Flow missing 'nodes' or 'edges'")

    if not any(key in raw for key in CONNECTOR_KEYS):
        sys.exit(
            f"FAIL: None of the expected Azure AD / Entra connector keys "
            f"{CONNECTOR_KEYS} found in {flow_path}"
        )

    connector_node = _find_connector_node(flow)
    _assert_list_groups_operation(connector_node)
    assert_where_configured(connector_node)

    assert_flow_has_node_type(["decision", "terminate"])

    print(
        f"OK: {len(flow['nodes'])} nodes, {len(flow['edges'])} edges; "
        f"Azure AD / Entra List Groups referenced; Decision and Terminate nodes "
        f"present; where filter tree on displayName='active' configured in "
        f"queryParameters and savedFilterTrees"
    )


if __name__ == "__main__":
    main()
