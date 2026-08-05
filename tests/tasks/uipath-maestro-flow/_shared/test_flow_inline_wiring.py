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
    assert_agent_sequence_wiring,
    assert_bindings_rows,
    assert_builtin_identity,
    assert_cluster_vars_ref,
    assert_connector_bindings,
    assert_connector_inputs,
    assert_context_inputs,
    assert_definition_present,
    assert_edge,
    assert_embedded_agent,
    assert_escalation_inputs,
    assert_no_derived_resource_fields,
    assert_prompt_tokens,
    assert_resource_inputs,
    assert_resource_source_uuid,
    assert_tool_type_key_uuid,
    find_autonomous_agent_node,
    find_flow_file,
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


# ── assert_no_derived_resource_fields (M3) ───────────────────────────────────


def test_no_derived_fields_passes_on_clean_tool_node():
    assert_no_derived_resource_fields(_tool_node())


def test_no_derived_fields_rejects_resource_type_discriminator():
    node = _tool_node()
    node["inputs"]["$resourceType"] = "tool"
    with pytest.raises(SystemExit, match=r"\$resourceType"):
        assert_no_derived_resource_fields(node)


def test_no_derived_fields_rejects_derived_type_string():
    with pytest.raises(SystemExit, match="derived resource.json type"):
        assert_no_derived_resource_fields(_tool_node(type="internal"))


def test_no_derived_fields_allows_argument_named_type():
    # A legitimate tool argument named "type" is a ValueSourceField OBJECT
    # (or a string outside the derived-type value set) — must not FAIL.
    node = _tool_node(type={"mode": "prompt", "textValue": "",
                            "promptValue": "The record type", "argumentPath": ""})
    assert_no_derived_resource_fields(node)


def test_no_derived_fields_rejects_location():
    with pytest.raises(SystemExit, match="location"):
        assert_no_derived_resource_fields(_tool_node(location="solution"))


def test_no_derived_fields_rejects_argument_properties():
    with pytest.raises(SystemExit, match="argumentProperties"):
        assert_no_derived_resource_fields(
            _tool_node(argumentProperties={"index": {"variant": "argument"}})
        )


def test_no_derived_fields_rejects_properties_tool_type():
    node = _tool_node(properties={"processName": "X", "folderPath": "Y",
                                  "toolType": "analyze-attachments"})
    with pytest.raises(SystemExit, match="toolType"):
        assert_no_derived_resource_fields(node)


# ── assert_bindings_rows (M3) ────────────────────────────────────────────────


def _bindings_row(attr="name"):
    return {"id": "b1", "name": attr, "type": "string", "resource": "process",
            "resourceKey": "Shared/uipath-agents/FibonacciRPA.FibonacciRPA",
            "propertyAttribute": attr, "default": "FibonacciRPA"}


def test_bindings_rows_pass_on_name_row():
    flow = _cluster_flow()
    flow["bindings"] = [_bindings_row("name"), _bindings_row("folderPath")]
    assert len(assert_bindings_rows(flow)) == 2


def test_bindings_rows_fail_when_absent():
    with pytest.raises(SystemExit, match="no top-level bindings"):
        assert_bindings_rows(_cluster_flow())


def test_bindings_rows_fail_on_unrelated_rows_only():
    flow = _cluster_flow()
    flow["bindings"] = [_bindings_row("connectionId")]
    with pytest.raises(SystemExit, match="no top-level bindings"):
        assert_bindings_rows(flow)


# ── assert_agent_sequence_wiring (M3) ────────────────────────────────────────


def _sequence_edges():
    return [
        {"id": "e1", "sourceNodeId": "start", "sourcePort": "output",
         "targetNodeId": "expAgent", "targetPort": "input"},
        {"id": "e2", "sourceNodeId": "expAgent", "sourcePort": "success",
         "targetNodeId": "end", "targetPort": "input"},
    ]


def test_sequence_wiring_passes():
    flow = _flow(edges=_sequence_edges())
    assert_agent_sequence_wiring(flow, find_autonomous_agent_node(flow))


def test_sequence_wiring_fails_without_input_edge():
    flow = _flow(edges=_sequence_edges()[1:])
    with pytest.raises(SystemExit, match="'input' port"):
        assert_agent_sequence_wiring(flow, find_autonomous_agent_node(flow))


def test_sequence_wiring_fails_without_success_edge():
    flow = _flow(edges=_sequence_edges()[:1])
    with pytest.raises(SystemExit, match="'success' port"):
        assert_agent_sequence_wiring(flow, find_autonomous_agent_node(flow))


# ── find_flow_file (M3) ──────────────────────────────────────────────────────


def test_find_flow_file_prefers_expected(tmp_path, monkeypatch):
    expected = tmp_path / "Sol" / "Proj" / "Proj.flow"
    expected.parent.mkdir(parents=True)
    expected.write_text("{}")
    monkeypatch.chdir(tmp_path)
    assert find_flow_file(expected) == expected


def test_find_flow_file_falls_back_to_sole_candidate(tmp_path, monkeypatch):
    actual = tmp_path / "Other" / "Other.flow"
    actual.parent.mkdir(parents=True)
    actual.write_text("{}")
    monkeypatch.chdir(tmp_path)
    got = find_flow_file(tmp_path / "Sol" / "Proj" / "Proj.flow")
    assert got.name == "Other.flow"


def test_find_flow_file_fails_on_multiple_candidates(tmp_path, monkeypatch):
    for name in ("A", "B"):
        d = tmp_path / name
        d.mkdir()
        (d / f"{name}.flow").write_text("{}")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit, match="2 .flow candidates"):
        find_flow_file(tmp_path / "Sol" / "Proj" / "Proj.flow")


def test_find_flow_file_fails_when_none(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit, match="0 .flow candidates"):
        find_flow_file(tmp_path / "Sol" / "Proj" / "Proj.flow")


# ── assert_builtin_identity (M3) ─────────────────────────────────────────────


def _builtin_node(suffix, **input_overrides):
    inputs = {
        "name": "Tool",
        "description": "A built-in tool.",
    }
    inputs.update(input_overrides)
    return {
        "id": "builtinTool",
        "type": f"uipath.agent.resource.tool.builtin.{suffix}",
        "typeVersion": "1.1",
        "display": {"label": "Tool"},
        "inputs": inputs,
    }


def test_builtin_identity_analyzefiles_requires_source_uuid():
    node = _builtin_node("analyzefiles",
                         source="3f2a9c1e-7b4d-4e8a-9c5f-1d2e3a4b5c6d")
    assert assert_builtin_identity(node) == "3f2a9c1e-7b4d-4e8a-9c5f-1d2e3a4b5c6d"


def test_builtin_identity_analyzefiles_fails_without_source():
    with pytest.raises(SystemExit, match="model.source: true"):
        assert_builtin_identity(_builtin_node("analyzefiles"))


def test_builtin_identity_summarize_requires_id_uuid():
    node = _builtin_node("summarize",
                         id="8e1b2d3c-4a5f-4b6e-8d7c-9a0b1c2d3e4f",
                         source="")
    assert assert_builtin_identity(node) == "8e1b2d3c-4a5f-4b6e-8d7c-9a0b1c2d3e4f"


def test_builtin_identity_summarize_allows_vars_file_expr_source():
    node = _builtin_node("summarize",
                         id="8e1b2d3c-4a5f-4b6e-8d7c-9a0b1c2d3e4f",
                         source="{{ $vars.start.output.docFile }}")
    assert_builtin_identity(node)


def test_builtin_identity_summarize_fails_without_id():
    with pytest.raises(SystemExit, match="identity is inputs.id"):
        assert_builtin_identity(_builtin_node("summarize", source=""))


def test_builtin_identity_batchtransform_rejects_uuid_in_source():
    node = _builtin_node("batchtransform",
                         id="8e1b2d3c-4a5f-4b6e-8d7c-9a0b1c2d3e4f",
                         source="9c40fd2e-58f4-45a3-93bb-0dbe38a72e10")
    with pytest.raises(SystemExit, match="FILE REFERENCE"):
        assert_builtin_identity(node)


def test_builtin_identity_rejects_instance_model_block():
    node = _builtin_node("analyzefiles",
                         source="3f2a9c1e-7b4d-4e8a-9c5f-1d2e3a4b5c6d")
    node["model"] = {"source": True}
    with pytest.raises(SystemExit, match="instance 'model' block"):
        assert_builtin_identity(node)


# ── assert_context_inputs (M4) ───────────────────────────────────────────────


CONTEXT_INDEX_ID = "de5819d5-a687-4059-988e-08dee2ae3999"


def _context_node(**input_overrides):
    inputs = {
        "source": "8d1e4f6a-2b3c-4e5d-9a7f-1c0b9e8d7f6a",
        "name": "ProductKnowledge",
        "description": "Semantic retrieval over the product knowledge index",
        "indexId": CONTEXT_INDEX_ID,
        "indexName": "UiPathAgentsProductKnowledge",
        "folderKey": "040287b3-85b2-4052-a4e1-b2c14bd0c49b",
        "folderPath": "Shared/uipath-agents",
        "retrievalMode": "semantic",
        "query": {"mode": "prompt", "textValue": "",
                  "promptValue": "The query", "argumentPath": ""},
        "threshold": 0,
        "resultCount": 3,
        "fileExtension": "All",
    }
    inputs.update(input_overrides)
    inputs = {k: v for k, v in inputs.items() if v is not ...}
    return {
        "id": "productKnowledge",
        "type": (
            "uipath.agent.resource.context.index."
            f"uipathagentsproductknowledge.{CONTEXT_INDEX_ID}"
        ),
        "typeVersion": "1.0.0",
        "display": {"label": "UiPathAgentsProductKnowledge"},
        "inputs": inputs,
    }


def test_context_inputs_pass_on_full_flow_form():
    inputs = assert_context_inputs(
        _context_node(),
        expected_identity={
            "indexName": "UiPathAgentsProductKnowledge",
            "folderPath": "Shared/uipath-agents",
        },
    )
    assert inputs["retrievalMode"] == "semantic"


def test_context_inputs_accept_all_lowercase_modes():
    for mode in ("semantic", "structured", "deeprag", "batchtransform"):
        assert_context_inputs(_context_node(retrievalMode=mode))


def test_context_inputs_reject_camelcase_retrieval_mode():
    # validate does NOT catch this — the camelCase value matches none of the
    # schema's lowercase conditionals and silently misroutes to semantic.
    with pytest.raises(SystemExit, match="all-lowercase"):
        assert_context_inputs(_context_node(retrievalMode="deepRAG"))


def test_context_inputs_reject_missing_retrieval_mode():
    with pytest.raises(SystemExit, match="retrievalMode"):
        assert_context_inputs(_context_node(retrievalMode=...))


def test_context_inputs_reject_wrong_identity():
    with pytest.raises(SystemExit, match="indexName"):
        assert_context_inputs(
            _context_node(indexName="SomeOtherIndex"),
            expected_identity={"indexName": "UiPathAgentsProductKnowledge"},
        )


def test_context_inputs_reject_index_id_type_suffix_mismatch():
    with pytest.raises(SystemExit, match="index-GUID suffix"):
        assert_context_inputs(
            _context_node(indexId="11111111-2222-4333-8444-555555555555")
        )


def test_context_inputs_tolerate_absent_index_id():
    # indexId is part of the copy-from-inputDefaults guidance but the
    # cross-check only fires when present.
    assert_context_inputs(_context_node(indexId=...))


def test_context_inputs_reject_derived_settings_union():
    with pytest.raises(SystemExit, match="FLAT"):
        assert_context_inputs(
            _context_node(settings={"retrievalMode": "semantic"})
        )


def test_context_inputs_reject_context_type_and_resource_type():
    with pytest.raises(SystemExit, match="contextType"):
        assert_context_inputs(_context_node(contextType="index"))
    with pytest.raises(SystemExit, match="resourceType"):
        assert_context_inputs(_context_node(**{"$resourceType": "context"}))


# ---------------------------------------------------------------------------
# assert_escalation_inputs (M5)
# ---------------------------------------------------------------------------

def _escalation_app(**overrides):
    app = {
        "appName": "HumanReviewEscalation",
        "resourceKey": "1f2e3d4c-5b6a-4978-8899-aabbccddeeff",
        "folderName": "solution_folder",
        "appVersion": 1,
        "inputSchema": {
            "type": "object",
            "properties": {"Content": {"type": "string"}, "Comment": {"type": "string"}},
        },
        "outputSchema": {
            "type": "object",
            "properties": {"Comment": {"type": "string"}},
        },
        "inputSchemaDotnetTypeMapping": {"Content": "System.String", "Comment": "System.String"},
        "outputSchemaDotnetTypeMapping": {"Comment": "System.String"},
    }
    app.update(overrides)
    return {k: v for k, v in app.items() if v is not ...}


def _escalation_node(**input_overrides):
    inputs = {
        "source": "b4f0d2c8-6a1e-4f7b-9c3d-2e5a8b0d4f61",
        "name": "HumanReview",
        "description": "Escalate uncertain cases to a human reviewer",
        "type": "app-task",
        "app": _escalation_app(),
        "recipients": [{"type": 3, "value": "reviewer@example.com"}],
        "outcomeMapping": {"approve": "continue", "reject": "continue"},
        "_additionalProps": {"taskTitle": "Review request", "priority": "medium", "labels": []},
        "_notifications": False,
        "_appInputs": None,
    }
    inputs.update(input_overrides)
    inputs = {k: v for k, v in inputs.items() if v is not ...}
    return {
        "id": "humanReview",
        "type": "uipath.agent.resource.escalation.coded-action-app",
        "typeVersion": "1.1",
        "display": {"label": "HumanReview"},
        "inputs": inputs,
    }


EXPECTED_ESCALATION_APP = {
    "appName": "HumanReviewEscalation",
    "folderName": "solution_folder",
}


def test_escalation_inputs_pass_on_full_flow_form():
    inputs = assert_escalation_inputs(
        _escalation_node(), expected_app=EXPECTED_ESCALATION_APP
    )
    assert inputs["app"]["appName"] == "HumanReviewEscalation"


def test_escalation_inputs_tolerate_absent_type_and_outcome_mapping():
    # `type` defaults to app-task via the resolver; outcomeMapping is
    # projection-nullable — absence is legal authoring.
    assert_escalation_inputs(_escalation_node(type=..., outcomeMapping=...))


def test_escalation_inputs_accept_draft_app_version_zero():
    # Draft apps carry ActionSchema version 0; projection coerces falsy to 1.
    assert_escalation_inputs(_escalation_node(app=_escalation_app(appVersion=0)))


def test_escalation_inputs_reject_quick_form_type_on_app_node():
    with pytest.raises(SystemExit, match="app-task"):
        assert_escalation_inputs(_escalation_node(type="quick-form"))


def test_escalation_inputs_reject_missing_app():
    with pytest.raises(SystemExit, match=r"inputs\.app"):
        assert_escalation_inputs(_escalation_node(app=...))


def test_escalation_inputs_reject_wrong_app_binding():
    with pytest.raises(SystemExit, match="folderName"):
        assert_escalation_inputs(
            _escalation_node(app=_escalation_app(folderName="Shared/Wrong")),
            expected_app=EXPECTED_ESCALATION_APP,
        )


def test_escalation_inputs_reject_non_uuid_resource_key():
    with pytest.raises(SystemExit, match="resourceKey"):
        assert_escalation_inputs(
            _escalation_node(app=_escalation_app(resourceKey="HumanReviewEscalation"))
        )


def test_escalation_inputs_accept_uppercase_resource_key():
    # Tenant-provided casing — unlike the authored lowercase inputs.source.
    assert_escalation_inputs(
        _escalation_node(app=_escalation_app(resourceKey="1F2E3D4C-5B6A-4978-8899-AABBCCDDEEFF"))
    )


def test_escalation_inputs_reject_schema_less_app():
    # Validate only checks app PRESENCE — a bare {appName, resourceKey,
    # folderName} passes validate but derives an EMPTY task form.
    with pytest.raises(SystemExit, match="inputSchema"):
        assert_escalation_inputs(
            _escalation_node(app=_escalation_app(inputSchema=..., outputSchema=...))
        )


def test_escalation_inputs_reject_empty_recipients():
    with pytest.raises(SystemExit, match="recipients"):
        assert_escalation_inputs(_escalation_node(recipients=[]))
    with pytest.raises(SystemExit, match="recipients"):
        assert_escalation_inputs(_escalation_node(recipients=[{"type": 3, "value": ""}]))


def test_escalation_inputs_reject_bad_outcome_mapping_value():
    with pytest.raises(SystemExit, match="outcomeMapping"):
        assert_escalation_inputs(
            _escalation_node(outcomeMapping={"approve": "resume"})
        )


def test_escalation_inputs_reject_invalid_priority():
    # Projection silently degrades unknown priorities to "medium"; validate
    # does not catch the drift — this checker is the only gate.
    with pytest.raises(SystemExit, match="priority"):
        assert_escalation_inputs(
            _escalation_node(
                _additionalProps={"taskTitle": "", "priority": "urgent", "labels": []}
            )
        )


def test_escalation_inputs_reject_derived_channels():
    with pytest.raises(SystemExit, match="channels"):
        assert_escalation_inputs(_escalation_node(channels=[{"type": "actionCenter"}]))


def test_escalation_inputs_reject_sidecar_resource_fields():
    with pytest.raises(SystemExit, match="resourceType"):
        assert_escalation_inputs(_escalation_node(**{"$resourceType": "escalation"}))
    with pytest.raises(SystemExit, match="escalationType"):
        assert_escalation_inputs(_escalation_node(escalationType=0))
    with pytest.raises(SystemExit, match="isEnabled"):
        assert_escalation_inputs(_escalation_node(isEnabled=True))
    with pytest.raises(SystemExit, match="taskTitleV2"):
        assert_escalation_inputs(_escalation_node(taskTitleV2={"type": "textBuilder"}))
    # Projection-carried fields — hydration never writes them back, so an
    # authored node carrying them ported a sidecar resource.json.
    with pytest.raises(SystemExit, match="referenceKey"):
        assert_escalation_inputs(_escalation_node(referenceKey=""))
    with pytest.raises(SystemExit, match="folderPath"):
        assert_escalation_inputs(_escalation_node(folderPath="solution_folder"))


def test_escalation_inputs_reject_quick_form_schema_on_app_task():
    with pytest.raises(SystemExit, match="quick-form-only"):
        assert_escalation_inputs(
            _escalation_node(schema={"fields": [], "outcomes": []})
        )


# ---------------------------------------------------------------------------
# assert_connector_inputs / assert_connector_bindings (M6)
# ---------------------------------------------------------------------------

CONN_ID = "2dc0d640-eac6-445f-9f0c-d5654c4f3b1a"
CONN_FOLDER_KEY = "040287B3-85B2-4052-A4E1-B2C14BD0C49B"  # any-case tolerated


def _connector_detail(**overrides):
    detail = {
        "connector": "uipath-uipath-airdk",
        "connectionId": CONN_ID,
        "connectionResourceId": CONN_ID,
        "connectionFolderKey": CONN_FOLDER_KEY,
        "method": "POST",
        "endpoint": "/v2/webSearch",
        "uiPathActivityTypeId": "de237ff4-fac6-34dc-b4a5-8d0708c99e15",
        "errorState": {"issues": []},
        "bodyParameters": {"query": '{{prompt: "The natural language query"}}'},
        "configuration": '=jsonString:{"essentialConfiguration":{"objectName":"v2::webSearch"}}',
    }
    detail.update(overrides)
    return {k: v for k, v in detail.items() if v is not ...}


def _connector_node(detail=..., **input_overrides):
    inputs = {
        "source": "7f3c2a10-9e4b-4c8d-a1f2-5b6d7e8f9a0b",
        "name": "WebSearch",
        "description": "Performs a web search operation.",
        "detail": _connector_detail() if detail is ... else detail,
    }
    inputs.update(input_overrides)
    inputs = {k: v for k, v in inputs.items() if v is not ...}
    return {
        "id": "webSearch",
        "type": "uipath.agent.resource.tool.connector.uipath-uipath-airdk.web-search",
        "typeVersion": "1.0.0",
        "display": {"label": "Web Search"},
        "inputs": inputs,
    }


def test_connector_inputs_pass_on_cli_populated_form():
    detail = assert_connector_inputs(_connector_node())
    assert detail["connectionId"] == CONN_ID


def test_connector_inputs_reject_missing_or_empty_detail():
    with pytest.raises(SystemExit, match="node configure"):
        assert_connector_inputs(_connector_node(detail=None))
    with pytest.raises(SystemExit, match="node configure"):
        assert_connector_inputs(_connector_node(detail={}))


def test_connector_inputs_reject_non_uuid_connection_identity():
    with pytest.raises(SystemExit, match="connectionId"):
        assert_connector_inputs(
            _connector_node(detail=_connector_detail(connectionId="my-connection"))
        )
    with pytest.raises(SystemExit, match="connectionFolderKey"):
        assert_connector_inputs(
            _connector_node(detail=_connector_detail(connectionFolderKey=""))
        )


def test_connector_inputs_reject_missing_endpoint_or_method():
    with pytest.raises(SystemExit, match="endpoint"):
        assert_connector_inputs(
            _connector_node(detail=_connector_detail(endpoint="v2/webSearch"))
        )
    with pytest.raises(SystemExit, match="method"):
        assert_connector_inputs(
            _connector_node(detail=_connector_detail(method=""))
        )


def test_connector_inputs_reject_hand_written_configuration():
    # fieldsContainer-only blob = the hand-authored shape that passes
    # validate but misses essentialConfiguration and fails at runtime.
    with pytest.raises(SystemExit, match="essentialConfiguration"):
        assert_connector_inputs(
            _connector_node(
                detail=_connector_detail(
                    configuration='{"fieldsContainer":{"inputFields":[]}}'
                )
            )
        )
    with pytest.raises(SystemExit, match="essentialConfiguration"):
        assert_connector_inputs(
            _connector_node(detail=_connector_detail(configuration=...))
        )


def test_connector_inputs_reject_derived_resource_fields():
    with pytest.raises(SystemExit, match="properties"):
        assert_connector_inputs(
            _connector_node(properties={"toolPath": "/v2/webSearch"})
        )
    with pytest.raises(SystemExit, match="inputSchema"):
        assert_connector_inputs(_connector_node(inputSchema={"type": "object"}))
    with pytest.raises(SystemExit, match="iconUrl"):
        assert_connector_inputs(_connector_node(iconUrl="https://x/image"))
    with pytest.raises(SystemExit, match="resourceType"):
        assert_connector_inputs(_connector_node(**{"$resourceType": "tool"}))


def test_connector_inputs_reject_missing_name_or_description():
    with pytest.raises(SystemExit, match="name"):
        assert_connector_inputs(_connector_node(name=""))
    with pytest.raises(SystemExit, match="description"):
        assert_connector_inputs(_connector_node(description=...))


def _connector_flow_bindings(**overrides):
    rows = {
        "conn": {
            "id": "b1",
            "name": "uipath-uipath-airdk connection",
            "type": "string",
            "resource": "connection",
            "resourceKey": CONN_ID,
            "propertyAttribute": "ConnectionId",
            "default": CONN_ID,
        },
        "folder": {
            "id": "b2",
            "name": "FolderKey",
            "type": "string",
            "resource": "connection",
            "resourceKey": CONN_ID,
            "propertyAttribute": "FolderKey",
            "default": CONN_FOLDER_KEY,
        },
    }
    rows.update(overrides)
    return {"bindings": [r for r in rows.values() if r is not None]}


def test_connector_bindings_pass_on_cli_written_rows():
    rows = assert_connector_bindings(_connector_flow_bindings(), CONN_ID)
    assert len(rows) == 2


def test_connector_bindings_reject_missing_or_mispointed_rows():
    with pytest.raises(SystemExit, match="ConnectionId"):
        assert_connector_bindings(_connector_flow_bindings(conn=None), CONN_ID)
    with pytest.raises(SystemExit, match="FolderKey"):
        assert_connector_bindings(_connector_flow_bindings(folder=None), CONN_ID)
    # Row exists but points at a different connection than detail.connectionId
    with pytest.raises(SystemExit, match="ConnectionId"):
        assert_connector_bindings(
            _connector_flow_bindings(), "99999999-9999-4999-8999-999999999999"
        )
    # FolderKey default must be a UUID, not a display name
    bad = _connector_flow_bindings()
    bad["bindings"][1]["default"] = "uipath-agents"
    with pytest.raises(SystemExit, match="FolderKey"):
        assert_connector_bindings(bad, CONN_ID)


def test_connector_bindings_ignore_non_connection_rows():
    flow = _connector_flow_bindings()
    flow["bindings"].append(
        {"id": "b3", "name": "name", "resource": "process",
         "resourceKey": "x", "propertyAttribute": "ConnectionId", "default": CONN_ID}
    )
    assert_connector_bindings(flow, CONN_ID)
