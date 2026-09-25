"""The agent-resource sidecar gate: a wired node with no agent-project resource fails.

Fixtures mirror the 2026-09-24 analyst/resolution artifacts.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SHARED = Path(__file__).resolve().parent
CHECKER = SHARED / "check_agent_resource_sidecars.py"

AGENT_SOURCE = "53a1c27a-109c-4daa-87bf-a8a2504b51da"
RESOURCE_ID = "95a1fe95-c69e-479f-8778-852dcdb888ab"
INDEX_ID = "cc45b9b4-dbf6-47b3-40ac-08debc0cec5b"
CONTEXT_TYPE = f"uipath.agent.resource.context.index.billing-dispute-sop-index.{INDEX_ID}"


def _flow(resource_node_type: str = CONTEXT_TYPE, *, resource_source: str = RESOURCE_ID) -> dict:
    return {
        "id": "analyst",
        "nodes": [
            {"id": "start", "type": "core.trigger.manual"},
            {"id": "analyze", "type": "uipath.agent.autonomous", "inputs": {"source": AGENT_SOURCE}},
            {"id": "ctx", "type": resource_node_type,
             "inputs": {"source": resource_source, "indexId": INDEX_ID}},
            {"id": "end", "type": "core.control.end"},
        ],
        "edges": [
            {"sourceNodeId": "start", "sourcePort": "output", "targetNodeId": "analyze", "targetPort": "input"},
            {"sourceNodeId": "analyze", "sourcePort": "context", "targetNodeId": "ctx", "targetPort": "input"},
            {"sourceNodeId": "analyze", "sourcePort": "success", "targetNodeId": "end", "targetPort": "input"},
        ],
    }


def _project(root: Path, flow: dict) -> Path:
    """Write `<root>/Sol/Proj/Proj.flow` plus the agent's own `agent.json`."""
    project = root / "Sol" / "Proj"
    (project / AGENT_SOURCE).mkdir(parents=True)
    (project / "Proj.flow").write_text(json.dumps(flow), encoding="utf-8")
    (project / AGENT_SOURCE / "agent.json").write_text(
        json.dumps({"version": "1.1.0", "type": "lowCode"}), encoding="utf-8"
    )
    return project


def _resource_json(resource_id: str = RESOURCE_ID, resource_type: str = "context") -> dict:
    return {
        "$resourceType": resource_type,
        "id": resource_id,
        "referenceKey": None,
        "name": "Billing Dispute SOP Index",
        "description": 'Context grounding index "Billing Dispute SOP Index".',
        "contextType": "index",
        "folderPath": "Shared/uipath-maestro-flow/BillingDispute",
        "indexName": "Billing Dispute SOP Index",
        "settings": {
            "retrievalMode": "semantic",
            "query": {"variant": "dynamic", "description": "billing dispute policy"},
            "folderPathPrefix": {"variant": "static"},
            "threshold": 0,
            "resultCount": 5,
            "fileExtension": {"value": "All"},
        },
    }


def _run(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER)], cwd=cwd, capture_output=True, text=True, check=False
    )


def _output(result: subprocess.CompletedProcess[str]) -> str:
    """Both streams: `fail()` raises SystemExit (stderr), the pass path prints (stdout)."""
    return result.stdout + result.stderr


def _write_resource(project: Path, body: dict, *, directory: str = RESOURCE_ID) -> None:
    target = project / AGENT_SOURCE / "resources" / directory / "resource.json"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(body), encoding="utf-8")


def test_a_wired_node_without_its_resource_fails(tmp_path: Path) -> None:
    _project(tmp_path, _flow())
    result = _run(tmp_path)
    assert result.returncode == 1, _output(result)
    assert "the agent project declares none" in _output(result)
    # The message has to name the id to declare and where, or it sends the reader
    # hunting.
    assert RESOURCE_ID in _output(result)
    assert f"{AGENT_SOURCE}/resources/" in _output(result)


def test_the_file_form_passes(tmp_path: Path) -> None:
    project = _project(tmp_path, _flow())
    _write_resource(project, _resource_json())
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 agent resource(s) joined" in result.stdout


def test_the_inline_agent_json_form_passes_too(tmp_path: Path) -> None:
    # `uip agent refresh` reads `resources/*/resource.json` AND `agent.json`'s own
    # `resources[]` into one list, so the gate must accept either.
    project = _project(tmp_path, _flow())
    agent_json = project / AGENT_SOURCE / "agent.json"
    agent_json.write_text(
        json.dumps({"version": "1.1.0", "type": "lowCode", "resources": [_resource_json()]}),
        encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_a_resource_under_the_wrong_id_does_not_count(tmp_path: Path) -> None:
    # The join is the node's `inputs.source`. A resource the node cannot reach is
    # the same defect with extra files.
    project = _project(tmp_path, _flow())
    other = "ffffffff-ffff-4fff-8fff-ffffffffffff"
    _write_resource(project, _resource_json(other), directory=other)
    result = _run(tmp_path)
    assert result.returncode == 1, _output(result)
    assert other in _output(result)


def test_a_name_directory_with_a_uuid_id_passes(tmp_path: Path) -> None:
    # The join is the `id` FIELD, not the directory name. Real agent projects name
    # the directory after the resource — `resources/CountSources/`,
    # `resources/WebSearch/`, `resources/SupportKnowledge/` are all real — and carry
    # a uuid in `id`. `compile` happens to name the directory for the uuid; keying on
    # the directory would pass the SDK's output and fail every designer-authored
    # project.
    project = _project(tmp_path, _flow())
    _write_resource(project, _resource_json(), directory="Billing Dispute SOP Index")
    result = _run(tmp_path)
    assert result.returncode == 0, _output(result)


def test_a_resource_with_no_id_falls_back_to_its_directory(tmp_path: Path) -> None:
    # The product's own example resource carries no `id` at all
    # (`UiPath.Tool.Agent/Examples/.../Resources/ProcessResource/resource.json`), so
    # the directory name is all there is to match on.
    project = _project(tmp_path, _flow())
    body = _resource_json()
    del body["id"]
    _write_resource(project, body)
    result = _run(tmp_path)
    assert result.returncode == 0, _output(result)


def test_the_wrong_resource_type_fails(tmp_path: Path) -> None:
    project = _project(tmp_path, _flow())
    _write_resource(project, _resource_json(resource_type="tool"))
    result = _run(tmp_path)
    assert result.returncode == 1, _output(result)
    assert "needs 'context'" in _output(result)


def test_an_unwired_resource_node_fails(tmp_path: Path) -> None:
    flow = _flow()
    flow["edges"] = [e for e in flow["edges"] if e["targetNodeId"] != "ctx"]
    _project(tmp_path, flow)
    result = _run(tmp_path)
    assert result.returncode == 1, _output(result)
    assert "joined to no agent handle" in _output(result)


def test_a_flow_with_no_agent_resources_is_silent(tmp_path: Path) -> None:
    flow = _flow()
    flow["nodes"] = [n for n in flow["nodes"] if n["id"] != "ctx"]
    flow["edges"] = [e for e in flow["edges"] if e["targetNodeId"] != "ctx"]
    _project(tmp_path, flow)
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "nothing to join" in result.stdout


@pytest.mark.parametrize("directory", [RESOURCE_ID, "Billing Dispute SOP Index"])
def test_both_directory_conventions_pass(tmp_path: Path, directory: str) -> None:
    # The real arm difference is the directory name: `compile` names it for the
    # uuid, a designer-authored project names it for the resource. The join is the
    # `id` field either way.
    project = _project(tmp_path, _flow())
    _write_resource(project, _resource_json(), directory=directory)
    assert _run(tmp_path).returncode == 0


@pytest.mark.parametrize("node_type", [
    # Generated by `uip agent refresh` from the flow's own connector node.
    "uipath.agent.resource.tool.connector.uipath-salesforce-slack.send-message",
    # Writing the file makes `flow validate` fail after refresh (#806).
    "uipath.agent.resource.tool.ixp.vendor-invoices.7f4e2d73-8915-4c61-b35c-06ab9f7e67a5",
    "uipath.agent.resource.tool.clientside",
    # Need a tenant read, or a toolType the compiler cannot map.
    "uipath.agent.resource.tool.mcp.ticket-mcp.7f4e2d73-8915-4c61-b35c-06ab9f7e67a5",
    "uipath.agent.resource.tool.a2a.research-agent.7f4e2d73-8915-4c61-b35c-06ab9f7e67a5",
    "uipath.agent.resource.tool.builtin.summarize",
    # Needs the Action Center app's ActionSchema; v1 emits the bare type, v2 a
    # suffixed one, and neither is gated.
    "uipath.agent.resource.escalation",
    "uipath.agent.resource.escalation.coded-action-app",
    # A feature, not a resource.
    "uipath.agent.resource.memory.support-history.7f4e2d73-8915-4c61-b35c-06ab9f7e67a5",
])
def test_exempt_families_pass_without_a_file(tmp_path: Path, node_type: str) -> None:
    # Gating a family nothing can emit is a criterion no one passes — and for ixp
    # and clientside the gate would contradict `flow validate` outright.
    _project(tmp_path, _flow(node_type))
    result = _run(tmp_path)
    assert result.returncode == 0, _output(result)


@pytest.mark.parametrize("kind", ["process", "api", "processorchestration", "flow", "agent", "function"])
def test_every_deployed_tool_kind_is_gated(tmp_path: Path, kind: str) -> None:
    # The kinds flow-builder-sdk#806 emits a file for, so a missing one is a defect
    # rather than a design decision.
    node_type = f"uipath.agent.resource.tool.{kind}.7f4e2d73-8915-4c61-b35c-06ab9f7e67a5"
    _project(tmp_path, _flow(node_type))
    result = _run(tmp_path)
    assert result.returncode == 1, _output(result)

    project = _project(tmp_path / kind, _flow(node_type))
    _write_resource(project, _resource_json(resource_type="tool"))
    assert _run(tmp_path / kind).returncode == 0
