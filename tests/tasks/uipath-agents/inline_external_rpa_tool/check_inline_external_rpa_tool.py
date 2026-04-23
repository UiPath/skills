#!/usr/bin/env python3
"""Inline agent + external RPA tool check.

Validates:
  1. Flow has a `uipath.agent.autonomous` node and a
     `uipath.agent.resource.tool.rpa` node.
  2. Edge wires agent.tool -> tool.input.
  3. Inline agent dir has `resources/InvoiceProcessor/resource.json`
     with:
       - $resourceType == "tool"
       - type == "process"
       - location == "external"
       - properties.processName == "InvoiceProcessor"
       - properties.folderPath is a real path (NOT "solution_folder")
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

FLOW_PATH = Path(os.getcwd()) / "BillingFlowSol" / "BillingFlow" / "BillingFlow.flow"
RPA_TOOL_NODE_TYPE = "uipath.agent.resource.tool.rpa"


def main() -> None:
    flow = load_json(FLOW_PATH)
    agent_node = find_autonomous_agent_node(flow)
    tool_node = find_resource_node(flow, node_type=RPA_TOOL_NODE_TYPE)
    print(f"OK: flow has {agent_node['type']} and {tool_node['type']} nodes")

    assert_edge(
        flow,
        source_id=agent_node["id"],
        source_port="tool",
        target_id=tool_node["id"],
        target_port="input",
    )
    print("OK: agent 'tool' handle is wired to external RPA tool node's 'input' handle")

    agent_dir = resolve_inline_agent_dir(FLOW_PATH, agent_node)
    resource_path = agent_dir / "resources" / "InvoiceProcessor" / "resource.json"
    resource = load_json(resource_path)

    expected = {
        "$resourceType": "tool",
        "type": "process",
        "location": "external",
    }
    for key, want in expected.items():
        if resource.get(key) != want:
            sys.exit(f"FAIL: {resource_path} {key!r} should be {want!r}, got {resource.get(key)!r}")
    print(
        f'OK: {resource_path.relative_to(Path(os.getcwd()))} is '
        f'$resourceType="tool", type="process", location="external"'
    )

    props = resource.get("properties") or {}
    if props.get("processName") != "InvoiceProcessor":
        sys.exit(f'FAIL: properties.processName should be "InvoiceProcessor", got {props.get("processName")!r}')
    fpath = props.get("folderPath")
    if not isinstance(fpath, str) or not fpath.strip():
        sys.exit(f"FAIL: properties.folderPath must be a non-empty string, got {fpath!r}")
    if fpath == "solution_folder":
        sys.exit(
            'FAIL: properties.folderPath is "solution_folder", which is only '
            'valid for location=="solution". External tools require a real '
            'Orchestrator folder path like "Shared".'
        )
    print(f'OK: properties.processName="InvoiceProcessor", folderPath={fpath!r} (not "solution_folder")')


if __name__ == "__main__":
    main()
