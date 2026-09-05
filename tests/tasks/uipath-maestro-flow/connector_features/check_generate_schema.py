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

import json
import os
import sys
from pathlib import Path
from typing import Any

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-maestro-flow")
    if os.environ.get("SKILLS_REPO_PATH")
    else str(Path(__file__).resolve().parents[1])
)
sys.path.insert(0, _shared_root)
from _shared.flow_check import find_flow_file  # noqa: E402

JIRA_NODE_TYPE = "uipath.connector.uipath-atlassian-jira.create-issue"
REQUIRED_PARENT_FIELDS = (
    "fields_sub_project_sub_key",
    "fields_sub_issuetype_sub_id",
)


def _fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def _parse_configuration(detail: dict[str, Any]) -> dict[str, Any]:
    configuration = detail.get("configuration")
    if isinstance(configuration, str) and configuration.startswith("=jsonString:"):
        try:
            configuration = json.loads(configuration.removeprefix("=jsonString:"))
        except json.JSONDecodeError as exc:
            _fail(f"Jira configuration is not valid embedded JSON: {exc}")
    if not isinstance(configuration, dict):
        _fail("Jira configuration is missing")
    return configuration


def _generate_schema_values(detail: dict[str, Any]) -> dict[str, Any]:
    configuration = _parse_configuration(detail)
    essential = configuration.get("essentialConfiguration")
    if not isinstance(essential, dict):
        _fail("Jira configuration missing essentialConfiguration")
    request = essential.get("customFieldsRequestDetails")
    if (
        not isinstance(request, dict)
        or request.get("objectActionName") != "GenerateSchema"
    ):
        _fail("Jira configuration missing GenerateSchema customFieldsRequestDetails")
    values = request.get("parameterValues")
    if not isinstance(values, list):
        _fail("GenerateSchema customFieldsRequestDetails missing parameterValues")
    return {
        entry[0]: entry[1]
        for entry in values
        if isinstance(entry, list) and len(entry) == 2
    }


def main() -> None:
    flow_path = find_flow_file()
    try:
        with open(flow_path, encoding="utf-8") as source:
            flow = json.load(source)
    except json.JSONDecodeError as e:
        _fail(f"{flow_path} is not valid JSON: {e}")

    if not isinstance(flow, dict):
        _fail("Flow root must be a JSON object")
    if not isinstance(flow.get("nodes"), list) or not isinstance(
        flow.get("edges"), list
    ):
        _fail("Flow missing 'nodes' or 'edges'")

    nodes = [node for node in flow["nodes"] if isinstance(node, dict)]
    types = [node.get("type", "") for node in nodes]
    if JIRA_NODE_TYPE not in types:
        _fail(f"Jira Create Issue node not found in {types}")

    jira_node = next(node for node in nodes if node.get("type") == JIRA_NODE_TYPE)
    detail = jira_node.get("inputs", {}).get("detail", {})
    if not isinstance(detail, dict):
        _fail("Jira node inputs.detail must be an object")
    values = _generate_schema_values(detail)
    missing = [field for field in REQUIRED_PARENT_FIELDS if not values.get(field)]
    if missing:
        _fail(f"GenerateSchema parameterValues missing parent values: {missing}")

    body = detail.get("bodyParameters", {})
    if not isinstance(body, dict):
        _fail("Jira bodyParameters must be an object")
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
