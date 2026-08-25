#!/usr/bin/env python3
"""Inline agent + built-in tool check.

Validates:
  1. Flow has a `uipath.agent.autonomous` node whose `inputs.source`
     matches the sub-folder UUID of the inline agent under the flow
     project.
  2. Flow has a `uipath.agent.resource.tool.builtin.<key>` node whose
     `inputs.source` matches the sub-folder UUID of the inline agent's
     resource (under `<inline-agent-uuid>/resources/`).
  3. Edge wires agent.tool -> tool.input.
  4. Every internal tool resource.json under the inline agent's
     resources/ tree matches the built-in tool registry:
       - $resourceType == "tool"
       - type == "internal"
       - referenceKey is null
       - properties.toolType in {analyze-attachments, load-attachments,
                                 deep-rag, batch-transform}
  5. The resource wired to the flow node is the "Analyze Files"
     built-in (toolType == "analyze-attachments" — the specific
     built-in the prompt requested).
"""

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.inline_wiring import (  # noqa: E402
    assert_edge,
    find_autonomous_agent_node,
    find_inline_resource,
    find_resource_node,
    load_json,
    resolve_inline_agent_dir,
    resolve_resource_source,
)

FLOW_PATH = Path(os.getcwd()) / "DocsFlowSol" / "DocsFlow" / "DocsFlow.flow"
BUILTIN_TOOL_NODE_TYPE_PREFIX = "uipath.agent.resource.tool.builtin."
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

EXPECTED_TOOL_TYPE = "analyze-attachments"
BUILTIN_TOOL_TYPES = {
    "analyze-attachments",
    "load-attachments",
    "deep-rag",
    "batch-transform",
}


def main() -> None:
    flow = load_json(FLOW_PATH)
    agent_node = find_autonomous_agent_node(flow)
    tool_node = find_resource_node(flow, node_type_prefix=BUILTIN_TOOL_NODE_TYPE_PREFIX)
    print(f"OK: flow has {agent_node['type']} and {tool_node['type']} nodes")

    agent_source = (agent_node.get("inputs") or {}).get("source")
    if not isinstance(agent_source, str) or not UUID_RE.match(agent_source):
        sys.exit(
            f"FAIL: {agent_node['type']} inputs.source must be a UUID matching "
            f"the inline agent's sub-folder name, got {agent_source!r}"
        )
    agent_dir = resolve_inline_agent_dir(FLOW_PATH, agent_node)
    if agent_dir.name != agent_source:
        sys.exit(
            f"FAIL: inputs.source UUID {agent_source!r} does not match "
            f"the inline agent sub-folder name {agent_dir.name!r}"
        )
    print(f"OK: autonomous node inputs.source={agent_source!r} matches inline agent sub-folder")

    tool_source = resolve_resource_source(tool_node)
    if not UUID_RE.match(tool_source):
        sys.exit(
            f"FAIL: {tool_node['type']} inputs.source must be a UUID matching "
            f"the inline agent resource's sub-folder name, got {tool_source!r}"
        )

    assert_edge(
        flow,
        source_id=agent_node["id"],
        source_port="tool",
        target_id=tool_node["id"],
        target_port="input",
    )
    print("OK: agent 'tool' handle is wired to built-in tool node's 'input' handle")

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

    resource_path, _resource = find_inline_resource(
        agent_dir,
        lambda d: (
            d.get("$resourceType") == "tool"
            and d.get("type") == "internal"
            and (d.get("properties") or {}).get("toolType") == EXPECTED_TOOL_TYPE
        ),
        description=f'built-in "Analyze Files" tool (toolType={EXPECTED_TOOL_TYPE!r})',
    )
    if resource_path.parent.name != tool_source:
        sys.exit(
            f"FAIL: tool node inputs.source UUID {tool_source!r} does not match "
            f"the resource sub-folder name {resource_path.parent.name!r}"
        )
    print(
        f"OK: tool node inputs.source={tool_source!r} matches resource sub-folder "
        f"({resource_path.relative_to(Path(os.getcwd()))})"
    )
    print(f'OK: "Analyze Files" (toolType={EXPECTED_TOOL_TYPE!r}) is enabled and wired in the flow')


if __name__ == "__main__":
    main()
