#!/usr/bin/env python3
"""Inline agent + external agent-as-tool check.

Validates:
  1. Flow has a `uipath.agent.autonomous` node and a
     `uipath.agent.resource.tool.agent.*` node (per-agent suffix).
  2. Edge wires agent.tool -> tool.input.
  3. Inline agent dir has at least one resource.json under
     `resources/**/` (UUID-named per inline-in-flow.md) for a
     "SupportExpert" external agent-as-tool with:
       - $resourceType == "tool"
       - type == "agent"
       - location == "external"
       - properties.processName == "SupportExpert"
       - properties.folderPath is a real path (NOT "solution_folder")
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.inline_wiring import (  # noqa: E402
    assert_edge,
    find_autonomous_agent_node,
    find_inline_resource,
    find_resource_node,
    load_json,
    resolve_inline_agent_dir,
)

FLOW_PATH = Path(os.getcwd()) / "RouterFlowSol" / "RouterFlow" / "RouterFlow.flow"
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
    print("OK: agent 'tool' handle is wired to external agent-as-tool node's 'input' handle")

    agent_dir = resolve_inline_agent_dir(FLOW_PATH, agent_node)
    resource_path, resource = find_inline_resource(
        agent_dir,
        lambda d: (
            d.get("$resourceType") == "tool"
            and d.get("type") == "agent"
            and d.get("location") == "external"
            and (d.get("properties") or {}).get("processName") == "SupportExpert"
        ),
        description='external agent-as-tool "SupportExpert"',
    )
    print(
        f'OK: {resource_path.relative_to(Path(os.getcwd()))} is '
        f'$resourceType="tool", type="agent", location="external"'
    )

    props = resource.get("properties") or {}
    fpath = props.get("folderPath")
    if not isinstance(fpath, str) or not fpath.strip():
        sys.exit(f"FAIL: properties.folderPath must be a non-empty string, got {fpath!r}")
    if fpath == "solution_folder":
        sys.exit(
            'FAIL: properties.folderPath is "solution_folder", which is only '
            'valid for location=="solution". External agent tools require a '
            'real Orchestrator folder path like "Shared".'
        )
    print(f'OK: properties.processName="SupportExpert", folderPath={fpath!r} (not "solution_folder")')


if __name__ == "__main__":
    main()
