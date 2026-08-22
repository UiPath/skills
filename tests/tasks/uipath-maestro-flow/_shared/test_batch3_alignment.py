"""Regression coverage for Batch 3 same-ground checker routing."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


TASK_ROOT = Path(__file__).resolve().parent.parent


def _run(relative: str, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TASK_ROOT / relative), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _write_flow(path: Path, nodes: list[dict], bindings: list[dict] | None = None) -> None:
    path.write_text(
        json.dumps({"nodes": nodes, "edges": [], "bindings": bindings or []}),
        encoding="utf-8",
    )


def test_bindings_checker_accepts_root_sdk_emit(tmp_path: Path) -> None:
    _write_flow(
        tmp_path / "BindingsMulti.flow",
        [
            {"id": "a", "type": "uipath.connector.one.operation"},
            {"id": "b", "type": "uipath.connector.two.operation"},
        ],
    )

    result = _run(
        "bindings/check_bindings.py",
        "connector_node_count",
        "**/BindingsMulti*.flow",
        "2",
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_multiselect_checker_accepts_root_sdk_emit(tmp_path: Path) -> None:
    _write_flow(
        tmp_path / "ComplexArrayTest.flow",
        [
            {
                "id": "slack",
                "type": "uipath.connector.uipath-salesforce-slack.create-group-direct-message",
                "inputs": {"detail": {"bodyParameters": {"users": ["U1", "U2"]}}},
            }
        ],
    )

    result = _run(
        "connector_features/check_multiselect_flow.py",
        "populated",
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_enum_checker_prefers_solution_flow_over_root_scratch(tmp_path: Path) -> None:
    _write_flow(tmp_path / "EnumTest.flow", [])
    project = tmp_path / "EnumTest" / "project.uiproj"
    project.parent.mkdir()
    project.write_text('{"ProjectType":"Flow"}', encoding="utf-8")
    _write_flow(
        project.parent / "EnumTest.flow",
        [{"id": "start", "type": "core.trigger.manual"}],
    )

    result = _run(
        "connector_features/check_enum_flow.py",
        "**/EnumTest*.flow",
        "structure",
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "EnumTest/EnumTest.flow" in result.stdout
