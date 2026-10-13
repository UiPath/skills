"""Unit tests for the inline-agent checkers' new pass/fail logic.

Each case builds a minimal solution in a temp dir and runs the real checker
script with that dir as cwd, the way coder-eval runs it. Covered:

- `inline_wiring.assert_external_tool_shape` + `assert_tool_folder_binding`
  through `check_inline_external_rpa_tool.py`: the SDK and v1 shapes pass;
  an unwitnessed (location, folderPath) pair, a wrong binding folder and a
  missing binding fail.
- `inline_wiring.assert_inline_agent_definition`: an `agent.json` with no
  system prompt fails.
- `check_inline_is_connector_tool.assert_connection_binding`: a real
  connection UUID passes; a placeholder, the SDK stub and a missing binding
  fail.
"""

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

SHARED = Path(__file__).resolve().parent
AGENT_ID = "7b767e04-85be-4d44-b702-756c1ace91e4"
TOOL_ID = "6f0c6a43-2d55-4c0b-9a51-0e2f0f8f5f11"
RPA_FOLDER = "Shared/uipath-agents/FibonacciRPA"
CONNECTION_ID = "971fc639-5f0e-4d58-a7c1-2b8e8d7d1c3a"

AGENT_JSON = {
    "version": "1.1.0",
    "id": AGENT_ID,
    "projectId": AGENT_ID,
    "type": "lowCode",
    "settings": {"model": "gpt-5.4"},
    "messages": [
        {"role": "system", "content": "You compute Fibonacci numbers with the tool."},
        {"role": "user", "content": "Index: {{input.index}}"},
    ],
}


def run_checker(name: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SHARED / name)],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def folder_binding(folder: str) -> dict:
    return {
        "id": "bFibonacciRPAFolderPath",
        "name": "folderPath",
        "resource": "process",
        "resourceKey": f"{RPA_FOLDER}.FibonacciRPA",
        "default": folder,
        "propertyAttribute": "folderPath",
    }


def build_rpa_solution(
    root: Path,
    *,
    location: str,
    folder_path: str,
    bindings: list | None = None,
    agent_json: dict | None = None,
) -> Path:
    project = root / "FibonacciFlowSol" / "FibonacciFlow"
    flow = {
        "nodes": [
            {"id": "agent1", "type": "uipath.agent.autonomous", "inputs": {"source": AGENT_ID}},
            {
                "id": "tool1",
                "type": f"uipath.agent.resource.tool.process.{TOOL_ID}",
                "inputs": {"source": TOOL_ID},
            },
        ],
        "edges": [
            {"sourceNodeId": "agent1", "sourcePort": "tool", "targetNodeId": "tool1", "targetPort": "input"}
        ],
        "bindings": [folder_binding(RPA_FOLDER)] if bindings is None else bindings,
    }
    write_json(project / "FibonacciFlow.flow", flow)
    write_json(project / AGENT_ID / "agent.json", agent_json or AGENT_JSON)
    write_json(
        project / AGENT_ID / "resources" / TOOL_ID / "resource.json",
        {
            "$resourceType": "tool",
            "type": "process",
            "location": location,
            "referenceKey": "f27d0f9b-1111-2222-3333-444455556666",
            "properties": {"processName": "FibonacciRPA", "folderPath": folder_path},
        },
    )
    return root


@pytest.mark.parametrize(
    ("location", "folder_path"),
    [("solution", ""), ("external", RPA_FOLDER)],
    ids=["sdk-shape", "v1-shape"],
)
def test_external_tool_witnessed_shapes_pass(tmp_path, location, folder_path):
    build_rpa_solution(tmp_path, location=location, folder_path=folder_path)
    result = run_checker("check_inline_external_rpa_tool.py", tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("location", "folder_path"),
    [("external", ""), ("solution", RPA_FOLDER), ("external", "Shared/Other")],
    ids=["external-empty", "solution-literal", "external-wrong-folder"],
)
def test_external_tool_unwitnessed_pairs_fail(tmp_path, location, folder_path):
    build_rpa_solution(tmp_path, location=location, folder_path=folder_path)
    result = run_checker("check_inline_external_rpa_tool.py", tmp_path)
    assert result.returncode != 0
    assert "(location, properties.folderPath)" in result.stderr


def test_external_tool_wrong_binding_folder_fails(tmp_path):
    build_rpa_solution(
        tmp_path, location="solution", folder_path="", bindings=[folder_binding("Shared/Other")]
    )
    result = run_checker("check_inline_external_rpa_tool.py", tmp_path)
    assert result.returncode != 0
    assert "no folderPath binding" in result.stderr


def test_external_tool_missing_binding_fails(tmp_path):
    build_rpa_solution(tmp_path, location="solution", folder_path="", bindings=[])
    result = run_checker("check_inline_external_rpa_tool.py", tmp_path)
    assert result.returncode != 0
    assert "found: none" in result.stderr


def test_agent_json_without_system_prompt_fails(tmp_path):
    agent = copy.deepcopy(AGENT_JSON)
    agent["messages"] = [m for m in agent["messages"] if m["role"] != "system"]
    build_rpa_solution(tmp_path, location="solution", folder_path="", agent_json=agent)
    result = run_checker("check_inline_external_rpa_tool.py", tmp_path)
    assert result.returncode != 0
    assert "no non-empty 'system' message" in result.stderr


def test_agent_json_missing_fails(tmp_path):
    build_rpa_solution(tmp_path, location="solution", folder_path="")
    (tmp_path / "FibonacciFlowSol" / "FibonacciFlow" / AGENT_ID / "agent.json").unlink()
    result = run_checker("check_inline_external_rpa_tool.py", tmp_path)
    assert result.returncode != 0
    assert "agent.json" in result.stderr


CONNECTOR = "uipath-uipath-airdk"


def build_is_solution(root: Path, connection_id: object, *, with_binding: bool = True) -> Path:
    project = root / "ResearchFlowSol" / "ResearchFlow"
    flow = {
        "nodes": [
            {"id": "agent1", "type": "uipath.agent.autonomous", "inputs": {"source": AGENT_ID}},
            {"id": "tool1", "type": f"uipath.agent.resource.tool.connector.{CONNECTOR}.web-search"},
        ],
        "edges": [
            {"sourceNodeId": "agent1", "sourcePort": "tool", "targetNodeId": "tool1", "targetPort": "input"}
        ],
    }
    write_json(project / "ResearchFlow.flow", flow)
    write_json(project / AGENT_ID / "agent.json", AGENT_JSON)
    write_json(
        project / AGENT_ID / "resources" / TOOL_ID / "resource.json",
        {"$resourceType": "tool", "type": "integration", "id": TOOL_ID, "isEnabled": True},
    )
    resources = []
    if with_binding:
        resources.append(
            {
                "resource": "connection",
                "metadata": {"Connector": CONNECTOR},
                "value": {"ConnectionId": {"defaultValue": connection_id}},
            }
        )
    write_json(project / "bindings_v2.json", {"version": "2.0", "resources": resources})
    return root


def test_is_connector_real_connection_passes(tmp_path):
    build_is_solution(tmp_path, CONNECTION_ID)
    result = run_checker("check_inline_is_connector_tool.py", tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "connection_id",
    ["<connection-id>", "TODO", "00000000-0000-0000-0000-000000000001", "", None],
    ids=["placeholder", "todo", "sdk-stub", "empty", "null"],
)
def test_is_connector_placeholder_connection_fails(tmp_path, connection_id):
    build_is_solution(tmp_path, connection_id)
    result = run_checker("check_inline_is_connector_tool.py", tmp_path)
    assert result.returncode != 0
    assert "no bindings_v2.json connection binding" in result.stderr


def test_is_connector_missing_binding_fails(tmp_path):
    build_is_solution(tmp_path, CONNECTION_ID, with_binding=False)
    result = run_checker("check_inline_is_connector_tool.py", tmp_path)
    assert result.returncode != 0
