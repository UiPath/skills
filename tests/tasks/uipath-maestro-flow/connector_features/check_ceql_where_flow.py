#!/usr/bin/env python3
"""CEQL where: verify the flow targets the SharePoint connector, has
Decision + Terminate nodes for the success/failure routing, and has the
connector node configured with a ``where`` CEQL filter — both as a
``queryParameters.where`` entry and as a ``savedFilterTrees.where`` entry
inside the connector ``configuration`` blob."""

import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _shared.flow_check import assert_flow_has_node_type  # noqa: E402

CONNECTOR_KEY = "uipath-microsoft-onedrive"
FLOW_GLOB = "**/CeqlWhereTest*.flow"


def _find_flow() -> str:
    flows = glob.glob(FLOW_GLOB, recursive=True)
    if not flows:
        sys.exit(f"FAIL: No flow file matching {FLOW_GLOB}")
    return flows[0]


def _find_connector_node(flow: dict) -> dict:
    for node in flow.get("nodes") or []:
        node_type = node.get("type", "")
        if CONNECTOR_KEY in node_type and node_type.startswith("uipath.connector."):
            return node
    sys.exit(
        f"FAIL: No connector node with type containing "
        f"'uipath.connector.{CONNECTOR_KEY}...' found"
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


def assert_where_configured(node: dict) -> None:
    detail = (node.get("inputs") or {}).get("detail") or {}
    if not detail:
        sys.exit("FAIL: connector node is missing inputs.detail")

    query_params = detail.get("queryParameters") or {}
    where_value = query_params.get("where")
    if not isinstance(where_value, str) or not where_value.strip():
        sys.exit(
            "FAIL: connector node inputs.detail.queryParameters.where "
            "must be a non-empty string"
        )

    config = _parse_configuration(detail)

    essential = config.get("essentialConfiguration") or {}
    saved_trees = essential.get("savedFilterTrees") or {}
    where_tree = saved_trees.get("where")
    if not isinstance(where_tree, dict):
        sys.exit(
            "FAIL: inputs.detail.configuration.essentialConfiguration."
            "savedFilterTrees.where is missing — the CEQL filter must be "
            "persisted in the filter builder tree"
        )

    filters = where_tree.get("filters")
    if not isinstance(filters, list) or not filters:
        sys.exit(
            "FAIL: savedFilterTrees.where.filters is empty — "
            "add at least one filter entry (e.g. createdDateTime operator)"
        )

    first = filters[0]
    if not first.get("id"):
        sys.exit("FAIL: savedFilterTrees.where.filters[0].id is missing")
    if not first.get("operator"):
        sys.exit("FAIL: savedFilterTrees.where.filters[0].operator is missing")
    value = first.get("value")
    if not isinstance(value, dict) or value.get("value") in (None, ""):
        sys.exit("FAIL: savedFilterTrees.where.filters[0].value.value is missing")


def main():
    flow_path = _find_flow()
    with open(flow_path) as f:
        flow = json.load(f)
    if "nodes" not in flow or "edges" not in flow:
        sys.exit("FAIL: Flow missing 'nodes' or 'edges'")

    raw = open(flow_path).read()
    if CONNECTOR_KEY not in raw:
        sys.exit(f"FAIL: Connector key {CONNECTOR_KEY!r} not found in {flow_path}")

    connector_node = _find_connector_node(flow)
    assert_where_configured(connector_node)

    assert_flow_has_node_type(["decision", "terminate"])

    print(
        f"OK: {len(flow['nodes'])} nodes, {len(flow['edges'])} edges; "
        f"{CONNECTOR_KEY} referenced; Decision and Terminate nodes present; "
        f"where filter configured in queryParameters and savedFilterTrees"
    )


if __name__ == "__main__":
    main()
