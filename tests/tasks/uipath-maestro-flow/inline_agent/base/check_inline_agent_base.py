#!/usr/bin/env python3
"""Flow-file-first inline-agent check for skill-flow-inline-agent-base.

Reads GreetingSol/GreetingFlow/GreetingFlow.flow (existence asserted by a
file_exists criterion in the task YAML) and grades the `.flow` as the source
of truth — the sidecar directory is a derived artifact and is neither
required nor forbidden:

  1. The flow contains a self-contained `uipath.agent.autonomous` node:
     string prompts (embed trigger), real system prompt, overridden model,
     lowercase-UUID `inputs.source`, no never-author artifacts (instance
     `model` block, `contentTokens`, `derivedInputDefinition`).
  2. Prompts use the canvas token namespace (`{{ $vars.* }}`), never the
     derived `{{input.*}}` / `{{ $agent.* }}` forms.
  3. `agentInputVariables` follows the authoring contract ([] or
     derived-shaped entries only).
  4. Typed output: `agentOutputVariables` declares `greeting: string`.
  5. `definitions[]` carries the node's manifest at the exact
     (type, typeVersion), and its serviceType is the inline-agent one
     (`Orchestrator.StartInlineAgentJob`, never the solution-agent
     `StartAgentJob`).
  6. The agent node is wired: at least one incoming edge on `input` and one
     outgoing edge on `success`.
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
    assert_agent_output_vars,
    assert_agent_input_vars,
    assert_definition_present,
)

INLINE_AGENT_SERVICE_TYPE = "Orchestrator.StartInlineAgentJob"
FLOW_PATH = Path(os.getcwd()) / "GreetingSol" / "GreetingFlow" / "GreetingFlow.flow"


def main() -> None:
    flow = load_json(FLOW_PATH)
    node = find_autonomous_agent_node(flow)

    assert_embedded_agent(node)
    print(f"OK: {node['id']} is self-contained (embedded prompts, model, UUID source)")

    assert_prompt_tokens(node)
    print("OK: prompts use the canvas token namespace")

    assert_agent_input_vars(node)
    assert_agent_output_vars(node, {"greeting": "string"})
    print("OK: typed output variable 'greeting' declared")

    definition = assert_definition_present(flow, node)
    service_type = (definition.get("model") or {}).get("serviceType")
    if service_type != INLINE_AGENT_SERVICE_TYPE:
        sys.exit(
            f"FAIL: definitions[] entry for {node.get('type')!r} has "
            f"model.serviceType {service_type!r}, expected "
            f"{INLINE_AGENT_SERVICE_TYPE!r} — 'Orchestrator.StartAgentJob' is "
            "the solution-agent variant; a missing serviceType means the "
            "definition was not copied verbatim from registry get"
        )
    print(f"OK: definition present with serviceType {INLINE_AGENT_SERVICE_TYPE!r}")

    agent_id = node["id"]
    edges = flow.get("edges") or []
    incoming_input = [
        e for e in edges
        if e.get("targetNodeId") == agent_id and e.get("targetPort") == "input"
    ]
    outgoing_success = [
        e for e in edges
        if e.get("sourceNodeId") == agent_id and e.get("sourcePort") == "success"
    ]
    if not incoming_input:
        sys.exit(
            f"FAIL: agent node {agent_id!r} has no incoming edge on "
            "targetPort 'input' — node is not wired into the flow"
        )
    if not outgoing_success:
        sys.exit(
            f"FAIL: agent node {agent_id!r} has no outgoing edge on "
            "sourcePort 'success' — flow has no continuation after the agent"
        )
    print(
        f"OK: agent node is wired — {len(incoming_input)} incoming on "
        f"'input', {len(outgoing_success)} outgoing on 'success'"
    )


if __name__ == "__main__":
    main()
