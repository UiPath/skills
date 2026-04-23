#!/usr/bin/env python3
"""Inline-agent Integration Service (IS) connector tool check.

Design-time checks only — this script does NOT invoke the connector.

Combines the F8 (standalone IS tool) resource-shape assertions with
the F2 (inline agent) flow-wiring assertions. Specifically:

  1. The flow file contains a `uipath.agent.autonomous` node whose
     `model.source` points at the inline agent's UUID subdirectory.
  2. The flow file contains a `uipath.agent.resource.tool.connector`
     node.
  3. An edge wires the agent's `tool` handle (source) to the connector
     node's `input` handle (target), per the flow-integration spec.
  4. Inside the inline agent's subdirectory, at least one resource.json
     under `resources/` declares an IS tool (`$resourceType=tool`,
     `type=integration`). Other `properties` fields are intentionally
     under-asserted until the canonical shape locks in.
  5. At least one `bindings_v2.json` was authored somewhere under the
     flow project (outside `.agent-builder/`). The agent creates this
     manually as the source for `uip solution resource refresh`. Shape
     under-asserted for now — we just verify presence and valid JSON.
  6. After refresh, at least one connection resource file exists under
     `ResearchFlowSol/resources/solution_folder/connection/`.
"""

import json
import os
import sys
from pathlib import Path

INLINE_AGENT_NODE_TYPE = "uipath.agent.autonomous"
CONNECTOR_TOOL_NODE_TYPE = "uipath.agent.resource.tool.connector"

SOLUTION = Path(os.getcwd()) / "ResearchFlowSol"
FLOW_PROJECT = SOLUTION / "ResearchFlow"
FLOW_PATH = FLOW_PROJECT / "ResearchFlow.flow"
CONNECTION_DIR = SOLUTION / "resources" / "solution_folder" / "connection"


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def assert_agent_and_connector_nodes(flow: dict) -> tuple:
    nodes = flow.get("nodes") or []
    agent_nodes = [n for n in nodes if n.get("type") == INLINE_AGENT_NODE_TYPE]
    if not agent_nodes:
        sys.exit(
            f"FAIL: flow has no node of type {INLINE_AGENT_NODE_TYPE!r}"
        )
    agent_node = agent_nodes[0]

    connector_nodes = [n for n in nodes if n.get("type") == CONNECTOR_TOOL_NODE_TYPE]
    if not connector_nodes:
        sys.exit(
            f"FAIL: flow has no node of type {CONNECTOR_TOOL_NODE_TYPE!r} — "
            "the IS connector tool was not added to the flow canvas"
        )
    connector_node = connector_nodes[0]

    if not agent_node.get("id"):
        sys.exit(f"FAIL: {INLINE_AGENT_NODE_TYPE} node has no id")
    if not connector_node.get("id"):
        sys.exit(f"FAIL: {CONNECTOR_TOOL_NODE_TYPE} node has no id")

    print(f"OK: flow has both {INLINE_AGENT_NODE_TYPE!r} and {CONNECTOR_TOOL_NODE_TYPE!r} nodes")
    return agent_node, connector_node


def assert_agent_source_dir(agent_node: dict) -> Path:
    source = (agent_node.get("model") or {}).get("source")
    if not source:
        sys.exit(f"FAIL: {INLINE_AGENT_NODE_TYPE} node has no model.source")
    agent_dir = FLOW_PATH.parent / source
    if not agent_dir.is_dir():
        sys.exit(
            f"FAIL: model.source {source!r} does not point to an existing "
            f"directory ({agent_dir})"
        )
    print(f"OK: inline agent directory resolves to {agent_dir.name}")
    return agent_dir


def assert_tool_edge(flow: dict, agent_id: str, connector_id: str) -> None:
    edges = flow.get("edges") or []
    matching = [
        e for e in edges
        if e.get("sourceNodeId") == agent_id
        and e.get("sourcePort") == "tool"
        and e.get("targetNodeId") == connector_id
        and e.get("targetPort") == "input"
    ]
    if not matching:
        sys.exit(
            "FAIL: no edge wires the agent's 'tool' handle (source) to the "
            "connector node's 'input' handle (target). Expected an edge with "
            f"sourceNodeId={agent_id!r}, sourcePort='tool', "
            f"targetNodeId={connector_id!r}, targetPort='input'."
        )
    print("OK: agent 'tool' handle is wired to connector node's 'input' handle")


def assert_integration_tool_resource(agent_dir: Path) -> None:
    resources_dir = agent_dir / "resources"
    if not resources_dir.is_dir():
        sys.exit(
            f"FAIL: {resources_dir} does not exist — the inline agent has no "
            "resources/ directory, so no IS tool resource.json was authored"
        )
    for path in sorted(resources_dir.rglob("resource.json")):
        data = load(path)
        if data.get("$resourceType") == "tool" and data.get("type") == "integration":
            rid = data.get("id")
            if not isinstance(rid, str) or "-" not in rid:
                sys.exit(f"FAIL: IS tool id missing or malformed at {path}: {rid!r}")
            if not data.get("isEnabled"):
                sys.exit(f"FAIL: IS tool isEnabled must be truthy at {path}")
            print(
                f'OK: {path.relative_to(SOLUTION.parent)} is $resourceType="tool", '
                f'type="integration" (id={rid})'
            )
            return
    sys.exit(
        f"FAIL: no IS tool resource found under {resources_dir} — "
        'expected at least one resource.json with $resourceType="tool" '
        'and type="integration"'
    )


def assert_bindings_v2_authored() -> None:
    candidates = sorted(FLOW_PROJECT.rglob("bindings_v2.json"))
    authored = [p for p in candidates if ".agent-builder" not in p.parts]
    if not authored:
        sys.exit(
            f"FAIL: no bindings_v2.json authored under {FLOW_PROJECT} (outside "
            ".agent-builder/). Agent must create it manually as the source "
            "for `uip solution resource refresh`."
        )
    path = authored[0]
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")
    if not isinstance(data, (dict, list)):
        sys.exit(f"FAIL: {path} root is neither object nor array: {type(data).__name__}")
    print(f"OK: bindings_v2.json authored at {path.relative_to(SOLUTION.parent)}")


def assert_connection_provisioned() -> None:
    if not CONNECTION_DIR.is_dir():
        sys.exit(
            f"FAIL: {CONNECTION_DIR} does not exist — `uip solution resource "
            "refresh` did not provision a connection resource under "
            "resources/solution_folder/connection/"
        )
    connection_files = [p for p in CONNECTION_DIR.rglob("*.json") if p.is_file()]
    if not connection_files:
        sys.exit(
            f"FAIL: {CONNECTION_DIR} is empty — refresh did not drop any "
            "connection resource JSON files"
        )
    print(
        f"OK: found {len(connection_files)} connection resource file(s) under "
        f"resources/solution_folder/connection/"
    )


def main() -> None:
    if not SOLUTION.is_dir():
        sys.exit(f"FAIL: Solution directory {SOLUTION} does not exist")
    flow = load(FLOW_PATH)

    agent_node, connector_node = assert_agent_and_connector_nodes(flow)
    agent_dir = assert_agent_source_dir(agent_node)
    assert_tool_edge(flow, agent_node["id"], connector_node["id"])
    assert_integration_tool_resource(agent_dir)
    assert_bindings_v2_authored()
    assert_connection_provisioned()


if __name__ == "__main__":
    main()
