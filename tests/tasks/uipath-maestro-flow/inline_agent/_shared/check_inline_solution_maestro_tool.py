#!/usr/bin/env python3
"""Inline agent + solution Maestro (processOrchestration) tool check.

Validates:
  1. Flow has a `uipath.agent.autonomous` node and a
     `uipath.agent.resource.tool.*` node (exact Maestro suffix
     under-asserted — use prefix match).
  2. Edge wires agent.tool -> tool.input.
  3. Inline agent dir has at least one resource.json under
     `resources/**/` (UUID-named per inline-in-flow.md) for an
     "EmployeeOnboarding" solution Maestro tool with:
       - $resourceType == "tool"
       - type == "processOrchestration"
       - location == "solution"
       - properties.folderPath in ("", "solution_folder")

`folderPath` accepts the builder-SDK's "" (what `uip agent validate
--inline-in-flow` accepts) as well as "solution_folder"; both derive identical
solution files and the "" shape ran its tool live:
https://github.com/UiPath/flow-builder-sdk/issues/922#issuecomment-6000881513
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.inline_wiring import (  # noqa: E402
    INLINE_SOLUTION_FOLDER_PATHS,
    assert_edge,
    find_autonomous_agent_node,
    find_inline_resource,
    find_resource_node,
    load_json,
    resolve_inline_agent_dir,
)

FLOW_PATH = Path(os.getcwd()) / "OnboardingFlowSol" / "OnboardingFlow" / "OnboardingFlow.flow"
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
    print("OK: agent 'tool' handle is wired to Maestro tool node's 'input' handle")

    agent_dir = resolve_inline_agent_dir(FLOW_PATH, agent_node)
    resource_path, resource = find_inline_resource(
        agent_dir,
        lambda d: (
            d.get("$resourceType") == "tool"
            and d.get("type") == "processOrchestration"
            and d.get("location") == "solution"
            and d.get("name") == "EmployeeOnboarding"
        ),
        description='solution Maestro tool "EmployeeOnboarding"',
    )
    print(
        f'OK: {resource_path.relative_to(Path(os.getcwd()))} is '
        f'$resourceType="tool", type="processOrchestration", location="solution"'
    )

    props = resource.get("properties") or {}
    if props.get("folderPath") not in INLINE_SOLUTION_FOLDER_PATHS:
        sys.exit(f'FAIL: properties.folderPath should be "" or "solution_folder", got {props.get("folderPath")!r}')
    print('OK: properties.folderPath=' + repr(props.get("folderPath")))


if __name__ == "__main__":
    main()
