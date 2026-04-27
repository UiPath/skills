#!/usr/bin/env python3
"""Inline agent + solution API workflow tool check.

Validates:
  1. Flow has a `uipath.agent.autonomous` node whose `model.source`
     resolves to an existing UUID subdirectory.
  2. Flow has a `uipath.agent.resource.tool.*` node for the API workflow
     (exact suffix under-asserted — use prefix match).
  3. Edge wires the autonomous node's `tool` handle (source) to the
     tool node's `input` handle (target).
  4. Inside the inline agent dir, `resources/CalculateShippingRate/resource.json`
     declares a solution-internal API workflow tool:
       - $resourceType == "tool"
       - type == "api"
       - location == "solution"
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

FLOW_PATH = Path(os.getcwd()) / "ShippingFlowSol" / "ShippingFlow" / "ShippingFlow.flow"
TOOL_NODE_PREFIX = "uipath.agent.resource.tool."


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
    print("OK: agent 'tool' handle is wired to API workflow tool node's 'input' handle")

    agent_dir = resolve_inline_agent_dir(FLOW_PATH, agent_node)
    resource_path = agent_dir / "resources" / "CalculateShippingRate" / "resource.json"
    resource = load_json(resource_path)

    expected = {
        "$resourceType": "tool",
        "type": "api",
        "location": "solution",
    }
    for key, want in expected.items():
        if resource.get(key) != want:
            sys.exit(f"FAIL: {resource_path} {key!r} should be {want!r}, got {resource.get(key)!r}")
    print(
        f'OK: {resource_path.relative_to(Path(os.getcwd()))} is '
        f'$resourceType="tool", type="api", location="solution"'
    )

    props = resource.get("properties") or {}
    if props.get("folderPath") != "solution_folder":
        sys.exit(f'FAIL: properties.folderPath should be "solution_folder", got {props.get("folderPath")!r}')
    print('OK: properties.folderPath="solution_folder"')


if __name__ == "__main__":
    main()
