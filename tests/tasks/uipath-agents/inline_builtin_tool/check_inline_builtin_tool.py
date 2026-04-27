#!/usr/bin/env python3
"""Inline agent + built-in tool check.

Validates:
  1. Flow has a `uipath.agent.autonomous` node and a
     `uipath.agent.resource.tool.*` node (exact built-in suffix
     under-asserted — use prefix match).
  2. Edge wires agent.tool -> tool.input.
  3. Inline agent dir has at least one resource.json under its
     resources/ tree matching the built-in tool registry:
       - $resourceType == "tool"
       - type == "internal"
       - referenceKey is null
       - properties.toolType in {analyze-attachments, load-attachments,
                                 deep-rag, batch-transform}
     and at least one of them has toolType == "analyze-attachments"
     (the specific built-in the prompt requested).
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

FLOW_PATH = Path(os.getcwd()) / "DocsFlowSol" / "DocsFlow" / "DocsFlow.flow"
TOOL_NODE_PREFIX = "uipath.agent.resource.tool."
BUILTIN_TOOL_TYPES = {
    "analyze-attachments",
    "load-attachments",
    "deep-rag",
    "batch-transform",
}


def main() -> None:
    flow = load_json(FLOW_PATH)
    agent_node = find_autonomous_agent_node(flow)
    tool_node = find_resource_node(flow, node_type_prefix=TOOL_NODE_PREFIX)
    print(f"OK: flow has {agent_node['type']} and {tool_node['type']} nodes")

    assert_edge(
        flow,
        source_id=agent_node["id"],
        source_port="tool",
        target_id=tool_node["id"],
        target_port="input",
    )
    print("OK: agent 'tool' handle is wired to built-in tool node's 'input' handle")

    agent_dir = resolve_inline_agent_dir(FLOW_PATH, agent_node)
    resources_dir = agent_dir / "resources"
    if not resources_dir.is_dir():
        sys.exit(f"FAIL: {resources_dir} does not exist — no resources/ directory")

    seen_tool_types = []
    for path in sorted(resources_dir.rglob("resource.json")):
        data = load_json(path)
        if data.get("$resourceType") != "tool" or data.get("type") != "internal":
            continue
        if data.get("referenceKey") is not None:
            sys.exit(f"FAIL: {path} referenceKey should be null for a built-in tool, got {data.get('referenceKey')!r}")
        props = data.get("properties") or {}
        tool_type = props.get("toolType")
        if tool_type not in BUILTIN_TOOL_TYPES:
            sys.exit(
                f"FAIL: {path} properties.toolType must be one of "
                f"{sorted(BUILTIN_TOOL_TYPES)}, got {tool_type!r}"
            )
        seen_tool_types.append(tool_type)
        print(f"OK: {path.parent.name} is a built-in tool with toolType={tool_type!r}")

    if not seen_tool_types:
        sys.exit(
            f"FAIL: no built-in tool resources found under {resources_dir} — "
            'expected at least one resource.json with $resourceType="tool" '
            'and type="internal"'
        )
    if "analyze-attachments" not in seen_tool_types:
        sys.exit(
            f'FAIL: prompt asked for "Analyze Files" (toolType '
            f'"analyze-attachments"), but it was not enabled. '
            f'Got toolTypes: {seen_tool_types}'
        )
    print('OK: "Analyze Files" (toolType="analyze-attachments") is enabled on the inline agent')


if __name__ == "__main__":
    main()
