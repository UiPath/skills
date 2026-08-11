#!/usr/bin/env python3
"""Flow-file-first check: inline agent + context grounding (semantic index).

Grades the `.flow` as the source of truth (sidecar neither required nor
forbidden):

  1. Self-contained `uipath.agent.autonomous` node (string prompts, real
     system prompt, overridden model, lowercase-UUID `inputs.source`, no
     never-author artifacts) with canvas-form prompt tokens and a
     contract-conformant `agentInputVariables`.
  2. Typed output: `agentOutputVariables` declares `answer: string` (the
     prompt's required output contract).
  3. Agent definition present at the exact (type, typeVersion) with the
     inline-agent serviceType.
  4. A `uipath.agent.resource.context.index.<name>.<id>` node wired to the
     agent's `context` handle, type keyed by the index GUID (discovered via
     registry search, not hand-constructed).
  5. Context node carries the FLAT flow-form config in `inputs`: UUID
     `source`, identity copied from the manifest's `inputDefaults`
     (`indexName == "UiPathAgentsProductKnowledge"`, `folderPath` == the
     real tenant folder), all-lowercase `retrievalMode` (validate cannot
     catch casing drift — a camelCase value silently misroutes to the
     semantic branch), no derived `settings`/`contextType`/`$resourceType`
     contamination.
  6. Context definition present at the exact (type, typeVersion).
  7. Flow data reaches the cluster: at least one `$vars.`/`$metadata.` ref
     across the agent prompts or the context's structured inputs (the
     prompt mandates a required `question` input).
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
    assert_agent_output_vars,
    assert_agent_sequence_wiring,
    assert_context_inputs,
    assert_definition_present,
    find_flow_file,
    find_wired_resource,
    assert_resource_source_uuid,
    assert_cluster_vars_ref,
)

INLINE_AGENT_SERVICE_TYPE = "Orchestrator.StartInlineAgentJob"
FLOW_PATH = Path(os.getcwd()) / "KnowledgeFlowSol" / "KnowledgeFlow" / "KnowledgeFlow.flow"
CONTEXT_TYPE_PREFIX = "uipath.agent.resource.context.index."
EXPECTED_IDENTITY = {
    "indexName": "UiPathAgentsProductKnowledge",
    "folderPath": "Shared/uipath-agents",
}
EXPECTED_OUTPUTS = {"answer": "string"}


def main() -> None:
    flow = load_json(find_flow_file(FLOW_PATH))
    agent_node = find_autonomous_agent_node(flow)

    assert_embedded_agent(agent_node)
    assert_prompt_tokens(agent_node)
    assert_agent_input_vars(agent_node)
    assert_agent_sequence_wiring(flow, agent_node)
    assert_agent_output_vars(agent_node, EXPECTED_OUTPUTS)
    print(
        f"OK: {agent_node['id']} is self-contained with typed output "
        f"{sorted(EXPECTED_OUTPUTS)}"
    )

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

    context_node = find_wired_resource(
        flow, agent_node, type_prefix=CONTEXT_TYPE_PREFIX, source_port="context"
    )
    print(f"OK: {context_node['type']} is wired to the agent's 'context' handle")

    assert_resource_source_uuid(context_node)
    assert_context_inputs(context_node, expected_identity=EXPECTED_IDENTITY)
    print(
        'OK: context inputs carry indexName="UiPathAgentsProductKnowledge", '
        "the real tenant folderPath, lowercase retrievalMode, UUID source"
    )

    assert_definition_present(flow, context_node)
    print("OK: context definition present at the exact (type, typeVersion)")

    assert_cluster_vars_ref([agent_node, context_node])
    print("OK: flow data is wired into the agent cluster")


if __name__ == "__main__":
    main()
