#!/usr/bin/env python3
"""Inline agent + external Maestro (processOrchestration) tool check.

Validates:
  1. Flow has a `uipath.agent.autonomous` node whose `inputs.source`
     matches the sub-folder UUID of the inline agent under the flow
     project.
  2. Flow has a `uipath.agent.resource.tool.processorchestration.<uuid>`
     node whose `inputs.source` matches the sub-folder UUID of the
     inline agent's resource (under `<inline-agent-uuid>/resources/`).
  3. Edge wires agent.tool -> tool.input.
  4. Inline agent dir has at least one resource.json under
     `resources/**/` (UUID-named per inline-in-flow.md) for the
     "ProcurementProcess" external Maestro tool with:
       - $resourceType == "tool"
       - type == "processOrchestration"
       - location == "external"
       - properties.processName == "ProcurementProcess"
       - properties.folderPath == "Shared/uipath-agents/ProcurementProcess"
       - referenceKey is a UUID-shaped non-empty string (copied from
         `uip solution resources list`'s `Key`)
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

FLOW_PATH = Path(os.getcwd()) / "ProcurementFlowSol" / "ProcurementFlow" / "ProcurementFlow.flow"
MAESTRO_TOOL_NODE_TYPE_PREFIX = "uipath.agent.resource.tool.processorchestration."
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

EXPECTED_PROCESS_NAME = "ProcurementProcess"
EXPECTED_FOLDER_PATH = "Shared/uipath-agents/ProcurementProcess"


def main() -> None:
    flow = load_json(FLOW_PATH)
    agent_node = find_autonomous_agent_node(flow)
    tool_node = find_resource_node(flow, node_type_prefix=MAESTRO_TOOL_NODE_TYPE_PREFIX)
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
    print("OK: agent 'tool' handle is wired to external Maestro tool node's 'input' handle")

    resource_path, resource = find_inline_resource(
        agent_dir,
        lambda d: (
            d.get("$resourceType") == "tool"
            and d.get("type") == "processOrchestration"
            and d.get("location") == "external"
            and (d.get("properties") or {}).get("processName") == EXPECTED_PROCESS_NAME
        ),
        description=f'external Maestro tool "{EXPECTED_PROCESS_NAME}"',
    )
    if resource_path.parent.name != tool_source:
        sys.exit(
            f"FAIL: tool inputs.source UUID {tool_source!r} does not match "
            f"the resource sub-folder name {resource_path.parent.name!r}"
        )
    print(
        f"OK: tool node inputs.source={tool_source!r} matches resource sub-folder "
        f"({resource_path.relative_to(Path(os.getcwd()))})"
    )
    print(
        f'OK: {resource_path.relative_to(Path(os.getcwd()))} is '
        f'$resourceType="tool", type="processOrchestration", location="external"'
    )

    props = resource.get("properties") or {}
    fpath = props.get("folderPath")
    if fpath != EXPECTED_FOLDER_PATH:
        sys.exit(
            f"FAIL: properties.folderPath should be {EXPECTED_FOLDER_PATH!r} "
            f"(the deployed Orchestrator folder of {EXPECTED_PROCESS_NAME}), got {fpath!r}"
        )
    print(f'OK: properties.processName={EXPECTED_PROCESS_NAME!r}, folderPath={EXPECTED_FOLDER_PATH!r}')

    rkey = resource.get("referenceKey")
    if not isinstance(rkey, str) or "-" not in rkey:
        sys.exit(
            f"FAIL: resource.referenceKey must be a UUID-shaped string copied "
            f"from `uip solution resources list`'s `Key`, got {rkey!r}"
        )
    print(f"OK: resource.referenceKey={rkey!r} (UUID-shaped)")


if __name__ == "__main__":
    main()
