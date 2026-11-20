"""Checker-level tests for check_inline_mcp_server_tool.py.

No run of this task exists (it is skipped), so the project is built here in
the shape the old checker and inline-in-flow.md document: an inline agent
whose `inputs.source` names a UUID folder holding `agent.json` and
`resources/<uuid>/resource.json`, and a `uipath.agent.resource.mcp.*` node on
the agent's `tool` handle. Studio Web's `new.flow` name is used, which the old
checker's pinned `DevToolsFlowSol/DevToolsFlow/DevToolsFlow.flow` path missed
unless the folders were named exactly so.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_inline_mcp_server_tool.py"
AGENT_DIR = "4f1d0c1e-5c0a-4d55-9d8e-0f0d2a8b9c11"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_inline_mcp_server_tool", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _flow(edge_port="tool"):
    return {
        "nodes": [
            {"id": "start", "type": "core.trigger.manual"},
            {"id": "devAgent", "type": "uipath.agent.autonomous", "inputs": {"source": AGENT_DIR}},
            {"id": "githubMcp", "type": "uipath.agent.resource.mcp.githubmcp.9b0c"},
            {"id": "end", "type": "core.control.end"},
        ],
        "edges": [
            {"sourceNodeId": "start", "sourcePort": "output", "targetNodeId": "devAgent", "targetPort": "input"},
            {"sourceNodeId": "devAgent", "sourcePort": edge_port, "targetNodeId": "githubMcp", "targetPort": "input"},
            {"sourceNodeId": "devAgent", "sourcePort": "success", "targetNodeId": "end", "targetPort": "input"},
        ],
        "variables": {"globals": [
            {"id": "repository", "direction": "in", "type": "string"},
            {"id": "question", "direction": "in", "type": "string"},
            {"id": "answer", "direction": "out", "type": "string"},
        ]},
    }


def _project(root: Path, *, flow=None, resource=True, enabled=True):
    project = root / "DevToolsFlow" / "DevToolsFlow"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    (project / "new.flow").write_text(json.dumps(flow or _flow()))
    agent = project / AGENT_DIR
    (agent / "resources" / "7c1e").mkdir(parents=True)
    (agent / "agent.json").write_text(json.dumps({"type": "lowCode"}))
    if resource:
        (agent / "resources" / "7c1e" / "resource.json").write_text(json.dumps({
            "$resourceType": "mcp", "name": "GitHubMcp", "description": "GitHub tools",
            "isEnabled": enabled, "id": "2d9f6a1e-1111-4222-8333-944455556666", "tools": [],
        }))


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _main(monkeypatch, mode, payload=None):
    checker = _load_checker()
    if payload is not None:
        monkeypatch.setattr(checker, "run_debug", lambda **_: payload)
    monkeypatch.setattr("sys.argv", ["check", mode])
    checker.main()


def _payload(answer, agent_status="Completed"):
    return {
        "finalStatus": "Completed",
        "elementExecutions": [
            {"elementId": "start", "status": "Completed"},
            {"elementId": "devAgent", "status": agent_status},
            {"elementId": "end", "status": "Completed"},
        ],
        "variables": {"globals": {
            "repository": "octocat/Hello-World", "question": "default branch?", "answer": answer,
        }},
    }


def test_wiring_in_a_studio_web_project_passes(sandbox, monkeypatch, capsys):
    _project(sandbox)
    _main(monkeypatch, "wiring")
    assert "uses GitHubMcp" in capsys.readouterr().out


def test_wiring_without_the_resource_file_fails(sandbox, monkeypatch):
    _project(sandbox, resource=False)
    with pytest.raises(SystemExit) as exc:
        _main(monkeypatch, "wiring")
    assert "GitHubMcp MCP server" in str(exc.value)


def test_wiring_with_a_disabled_resource_fails(sandbox, monkeypatch):
    _project(sandbox, enabled=False)
    with pytest.raises(SystemExit) as exc:
        _main(monkeypatch, "wiring")
    assert "is not enabled" in str(exc.value)


def test_mcp_node_on_the_wrong_handle_fails(sandbox, monkeypatch):
    _project(sandbox, flow=_flow(edge_port="context"))
    with pytest.raises(SystemExit) as exc:
        _main(monkeypatch, "wiring")
    assert "'tool' handle" in str(exc.value)


def test_run_that_answers_the_default_branch_passes(sandbox, monkeypatch):
    _project(sandbox)
    _main(monkeypatch, "run", _payload("The default branch of octocat/Hello-World is `master`."))


def test_run_whose_agent_faulted_fails(sandbox, monkeypatch):
    _project(sandbox)
    with pytest.raises(SystemExit) as exc:
        _main(monkeypatch, "run", _payload("master", agent_status="Faulted"))
    assert "did not complete" in str(exc.value)


def test_run_with_a_wrong_answer_fails(sandbox, monkeypatch):
    _project(sandbox)
    with pytest.raises(SystemExit) as exc:
        _main(monkeypatch, "run", _payload("I could not reach the repository."))
    assert "answer" in str(exc.value)
