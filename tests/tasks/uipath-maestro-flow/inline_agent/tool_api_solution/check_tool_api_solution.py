#!/usr/bin/env python3
"""Flow-file-first check: inline agent + in-solution API workflow tool.

Grades the `.flow` as the source of truth (sidecar neither required nor
forbidden): self-contained autonomous node, verbatim definitions (agent +
tool), a `uipath.agent.resource.tool.api.<key>` node wired on the `tool`
handle carrying `inputs` config (processName "CalculateShippingRate",
folderPath "solution_folder", UUID source).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from _shared.flow_inline_wiring import (  # noqa: E402
    load_json,
    find_autonomous_agent_node,
    assert_embedded_agent,
    assert_prompt_tokens,
    assert_agent_input_vars,
    assert_definition_present,
    find_wired_resource,
    assert_resource_source_uuid,
    assert_resource_inputs,
    assert_tool_type_key_uuid,
)

INLINE_AGENT_SERVICE_TYPE = "Orchestrator.StartInlineAgentJob"
FLOW_PATH = Path(os.getcwd()) / "ShippingFlowSol" / "ShippingFlow" / "ShippingFlow.flow"
TOOL_TYPE_PREFIX = "uipath.agent.resource.tool.api."
EXPECTED_PROPERTIES = {
    "processName": "CalculateShippingRate",
    "folderPath": "solution_folder",
}


def main() -> None:
    flow = load_json(FLOW_PATH)
    agent_node = find_autonomous_agent_node(flow)

    assert_embedded_agent(agent_node)
    assert_prompt_tokens(agent_node)
    assert_agent_input_vars(agent_node)
    print(f"OK: {agent_node['id']} is self-contained (embedded prompts, model, UUID source)")

    definition = assert_definition_present(flow, agent_node)
    service_type = (definition.get("model") or {}).get("serviceType")
    if service_type != INLINE_AGENT_SERVICE_TYPE:
        sys.exit(
            f"FAIL: agent definitions[] entry has model.serviceType "
            f"{service_type!r}, expected {INLINE_AGENT_SERVICE_TYPE!r} — a "
            "missing serviceType means the definition was not copied verbatim "
            "from registry get"
        )
    print(f"OK: agent definition present with serviceType {INLINE_AGENT_SERVICE_TYPE!r}")

    tool_node = find_wired_resource(
        flow, agent_node, type_prefix=TOOL_TYPE_PREFIX, source_port="tool"
    )
    print(f"OK: {tool_node['type']} is wired to the agent's 'tool' handle")

    assert_tool_type_key_uuid(tool_node)
    assert_resource_source_uuid(tool_node)
    assert_resource_inputs(tool_node, expected_properties=EXPECTED_PROPERTIES)
    print(
        'OK: tool inputs carry processName="CalculateShippingRate", '
        'folderPath="solution_folder", UUID source'
    )

    assert_definition_present(flow, tool_node)
    print("OK: tool definition present at the exact (type, typeVersion)")


if __name__ == "__main__":
    main()
