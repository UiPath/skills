#!/usr/bin/env python3
"""Flow-file-first check: inline agent + MCP server tool.

Grades the `.flow` as the source of truth (sidecar neither required nor
forbidden):

  1. Self-contained `uipath.agent.autonomous` node (string prompts, real
     system prompt, overridden model, lowercase-UUID `inputs.source`, no
     never-author artifacts) with canvas-form prompt tokens and a
     contract-conformant `agentInputVariables`.
  2. Agent definition present at the exact (type, typeVersion) with the
     inline-agent serviceType.
  3. A `uipath.agent.resource.tool.mcp.<name>.<key>` node wired to the
     agent's **`tool` handle** (no `mcp` handle exists on any autonomous
     manifest), with its definition present (dynamic type — minted per
     registered server; hand-fabricated definitions are the failure mode
     the registry gap invites).
  4. MCP node carries the flat flow form: UUID `source`, expected `name`,
     slug == serverUrl (the canonical server slug), literal external
     `folderPath`, `referenceKey` matching the node-type suffix key,
     >= 1 `selectedTools` entry with object (parsed) inputSchemas, sane
     `discoveryMode`/`mcpType`, and none of the derived resource.json
     fields (availableTools/toolsConfiguration/solutionProperties).
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
    assert_agent_sequence_wiring,
    assert_definition_present,
    assert_mcp_inputs,
    find_flow_file,
    find_wired_resource,
    assert_resource_source_uuid,
)

INLINE_AGENT_SERVICE_TYPE = "Orchestrator.StartInlineAgentJob"
FLOW_PATH = Path(os.getcwd()) / "DevToolsFlowSol" / "DevToolsFlow" / "DevToolsFlow.flow"
TOOL_TYPE_PREFIX = "uipath.agent.resource.tool.mcp."
EXPECTED_SERVER_NAME = "GitHubMcp"


def main() -> None:
    flow_path = find_flow_file(FLOW_PATH)
    flow = load_json(flow_path)
    agent_node = find_autonomous_agent_node(flow)

    assert_embedded_agent(agent_node)
    assert_prompt_tokens(agent_node)
    assert_agent_input_vars(agent_node)
    assert_agent_sequence_wiring(flow, agent_node)
    print(f"OK: {agent_node['id']} is a self-contained embedded agent")

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

    mcp_node = find_wired_resource(
        flow, agent_node, type_prefix=TOOL_TYPE_PREFIX, source_port="tool"
    )
    print(f"OK: {mcp_node['type']} is wired to the agent's 'tool' handle")

    assert_resource_source_uuid(mcp_node)
    inputs = assert_mcp_inputs(mcp_node, expected_name=EXPECTED_SERVER_NAME)
    print(
        f"OK: MCP node inputs carry the flat flow form "
        f"(slug {inputs['slug']!r}, {len(inputs['selectedTools'])} selected tools)"
    )

    mcp_definition = assert_definition_present(flow, mcp_node)
    if (mcp_definition.get("model") or {}).get("source") is not True:
        sys.exit(
            "FAIL: MCP tool definitions[] entry lacks model.source: true — "
            "the definition was not copied verbatim from registry get "
            "(never hand-fabricate an MCP manifest; see the capability "
            "doc's registry-gap callout)"
        )
    # Fabrication probe: a registry-verbatim manifest always carries these
    # manifest-only sections; a minimal hand-written stub does not.
    missing = [
        k for k in ("inputDefinition", "handleConfiguration") if k not in mcp_definition
    ]
    if missing:
        sys.exit(
            f"FAIL: MCP tool definitions[] entry is missing {missing} — a "
            "registry-verbatim manifest always carries them; this definition "
            "looks hand-fabricated (see the capability doc's registry-gap "
            "callout: surface the gap, never fabricate)"
        )
    print("OK: MCP tool definition present with model.source: true + manifest sections")


if __name__ == "__main__":
    main()
