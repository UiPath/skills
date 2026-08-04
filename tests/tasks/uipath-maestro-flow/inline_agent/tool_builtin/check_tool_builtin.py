#!/usr/bin/env python3
"""Flow-file-first check: inline agent + built-in "Analyze Files" tool.

Grades the `.flow` as the source of truth (sidecar neither required nor
forbidden):

  1. Self-contained `uipath.agent.autonomous` node (string prompts, real
     system prompt, overridden model, lowercase-UUID `inputs.source`, no
     never-author artifacts) with canvas-form prompt tokens, a
     contract-conformant `agentInputVariables`, and sequence wiring
     (input + success edges).
  2. Agent definition present at the exact (type, typeVersion) with the
     inline-agent serviceType.
  3. A `uipath.agent.resource.tool.builtin.analyzefiles` node wired to the
     agent's `tool` handle (artifact edge, target port `input`). The node
     TYPE suffix selects the tool — replaces the old sidecar
     resource.json `properties.toolType` assertion.
  4. Builtin identity contract: analyzefiles declares `model.source: true`
     ⇒ lowercase-UUID `inputs.source` (no source==dirname cross-check —
     no sidecar directory is authored).
  5. No derived resource.json fields in the tool node's `inputs` (no
     `$resourceType`/`type: "internal"`/`location`/`argumentProperties`/
     `properties.toolType` — the likely legacy contamination).
  6. Tool node carries non-empty `name`/`description` in `inputs`.
  7. Tool definition present at the exact (type, typeVersion).
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
    assert_agent_sequence_wiring,
    assert_builtin_identity,
    assert_embedded_agent,
    assert_no_derived_resource_fields,
    assert_prompt_tokens,
    assert_agent_input_vars,
    assert_definition_present,
    assert_resource_inputs,
    find_flow_file,
    find_wired_resource,
)

INLINE_AGENT_SERVICE_TYPE = "Orchestrator.StartInlineAgentJob"
FLOW_PATH = Path(os.getcwd()) / "DocsFlowSol" / "DocsFlow" / "DocsFlow.flow"
# The prompt requests the built-in "Analyze Files" tool — the analyzefiles
# node type (its derived sidecar toolType is `analyze-attachments`; the
# summarize/batchtransform builtins would not satisfy the request).
EXPECTED_TOOL_TYPE_PREFIX = "uipath.agent.resource.tool.builtin.analyzefiles"


def main() -> None:
    flow = load_json(find_flow_file(FLOW_PATH))
    agent_node = find_autonomous_agent_node(flow)

    assert_embedded_agent(agent_node)
    assert_prompt_tokens(agent_node)
    assert_agent_input_vars(agent_node)
    assert_agent_sequence_wiring(flow, agent_node)
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
        flow, agent_node, type_prefix=EXPECTED_TOOL_TYPE_PREFIX, source_port="tool"
    )
    print(f"OK: {tool_node['type']} is wired to the agent's 'tool' handle")

    assert_builtin_identity(tool_node)
    assert_no_derived_resource_fields(tool_node)
    assert_resource_inputs(tool_node)
    print("OK: builtin tool inputs carry UUID source + name/description, no derived resource.json fields")

    assert_definition_present(flow, tool_node)
    print("OK: builtin tool definition present at the exact (type, typeVersion)")


if __name__ == "__main__":
    main()
