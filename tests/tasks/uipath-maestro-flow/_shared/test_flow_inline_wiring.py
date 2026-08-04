"""Unit tests for flow_inline_wiring helpers. Run with ``pytest`` from any directory.

Exercises the flow-file-first assertion helpers against hand-crafted `.flow`
shapes (embedded agents, legacy shells, scaffold defaults) so regressions in
the eval logic are caught without burning a real tenant run. Fixture shapes
mirror the M0 gating experiment's validated flow (see
docs/plans/inline-agent-flow-file-rewrite.md § M0 notes).
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flow_inline_wiring import (  # noqa: E402
    assert_agent_input_vars,
    assert_agent_output_vars,
    assert_cluster_vars_ref,
    assert_definition_present,
    assert_edge,
    assert_embedded_agent,
    assert_prompt_tokens,
    assert_resource_inputs,
    assert_resource_source_uuid,
    assert_tool_type_key_uuid,
    find_autonomous_agent_node,
    find_wired_resource,
    load_json,
)

REAL_PROMPT = (
    "You are a precise assistant. Answer factual questions about UiPath "
    "Maestro flows in a single short sentence."
)


def _agent_node(**input_overrides):
    inputs = {
        "source": "a070100f-d49d-4a39-b619-7aa166bae5e5",
        "systemPrompt": REAL_PROMPT,
        "userPrompt": "Name the weekday that follows Tuesday.",
        "model": "anthropic.claude-sonnet-4-20250514-v1:0",
        "mode": "standard",
        "guardrails": [],
        "agentInputVariables": [],
        "agentOutputVariables": [
            {"id": "answer", "type": "string", "description": "The answer"}
        ],
    }
    inputs.update(input_overrides)
    return {
        "id": "expAgent",
        "type": "uipath.agent.autonomous",
        "typeVersion": "1.3",
        "display": {"label": "Exp Agent"},
        "inputs": inputs,
    }


def _flow(nodes=None, edges=None, definitions=None):
    return {
        "id": "c40f1fa0-9a8f-426c-afc1-ebffe6aa2fd9",
        "version": "1.9",
        "name": "ExpFlow",
        "nodes": nodes if nodes is not None else [_agent_node()],
        "edges": edges or [],
        "definitions": definitions or [],
    }


# ── load_json ───────────────────────────────────────────────────────────────


def test_load_json_reads_valid_file(tmp_path):
    p = tmp_path / "f.flow"
    p.write_text('{"nodes": []}')
    assert load_json(p) == {"nodes": []}


def test_load_json_fails_on_missing_file(tmp_path):
    with pytest.raises(SystemExit, match="Missing"):
        load_json(tmp_path / "absent.flow")


def test_load_json_fails_on_invalid_json(tmp_path):
    p = tmp_path / "f.flow"
    p.write_text("{not json")
    with pytest.raises(SystemExit, match="not valid JSON"):
        load_json(p)


# ── find_autonomous_agent_node ──────────────────────────────────────────────


def test_finds_autonomous_node():
    node = find_autonomous_agent_node(_flow())
    assert node["id"] == "expAgent"


def test_fails_when_no_autonomous_node():
    flow = _flow(nodes=[{"id": "start", "type": "core.trigger.manual"}])
    with pytest.raises(SystemExit, match="no node of type"):
        find_autonomous_agent_node(flow)


def test_published_agent_node_does_not_match():
    # uipath.core.agent.* = published agent reference, NOT an inline agent.
    flow = _flow(nodes=[{"id": "ref", "type": "uipath.core.agent.abc123"}])
    with pytest.raises(SystemExit):
        find_autonomous_agent_node(flow)


# ── assert_embedded_agent ───────────────────────────────────────────────────


def test_embedded_agent_passes_on_real_config():
    inputs = assert_embedded_agent(_agent_node())
    assert inputs["model"].startswith("anthropic.")


def test_legacy_shell_fails_embed_predicate():
    # Structural-only inputs (source + variables arrays) = legacy shell.
    node = _agent_node()
    del node["inputs"]["systemPrompt"]
    del node["inputs"]["userPrompt"]
    del node["inputs"]["model"]
    with pytest.raises(SystemExit, match="legacy shell"):
        assert_embedded_agent(node)


def test_placeholder_system_prompt_fails():
    node = _agent_node(systemPrompt="You are an agentic assistant.")
    with pytest.raises(SystemExit, match="placeholder"):
        assert_embedded_agent(node)


def test_short_system_prompt_fails():
    node = _agent_node(systemPrompt="Be helpful.")
    with pytest.raises(SystemExit, match="too short"):
        assert_embedded_agent(node)


def test_scaffold_model_fails_by_default():
    node = _agent_node(model="gpt-4o-2024-11-20")
    with pytest.raises(SystemExit, match="not overridden"):
        assert_embedded_agent(node)


def test_scaffold_model_passes_when_override_not_required():
    inputs = assert_embedded_agent(_agent_node(model="gpt-4o-2024-11-20"),
                                   require_model_override=False)
    assert inputs["model"] == "gpt-4o-2024-11-20"


def test_missing_model_fails_even_without_override_requirement():
    node = _agent_node()
    del node["inputs"]["model"]
    with pytest.raises(SystemExit, match="model is missing"):
        assert_embedded_agent(node, require_model_override=False)


@pytest.mark.parametrize(
    "bad_source",
    [
        None,
        "",
        "not-a-uuid",
        "A070100F-D49D-4A39-B619-7AA166BAE5E5",  # uppercase breaks folder identity
        "{a070100f-d49d-4a39-b619-7aa166bae5e5}",
    ],
)
def test_bad_source_fails(bad_source):
    node = _agent_node(source=bad_source)
    with pytest.raises(SystemExit, match="lowercase UUID"):
        assert_embedded_agent(node)


def test_no_sidecar_directory_required():
    # The core contract inversion: an embedded agent passes with NO <GUID>/
    # directory anywhere on disk — nothing in the helper touches the filesystem.
    assert_embedded_agent(_agent_node())


def test_triage_placeholder_prompt_fails():
    # Placeholder set parity with check_inline_agent.py, incl. the
    # robust-smoke scenario's scaffold prompt.
    node = _agent_node(systemPrompt="Triage the inbound email.")
    with pytest.raises(SystemExit, match="placeholder"):
        assert_embedded_agent(node)


# ── assert_embedded_agent: never-author guards ──────────────────────────────


def test_instance_model_block_fails():
    node = _agent_node()
    node["model"] = {"source": True, "type": "bpmn:ServiceTask"}
    with pytest.raises(SystemExit, match="instance 'model' block"):
        assert_embedded_agent(node)


def test_content_tokens_in_inputs_fails():
    node = _agent_node(contentTokens=[{"type": "simpleText", "rawString": "x"}])
    with pytest.raises(SystemExit, match="contentTokens"):
        assert_embedded_agent(node)


def test_derived_input_definition_fails():
    node = _agent_node(derivedInputDefinition=[])
    with pytest.raises(SystemExit, match="derivedInputDefinition"):
        assert_embedded_agent(node)


# ── assert_prompt_tokens ────────────────────────────────────────────────────


def test_prompt_tokens_pass_on_canvas_form():
    node = _agent_node(
        userPrompt="Answer about {{ $vars.start.output.topic }} for run "
                   "{{ $metadata.runId }}."
    )
    assert_prompt_tokens(node)


def test_prompt_tokens_pass_on_plain_static_prompts():
    assert_prompt_tokens(_agent_node())


@pytest.mark.parametrize("derived", [
    "Analyze {{input.start__output__topic}} carefully.",
    "Analyze {{ input.start__output__topic }} carefully.",
    "Analyze {{ $agent.start__output__topic }} carefully.",
])
def test_prompt_tokens_fail_on_derived_namespaces(derived):
    node = _agent_node(userPrompt=derived)
    with pytest.raises(SystemExit, match="derived-artifact token form"):
        assert_prompt_tokens(node)


def test_prompt_tokens_fail_on_derived_form_in_system_prompt():
    node = _agent_node(systemPrompt=REAL_PROMPT + " Use {{input.context}}.")
    with pytest.raises(SystemExit, match="systemPrompt uses derived"):
        assert_prompt_tokens(node)


def test_prompt_tokens_require_vars_ref_fails_on_static_prompts():
    with pytest.raises(SystemExit, match="no .* reference in either prompt"):
        assert_prompt_tokens(_agent_node(), require_vars_ref=True)


def test_prompt_tokens_require_vars_ref_passes_with_ref():
    node = _agent_node(userPrompt="Classify {{ $vars.start.output.email }}.")
    assert_prompt_tokens(node, require_vars_ref=True)


# ── assert_agent_output_vars ────────────────────────────────────────────────


def test_output_vars_pass_on_expected_typed_fields():
    assert_agent_output_vars(_agent_node(), {"answer": "string"})


def test_output_vars_allow_extras():
    node = _agent_node(agentOutputVariables=[
        {"id": "answer", "type": "string"},
        {"id": "confidence", "type": "number"},
    ])
    assert_agent_output_vars(node, {"answer": "string"})


def test_output_vars_fail_on_missing_id():
    with pytest.raises(SystemExit, match="missing output variable"):
        assert_agent_output_vars(_agent_node(), {"rationale": "string"})


def test_output_vars_fail_on_wrong_type():
    with pytest.raises(SystemExit, match="expected 'number'"):
        assert_agent_output_vars(_agent_node(), {"answer": "number"})


def test_output_vars_fail_on_missing_description_when_required():
    node = _agent_node(agentOutputVariables=[{"id": "answer", "type": "string"}])
    with pytest.raises(SystemExit, match="no description"):
        assert_agent_output_vars(node, {"answer": "string"},
                                 require_description=True)


# ── assert_agent_input_vars ─────────────────────────────────────────────────


def test_input_vars_pass_on_authored_empty_list():
    assert_agent_input_vars(_agent_node())


def test_input_vars_pass_when_key_absent():
    node = _agent_node()
    del node["inputs"]["agentInputVariables"]
    assert_agent_input_vars(node)


def test_input_vars_pass_on_derived_entries():
    node = _agent_node(agentInputVariables=[
        {"id": "start__output__topic", "type": "string",
         "binding": "=$vars.start.output.topic"},
        {"id": "metadata__runId", "type": "string",
         "binding": "=$metadata.runId"},
    ])
    assert_agent_input_vars(node)


def test_input_vars_fail_on_hand_authored_entry_without_binding():
    node = _agent_node(agentInputVariables=[{"id": "topic", "type": "string"}])
    with pytest.raises(SystemExit, match="binding"):
        assert_agent_input_vars(node)


def test_input_vars_fail_when_not_a_list():
    node = _agent_node(agentInputVariables={"topic": "string"})
    with pytest.raises(SystemExit, match="not a list"):
        assert_agent_input_vars(node)


# ── assert_edge ─────────────────────────────────────────────────────────────


def _edges_flow():
    return _flow(edges=[
        {"id": "e1", "sourceNodeId": "start", "sourcePort": "output",
         "targetNodeId": "expAgent", "targetPort": "input"},
        {"id": "e5", "sourceNodeId": "expAgent", "sourcePort": "tool",
         "targetNodeId": "rpaTool", "targetPort": "input"},
    ])


def test_edge_match():
    assert_edge(_edges_flow(), source_id="expAgent", source_port="tool",
                target_id="rpaTool", target_port="input")


def test_edge_fails_on_wrong_port():
    with pytest.raises(SystemExit, match="no edge wires"):
        assert_edge(_edges_flow(), source_id="expAgent", source_port="context",
                    target_id="rpaTool", target_port="input")


# ── assert_definition_present ───────────────────────────────────────────────


def _definition(node_type="uipath.agent.autonomous", version="1.3"):
    return {"nodeType": node_type, "version": version,
            "display": {"label": "Autonomous agent"}}


def test_definition_present_returns_manifest():
    flow = _flow(definitions=[_definition()])
    node = find_autonomous_agent_node(flow)
    definition = assert_definition_present(flow, node)
    assert definition["nodeType"] == "uipath.agent.autonomous"


def test_definition_missing_fails():
    flow = _flow(definitions=[])
    node = find_autonomous_agent_node(flow)
    with pytest.raises(SystemExit, match="no entry"):
        assert_definition_present(flow, node)


def test_definition_version_must_match_exactly():
    # Multiple versions of one nodeType coexist; (type, typeVersion) must
    # match a (nodeType, version) pair exactly.
    flow = _flow(definitions=[_definition(version="1.1")])
    node = find_autonomous_agent_node(flow)
    with pytest.raises(SystemExit, match="no entry"):
        assert_definition_present(flow, node)


# ── resource-node helpers (M2: process-family tools) ────────────────────────


TOOL_TYPE = "uipath.agent.resource.tool.process.f27d0f9b-6972-47d3-8874-ec8aed8e8e16"


def _tool_node(**input_overrides):
    inputs = {
        "source": "9c40fd2e-58f4-45a3-93bb-0dbe38a72e10",
        "name": "FibonacciRPA",
        "description": "Computes the Fibonacci number for a given index.",
        "index": {"mode": "prompt", "textValue": "",
                  "promptValue": "The index to compute", "argumentPath": ""},
        "inputSchema": {"type": "object", "properties": {"index": {"type": "number"}}},
        "outputSchema": {"type": "object", "properties": {"value": {"type": "integer"}}},
        "properties": {"processName": "FibonacciRPA",
                       "folderPath": "Shared/uipath-agents/FibonacciRPA"},
    }
    inputs.update(input_overrides)
    return {
        "id": "rpaTool",
        "type": TOOL_TYPE,
        "typeVersion": "1.0.0",
        "display": {"label": "FibonacciRPA"},
        "inputs": inputs,
    }


def _cluster_flow(tool=None, edges=None):
    tool = tool if tool is not None else _tool_node()
    return _flow(
        nodes=[_agent_node(), tool],
        edges=edges if edges is not None else [
            {"id": "e5", "sourceNodeId": "expAgent", "sourcePort": "tool",
             "targetNodeId": "rpaTool", "targetPort": "input"},
        ],
    )


# ── find_wired_resource ──────────────────────────────────────────────────────


def test_find_wired_resource_returns_wired_node():
    flow = _cluster_flow()
    agent = find_autonomous_agent_node(flow)
    node = find_wired_resource(
        flow, agent, type_prefix="uipath.agent.resource.tool.process.",
        source_port="tool",
    )
    assert node["id"] == "rpaTool"


def test_find_wired_resource_fails_when_no_candidate():
    flow = _flow()
    agent = find_autonomous_agent_node(flow)
    with pytest.raises(SystemExit, match="no node with type prefix"):
        find_wired_resource(
            flow, agent, type_prefix="uipath.agent.resource.tool.process.",
            source_port="tool",
        )


def test_find_wired_resource_fails_when_unwired():
    flow = _cluster_flow(edges=[])
    agent = find_autonomous_agent_node(flow)
    with pytest.raises(SystemExit, match="no artifact edge"):
        find_wired_resource(
            flow, agent, type_prefix="uipath.agent.resource.tool.process.",
            source_port="tool",
        )


def test_find_wired_resource_fails_on_wrong_port():
    flow = _cluster_flow(edges=[
        {"id": "e5", "sourceNodeId": "expAgent", "sourcePort": "context",
         "targetNodeId": "rpaTool", "targetPort": "input"},
    ])
    agent = find_autonomous_agent_node(flow)
    with pytest.raises(SystemExit, match="no artifact edge"):
        find_wired_resource(
            flow, agent, type_prefix="uipath.agent.resource.tool.process.",
            source_port="tool",
        )


# ── assert_resource_source_uuid ──────────────────────────────────────────────


def test_resource_source_uuid_accepts_lowercase_uuid():
    assert assert_resource_source_uuid(_tool_node()) == (
        "9c40fd2e-58f4-45a3-93bb-0dbe38a72e10"
    )


def test_resource_source_uuid_rejects_non_uuid():
    with pytest.raises(SystemExit, match="not a lowercase UUID"):
        assert_resource_source_uuid(_tool_node(source="fibonacci-tool"))


def test_resource_source_uuid_rejects_uppercase():
    with pytest.raises(SystemExit, match="not a lowercase UUID"):
        assert_resource_source_uuid(
            _tool_node(source="9C40FD2E-58F4-45A3-93BB-0DBE38A72E10")
        )


def test_resource_source_uuid_rejects_instance_model_block():
    node = _tool_node()
    node["model"] = {"source": True}
    with pytest.raises(SystemExit, match="instance 'model' block"):
        assert_resource_source_uuid(node)


# ── assert_resource_inputs ───────────────────────────────────────────────────


def test_resource_inputs_pass():
    inputs = assert_resource_inputs(
        _tool_node(),
        expected_properties={"processName": "FibonacciRPA",
                             "folderPath": "Shared/uipath-agents/FibonacciRPA"},
    )
    assert inputs["name"] == "FibonacciRPA"


def test_resource_inputs_fails_on_wrong_process_name():
    with pytest.raises(SystemExit, match="processName"):
        assert_resource_inputs(
            _tool_node(properties={"processName": "Renamed",
                                   "folderPath": "Shared/uipath-agents/FibonacciRPA"}),
            expected_properties={"processName": "FibonacciRPA"},
        )


def test_resource_inputs_fails_on_empty_folder_path():
    # An empty folderPath breaks runtime process resolution — the exact
    # failure seen on the 2026-07-23 codex nightly (inline_solution_maestro).
    with pytest.raises(SystemExit, match="folderPath"):
        assert_resource_inputs(
            _tool_node(properties={"processName": "FibonacciRPA", "folderPath": ""}),
            expected_properties={"processName": "FibonacciRPA",
                                 "folderPath": "solution_folder"},
        )


def test_resource_inputs_fails_on_missing_properties_object():
    node = _tool_node()
    del node["inputs"]["properties"]
    with pytest.raises(SystemExit, match="properties is not an object"):
        assert_resource_inputs(node, expected_properties={"processName": "FibonacciRPA"})


def test_resource_inputs_fails_on_empty_name_and_description():
    with pytest.raises(SystemExit, match="inputs.name.*inputs.description"):
        assert_resource_inputs(_tool_node(name="", description="  "))


# ── assert_tool_type_key_uuid ────────────────────────────────────────────────


def test_tool_type_key_uuid_accepts_registry_minted_type():
    assert assert_tool_type_key_uuid(_tool_node()) == (
        "f27d0f9b-6972-47d3-8874-ec8aed8e8e16"
    )


def test_tool_type_key_uuid_rejects_hand_constructed_type():
    node = _tool_node()
    node["type"] = "uipath.agent.resource.tool.process.FibonacciRPA"
    with pytest.raises(SystemExit, match="resource-key GUID"):
        assert_tool_type_key_uuid(node)


# ── assert_cluster_vars_ref ──────────────────────────────────────────────────


def test_cluster_vars_ref_found_in_prompt_token():
    agent = _agent_node(userPrompt="Compute {{ $vars.start.output.index }}.")
    tool = _tool_node()
    assert_cluster_vars_ref([agent, tool])


def test_cluster_vars_ref_found_in_variable_mode_argument_path():
    # Flow data may enter through a resource node's structured input instead
    # of a prompt token — a variable-mode per-argument argumentPath.
    agent = _agent_node()
    tool = _tool_node(index={"mode": "variable", "textValue": "",
                             "promptValue": "",
                             "argumentPath": "$vars.start.output.index"})
    assert_cluster_vars_ref([agent, tool])


def test_cluster_vars_ref_fails_when_absent():
    with pytest.raises(SystemExit, match="no .vars./.metadata. reference"):
        assert_cluster_vars_ref([_agent_node(), _tool_node()])
