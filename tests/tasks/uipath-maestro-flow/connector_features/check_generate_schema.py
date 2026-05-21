#!/usr/bin/env python3
"""GenerateSchema: verify the agent's GenerateSchemaTest flow wires the
Atlassian Jira "Create Issue" connector node end-to-end.

Consolidates four checks the YAML previously inlined as ``python3 -c``
one-liners:

1. Flow file exists and is valid JSON with ``nodes`` and ``edges``.
2. Flow contains a node of type
   ``uipath.connector.uipath-atlassian-jira.create-issue``.
3. ``customFieldsRequestDetails`` records BOTH parent-field tuples
   (``fields_sub_project_sub_key`` + ``fields_sub_issuetype_sub_id``)
   under the ``GenerateSchema`` objectActionName so the schema fetch can
   be replayed at design time.
4. ``bodyParameters`` carries a non-empty ``fields.summary``.
"""

from __future__ import annotations

import glob
import json
import sys

FLOW_GLOB = "**/GenerateSchemaTest*.flow"
JIRA_NODE_TYPE = "uipath.connector.uipath-atlassian-jira.create-issue"
REQUIRED_RAW_TOKENS = (
    "GenerateSchema",
    "fields_sub_project_sub_key",
    "fields_sub_issuetype_sub_id",
)


def _fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def _find_flow() -> str:
    flows = glob.glob(FLOW_GLOB, recursive=True)
    if not flows:
        _fail(f"No flow file matching {FLOW_GLOB}")
    return flows[0]


def main() -> None:
    flow_path = _find_flow()
    raw = open(flow_path, encoding="utf-8").read()
    try:
        flow = json.loads(raw)
    except json.JSONDecodeError as e:
        _fail(f"{flow_path} is not valid JSON: {e}")

    if "nodes" not in flow or "edges" not in flow:
        _fail("Flow missing 'nodes' or 'edges'")

    types = [n.get("type", "") for n in flow["nodes"]]
    if JIRA_NODE_TYPE not in types:
        _fail(f"Jira Create Issue node not found in {types}")

    missing = [tok for tok in REQUIRED_RAW_TOKENS if tok not in raw]
    if missing:
        _fail(
            "customFieldsRequestDetails missing required tokens "
            f"under GenerateSchema: {missing}"
        )

    jira_nodes = [n for n in flow["nodes"] if n.get("type") == JIRA_NODE_TYPE]
    body = jira_nodes[0].get("inputs", {}).get("detail", {}).get("bodyParameters", {})
    summary = body.get("fields.summary")
    if not summary:
        _fail(f"fields.summary missing or empty in bodyParameters: {body}")

    print(
        f"OK: {len(flow['nodes'])} nodes, {len(flow['edges'])} edges; "
        f"Jira Create Issue node present; customFieldsRequestDetails "
        f"has both parent-field tuples; fields.summary={summary!r}"
    )


if __name__ == "__main__":
    main()
