"""Tests for the lowcode_scaffold fixture helpers."""

import json
import sys
from pathlib import Path

SETUP = Path(__file__).resolve().parents[1] / "_setup"
sys.path.insert(0, str(SETUP))

import lowcode_scaffold as s  # noqa: E402


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_stable_id_is_deterministic_and_distinct():
    assert s.stable_id("a", "b") == s.stable_id("a", "b")
    assert s.stable_id("a", "b") != s.stable_id("a", "c")


def test_string_props_omits_empty_description():
    props = s.string_props({"a": "Alpha", "b": ""})
    assert props["a"] == {"type": "string", "description": "Alpha"}
    assert props["b"] == {"type": "string"}


def test_apply_agent_patches_both_copies_and_entry_points(tmp_path):
    project = s.write_baseline_lowcode_agent(tmp_path / "ReviewSol")
    schema_in = {"type": "object", "properties": s.string_props({"q": "Question"}), "required": ["q"]}
    schema_out = {"type": "object", "properties": s.string_props({"a": "Answer"})}
    s.apply_agent(project, system="You are X.", user="{{input.q}}", input_schema=schema_in,
                  output_schema=schema_out, settings={"temperature": 0.7}, guardrails=[{"id": "g"}])
    for base in (project, project / ".agent-builder"):
        agent = _load(base / "agent.json")
        assert agent["inputSchema"] == schema_in
        assert agent["outputSchema"] == schema_out
        assert agent["settings"]["temperature"] == 0.7
        assert agent["settings"]["model"] == s.BASELINE_SETTINGS["model"]
        assert agent["guardrails"] == [{"id": "g"}]
        system = next(m for m in agent["messages"] if m["role"] == "system")
        assert system["content"] == "You are X."
        ep = _load(base / "entry-points.json")["entryPoints"][0]
        assert ep["input"] == schema_in and ep["output"] == schema_out


def test_write_tool_writes_resource_and_returns_binding(tmp_path):
    project = s.write_baseline_lowcode_agent(tmp_path / "ReviewSol")
    binding = s.write_tool(project, "get_order", "Get an order.", {"order_id": "Order ID"},
                           required=["order_id"], outputs={"status": "Order status"})
    res = _load(project / "resources" / "get_order" / "resource.json")
    assert res["$resourceType"] == "tool" and res["type"] == "process"
    assert res["inputSchema"]["required"] == ["order_id"]
    assert res["outputSchema"]["properties"]["status"]["description"] == "Order status"
    assert binding["key"] == "get_order"


def test_write_tool_accepts_full_output_schema(tmp_path):
    project = s.write_baseline_lowcode_agent(tmp_path / "ReviewSol")
    out = {"type": "object", "properties": {"state": {"type": "string", "enum": ["Up", "Down"]}}}
    s.write_tool(project, "t", "T.", {}, outputs=out, tool_type="agent")
    res = _load(project / "resources" / "t" / "resource.json")
    assert res["outputSchema"] == out and res["type"] == "agent"


def test_write_context_index(tmp_path):
    project = s.write_baseline_lowcode_agent(tmp_path / "ReviewSol")
    s.write_context_index(project, "Policies", "HR policy PDFs.", "hr-policies", "Policy question",
                          threshold=0, result_count=20)
    res = _load(project / "resources" / "Policies" / "resource.json")
    assert res["$resourceType"] == "context" and res["contextType"] == "index"
    assert res["settings"]["threshold"] == 0 and res["settings"]["resultCount"] == 20
    assert res["settings"]["query"]["description"] == "Policy question"


def test_write_escalation(tmp_path):
    project = s.write_baseline_lowcode_agent(tmp_path / "ReviewSol")
    s.write_escalation(project, "Supervisor", "Escalate to a supervisor.", "supervisor@example.com")
    res = _load(project / "resources" / "Supervisor" / "resource.json")
    assert res["$resourceType"] == "escalation" and res["isEnabled"] is True
    assert res["channels"][0]["recipients"] == [{"type": 3, "value": "supervisor@example.com"}]


def test_write_evals_replaces_evaluators_and_datapoints(tmp_path):
    project = s.write_baseline_lowcode_agent(tmp_path / "ReviewSol")
    ev = s.equality_evaluator("Exact")
    s.write_evals(project, [ev], [{"name": "d1", "inputs": {"q": "x"}, "expectedOutput": {"a": "y"}}])
    files = sorted(p.name for p in (project / "evals" / "evaluators").glob("*.json"))
    assert files == [ev["fileName"]]
    es = _load(project / "evals" / "eval-sets" / "evaluation-set-default.json")
    assert es["evaluatorRefs"] == [ev["id"]]
    assert es["evaluations"][0]["expectedOutput"] == {"a": "y"}
    assert es["evaluations"][0]["evalSetId"] == s.EVAL_SET_ID


def test_builtin_guardrail_shape():
    g = s.builtin_guardrail("PII", "pii_detection", ["Tool"], {"$actionType": "block", "reason": "r"},
                            match_names=["send_email"])
    assert g["$guardrailType"] == "builtInValidator"
    assert g["selector"] == {"scopes": ["Tool"], "matchNames": ["send_email"]}


def test_scaffold_imports_on_python_without_pep604_runtime():
    assert isinstance(s.apply_agent.__annotations__["settings"], str)
