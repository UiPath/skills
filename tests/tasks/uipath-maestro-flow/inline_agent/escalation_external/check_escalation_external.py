#!/usr/bin/env python3
"""Flow-file-first check: inline agent + external escalation (deployed app).

Grades the `.flow` as the source of truth (sidecar neither required nor
forbidden):

  1. Self-contained `uipath.agent.autonomous` node (string prompts, real
     system prompt, overridden model, lowercase-UUID `inputs.source`, no
     never-author artifacts) with canvas-form prompt tokens and a
     contract-conformant `agentInputVariables`.
  2. Agent definition present at the exact (type, typeVersion) with the
     inline-agent serviceType.
  3. A `uipath.agent.resource.escalation*` node wired to the agent's
     `escalation` handle.
  4. Escalation node carries the FLAT flow-form config in `inputs`: UUID
     `source`, full `app` object bound to the DEPLOYED app
     (`appName == "FraudEscalation"`, `folderName ==
     "Shared/uipath-agents/FraudEscalation"` — the literal deployed
     Orchestrator folder from `resources list`, UUID `resourceKey`,
     non-empty action schemas — validate only checks app PRESENCE, so
     the checker owns schema completeness), >= 1 recipient with a value,
     no derived `channels[]`/`$resourceType`/`escalationType`
     contamination (the delivery layer derives at projection).
  5. Escalation definition present at the exact (type, typeVersion).
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
    assert_escalation_inputs,
    find_flow_file,
    find_wired_resource,
    assert_resource_source_uuid,
)

INLINE_AGENT_SERVICE_TYPE = "Orchestrator.StartInlineAgentJob"
FLOW_PATH = Path(os.getcwd()) / "FraudFlowSol" / "FraudFlow" / "FraudFlow.flow"
# No trailing dot: matches the tenant variants (`…escalation.coded-action-app`,
# `…escalation.quick-form`) AND the bare OOTB `…escalation` type.
ESCALATION_TYPE_PREFIX = "uipath.agent.resource.escalation"
EXPECTED_APP = {
    "appName": "FraudEscalation",
    "folderName": "Shared/uipath-agents/FraudEscalation",
}


def main() -> None:
    flow = load_json(find_flow_file(FLOW_PATH))
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

    escalation_node = find_wired_resource(
        flow, agent_node, type_prefix=ESCALATION_TYPE_PREFIX, source_port="escalation"
    )
    print(f"OK: {escalation_node['type']} is wired to the agent's 'escalation' handle")

    assert_resource_source_uuid(escalation_node)
    assert_escalation_inputs(escalation_node, expected_app=EXPECTED_APP)
    print(
        'OK: escalation inputs carry the full app object bound to the deployed '
        '"FraudEscalation" app (real Orchestrator folder), recipients, UUID source'
    )

    assert_definition_present(flow, escalation_node)
    print("OK: escalation definition present at the exact (type, typeVersion)")


if __name__ == "__main__":
    main()
