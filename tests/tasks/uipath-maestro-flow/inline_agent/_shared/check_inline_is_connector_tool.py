#!/usr/bin/env python3
"""Inline-agent Integration Service (IS) connector tool check.

Design-time checks only — this script does NOT invoke the connector.

Combines the F8 (standalone IS tool) resource-shape assertions with
the F2 (inline agent) flow-wiring assertions. Specifically:

  1. The flow file contains a `uipath.agent.autonomous` node whose
     `inputs.source` points at the inline agent's UUID subdirectory.
  2. The flow file contains a `uipath.agent.resource.tool.connector`
     node.
  3. An edge wires the agent's `tool` handle (source) to the connector
     node's `input` handle (target), per the flow-integration spec.
  4. Inside the inline agent's subdirectory, at least one resource.json
     under `resources/` declares an IS tool (`$resourceType=tool`,
     `type=integration`). Other `properties` fields are intentionally
     under-asserted until the canonical shape locks in.
  5. A `bindings_v2.json` under the flow project (outside
     `.agent-builder/`) carries a `connection` binding for the connector
     the tool node uses, with a non-empty `ConnectionId`. That binding is
     what `uip solution pack` and `uip maestro flow debug` read the
     connection from.

The solution-level `resources/solution_folder/connection/*.json` file is
NOT required. Pack and debug each run a resource refresh themselves and
write that file (byte-identical to a manual `uip solution resources
refresh`), so it is an upload-side artifact. The task forbids upload, so
an author who skips the manual refresh is correct. Measured 2026-10-05 on
alpha: debug of a copy without the folder completed and the web-search
tool ran; pack emitted the connection file.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.inline_wiring import find_inline_resource  # noqa: E402

INLINE_AGENT_NODE_TYPE = "uipath.agent.autonomous"
# Connector tool nodes carry the connector-key + activity in the type suffix
# (e.g. `uipath.agent.resource.tool.connector.uipath-slack.send-message`),
# so match on the prefix. Trailing "." disambiguates from any future bare type.
CONNECTOR_TOOL_NODE_TYPE_PREFIX = "uipath.agent.resource.tool.connector."

SOLUTION = Path(os.getcwd()) / "ResearchFlowSol"
FLOW_PROJECT = SOLUTION / "ResearchFlow"
FLOW_PATH = FLOW_PROJECT / "ResearchFlow.flow"


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

    connector_nodes = [
        n for n in nodes
        if isinstance(n.get("type"), str)
        and n["type"].startswith(CONNECTOR_TOOL_NODE_TYPE_PREFIX)
    ]
    if not connector_nodes:
        sys.exit(
            f"FAIL: flow has no node with type starting with "
            f"{CONNECTOR_TOOL_NODE_TYPE_PREFIX!r} — the IS connector tool was "
            "not added to the flow canvas"
        )
    connector_node = connector_nodes[0]

    if not agent_node.get("id"):
        sys.exit(f"FAIL: {INLINE_AGENT_NODE_TYPE} node has no id")
    if not connector_node.get("id"):
        sys.exit(f"FAIL: connector tool node has no id")

    print(
        f"OK: flow has {INLINE_AGENT_NODE_TYPE!r} and connector tool node "
        f"{connector_node['type']!r}"
    )
    return agent_node, connector_node


def assert_agent_source_dir(agent_node: dict) -> Path:
    inputs = agent_node.get("inputs") or {}
    source = inputs.get("source")
    if not isinstance(source, str) or not source:
        sys.exit(
            f"FAIL: {INLINE_AGENT_NODE_TYPE} node has no inputs.source"
        )
    agent_dir = FLOW_PATH.parent / source
    if not agent_dir.is_dir():
        sys.exit(
            f"FAIL: inputs.source {source!r} does not point to an existing "
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
    path, data = find_inline_resource(
        agent_dir,
        lambda d: d.get("$resourceType") == "tool" and d.get("type") == "integration",
        description='IS tool ($resourceType=="tool", type=="integration")',
    )
    rid = data.get("id")
    if not isinstance(rid, str) or "-" not in rid:
        sys.exit(f"FAIL: IS tool id missing or malformed at {path}: {rid!r}")
    if not data.get("isEnabled"):
        sys.exit(f"FAIL: IS tool isEnabled must be truthy at {path}")
    print(
        f'OK: {path.relative_to(SOLUTION.parent)} is $resourceType="tool", '
        f'type="integration" (id={rid})'
    )


def assert_connection_binding(connector_node: dict) -> None:
    candidates = sorted(FLOW_PROJECT.rglob("bindings_v2.json"))
    authored = [p for p in candidates if ".agent-builder" not in p.parts]
    if not authored:
        sys.exit(
            f"FAIL: no bindings_v2.json under {FLOW_PROJECT} (outside "
            ".agent-builder/) — the connector tool's connection is bound nowhere."
        )
    node_type = connector_node.get("type", "")
    for path in authored:
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            sys.exit(f"FAIL: {path} is not valid JSON: {e}")
        resources = data.get("resources") if isinstance(data, dict) else None
        for r in resources or []:
            if not isinstance(r, dict) or r.get("resource") != "connection":
                continue
            connector = (r.get("metadata") or {}).get("Connector") or ""
            conn_id = ((r.get("value") or {}).get("ConnectionId") or {}).get("defaultValue")
            if connector and f".{connector}." in f"{node_type}." and isinstance(conn_id, str) and conn_id.strip():
                print(
                    f"OK: {path.relative_to(SOLUTION.parent)} binds connector "
                    f"{connector!r} to connection {conn_id!r}"
                )
                return
    sys.exit(
        f"FAIL: no bindings_v2.json connection binding matches the tool node "
        f"{node_type!r} (need resource=connection, metadata.Connector = the "
        "node's connector key, non-empty value.ConnectionId.defaultValue)"
    )


def main() -> None:
    if not SOLUTION.is_dir():
        sys.exit(f"FAIL: Solution directory {SOLUTION} does not exist")
    flow = load(FLOW_PATH)

    agent_node, connector_node = assert_agent_and_connector_nodes(flow)
    agent_dir = assert_agent_source_dir(agent_node)
    assert_tool_edge(flow, agent_node["id"], connector_node["id"])
    assert_integration_tool_resource(agent_dir)
    assert_connection_binding(connector_node)


if __name__ == "__main__":
    main()
