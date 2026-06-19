"""Unit tests for check_api_workflow_flow.py — purely structural, no CLI.

Run with ``pytest tests/tasks/uipath-maestro-flow/single_node/api_workflow``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


CHECKER = Path(__file__).resolve().parent / "check_api_workflow_flow.py"


def _flow_dir(tmp_path: Path) -> Path:
    d = tmp_path / "NameToAge" / "NameToAge"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_flow(tmp_path: Path, payload: dict[str, Any]) -> None:
    d = _flow_dir(tmp_path)
    (d / "NameToAge.flow").write_text(json.dumps(payload))
    # assert_flow_has_node_type needs a Flow project.uiproj alongside the .flow.
    (d / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))


def _run(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def _well_formed() -> dict[str, Any]:
    """Mirror the actual failing-run artifact shape."""
    return {
        "version": "1.0.0",
        "nodes": [
            {"id": "start", "type": "core.trigger.manual"},
            {
                "id": "callApiWorkflow",
                "type": "uipath.core.api-workflow.84e2a2f6-50d1-4753-bae2-d873eda90b61",
                "inputs": {"name": "tomasz"},
            },
            {"id": "end", "type": "core.control.end"},
        ],
        "edges": [
            {"sourceNodeId": "start", "targetNodeId": "callApiWorkflow"},
            {"sourceNodeId": "callApiWorkflow", "targetNodeId": "end"},
        ],
        "bindings": [
            {
                "id": "bCallApiWorkflowName",
                "name": "name",
                "resource": "process",
                "resourceKey": "Shared/uipath-maestro-flow/NameToAge APIWF.API Workflow",
                "resourceSubType": "Api",
            },
            {
                "id": "bCallApiWorkflowFolderPath",
                "name": "folderPath",
                "resource": "process",
                "resourceKey": "Shared/uipath-maestro-flow/NameToAge APIWF.API Workflow",
                "resourceSubType": "Api",
            },
        ],
    }


def test_well_formed_flow_passes(tmp_path: Path) -> None:
    _write_flow(tmp_path, _well_formed())
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_missing_api_workflow_node_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    payload["nodes"] = [n for n in payload["nodes"] if "api-workflow" not in n["type"]]
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0


def test_missing_binding_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    payload["bindings"] = []
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "binding" in (result.stdout + result.stderr).lower()


def test_binding_without_resource_key_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    payload["bindings"] = [
        {"id": "b1", "resource": "process", "resourceSubType": "Api", "resourceKey": ""},
    ]
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0


def test_wrong_name_input_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if "api-workflow" in n["type"]:
            n["inputs"] = {"name": "alice"}
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "tomasz" in (result.stdout + result.stderr)


def test_name_input_case_insensitive_passes(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if "api-workflow" in n["type"]:
            n["inputs"] = {"name": "Tomasz"}
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
