#!/usr/bin/env python3
"""Inline agent + solution agent-as-tool check.

Validates:
  1. Flow has a `uipath.agent.autonomous` node and a
     `uipath.agent.resource.tool.agent.*` node (per-agent suffix).
  2. Edge wires agent.tool -> tool.input.
  3. Inline agent dir has `resources/ToolAgent/resource.json` with:
       - $resourceType == "tool"
       - type == "agent"
       - location == "solution"
       - properties.processName == "ToolAgent"
       - properties.folderPath == "solution_folder"
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.inline_wiring import (  # noqa: E402
    assert_edge,
    find_autonomous_agent_node,
    find_resource_node,
    load_json,
    resolve_inline_agent_dir,
)

FLOW_PATH = Path(os.getcwd()) / "OrchestratorFlowSol" / "OrchestratorFlow" / "OrchestratorFlow.flow"
AGENT_TOOL_NODE_PREFIX = "uipath.agent.resource.tool.agent."


def main() -> None:
    flow = load_json(FLOW_PATH)
    agent_node = find_autonomous_agent_node(flow)
    tool_node = find_resource_node(flow, node_type_prefix=AGENT_TOOL_NODE_PREFIX)
    print(f"OK: flow has {agent_node['type']} and {tool_node['type']} nodes")

    assert_edge(
        flow,
        source_id=agent_node["id"],
        source_port="tool",
        target_id=tool_node["id"],
        target_port="input",
    )
    print("OK: agent 'tool' handle is wired to agent-as-tool node's 'input' handle")

    agent_dir = resolve_inline_agent_dir(FLOW_PATH, agent_node)
    resource_path = agent_dir / "resources" / "ToolAgent" / "resource.json"
    resource = load_json(resource_path)

    expected = {
        "$resourceType": "tool",
        "type": "agent",
        "location": "solution",
    }
    for key, want in expected.items():
        if resource.get(key) != want:
            sys.exit(f"FAIL: {resource_path} {key!r} should be {want!r}, got {resource.get(key)!r}")
    print(
        f'OK: {resource_path.relative_to(Path(os.getcwd()))} is '
        f'$resourceType="tool", type="agent", location="solution"'
    )

    props = resource.get("properties") or {}
    if props.get("processName") != "ToolAgent":
        sys.exit(f'FAIL: properties.processName should be "ToolAgent", got {props.get("processName")!r}')
    if props.get("folderPath") != "solution_folder":
        sys.exit(f'FAIL: properties.folderPath should be "solution_folder", got {props.get("folderPath")!r}')
    print('OK: properties.processName="ToolAgent", folderPath="solution_folder"')


if __name__ == "__main__":
    main()
