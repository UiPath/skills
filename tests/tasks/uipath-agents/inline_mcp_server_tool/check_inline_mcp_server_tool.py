#!/usr/bin/env python3
"""Inline agent + MCP server resource check.

Validates:
  1. Flow has a `uipath.agent.autonomous` node and a
     `uipath.agent.resource.mcp.*` node (suffix documented as wildcard
     in agent-flow-integration.md).
  2. Edge wires agent.tool -> mcp.input. (The `tool` handle is the
     only agent-side handle documented for non-context / non-escalation
     resources; MCP uses it per convention.)
  3. Inline agent dir has `resources/GitHubMcp/resource.json` with the
     documented sparse shape:
       - $resourceType == "mcp"  (not "tool")
       - name == "GitHubMcp"
       - description is non-empty
       - isEnabled is truthy
       - id is a UUID-shaped string
       - tools is a list (may be empty — populated at runtime)
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

FLOW_PATH = Path(os.getcwd()) / "DevToolsFlowSol" / "DevToolsFlow" / "DevToolsFlow.flow"
MCP_NODE_PREFIX = "uipath.agent.resource.mcp."


def main() -> None:
    flow = load_json(FLOW_PATH)
    agent_node = find_autonomous_agent_node(flow)
    mcp_node = find_resource_node(flow, node_type_prefix=MCP_NODE_PREFIX)
    print(f"OK: flow has {agent_node['type']} and {mcp_node['type']} nodes")

    assert_edge(
        flow,
        source_id=agent_node["id"],
        source_port="tool",
        target_id=mcp_node["id"],
        target_port="input",
    )
    print("OK: agent 'tool' handle is wired to MCP server node's 'input' handle")

    agent_dir = resolve_inline_agent_dir(FLOW_PATH, agent_node)
    resource_path = agent_dir / "resources" / "GitHubMcp" / "resource.json"
    resource = load_json(resource_path)

    if resource.get("$resourceType") != "mcp":
        sys.exit(
            f'FAIL: {resource_path} $resourceType should be "mcp" '
            f'(distinct from "tool"), got {resource.get("$resourceType")!r}'
        )
    if resource.get("name") != "GitHubMcp":
        sys.exit(f'FAIL: MCP resource name should be "GitHubMcp", got {resource.get("name")!r}')
    description = resource.get("description")
    if not isinstance(description, str) or not description.strip():
        sys.exit(f"FAIL: MCP resource description missing or empty: {description!r}")
    if not resource.get("isEnabled"):
        sys.exit(f"FAIL: MCP resource isEnabled must be truthy, got {resource.get('isEnabled')!r}")
    rid = resource.get("id")
    if not isinstance(rid, str) or "-" not in rid:
        sys.exit(f"FAIL: MCP resource id missing or malformed: {rid!r}")
    tools = resource.get("tools")
    if not isinstance(tools, list):
        sys.exit(f"FAIL: MCP resource tools must be a list, got {tools!r}")
    print(
        f'OK: {resource_path.relative_to(Path(os.getcwd()))} is '
        f'$resourceType="mcp", name="GitHubMcp", id={rid}, isEnabled=true, '
        f'tools list present ({len(tools)} entries)'
    )


if __name__ == "__main__":
    main()
