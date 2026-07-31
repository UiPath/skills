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
    assert_definition_present,
    assert_edge,
    assert_embedded_agent,
    find_autonomous_agent_node,
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
