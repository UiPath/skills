"""Unit tests for check_transform_group_by_flow.py — purely structural, no CLI.

Run with ``pytest tests/tasks/uipath-maestro-flow/single_node/transform_group_by``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


CHECKER = Path(__file__).resolve().parent / "check_transform_group_by_flow.py"


def _flow_dir(tmp_path: Path) -> Path:
    d = tmp_path / "TransformGroupByDemo" / "TransformGroupByDemo"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_flow(tmp_path: Path, payload: dict[str, Any]) -> None:
    d = _flow_dir(tmp_path)
    (d / "TransformGroupByDemo.flow").write_text(json.dumps(payload))
    # Match the canonical Flow project layout (a project.uiproj alongside the .flow).
    (d / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))


def _run(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def _group_by_node() -> dict[str, Any]:
    return {
        "id": "groupByDept",
        "type": "core.action.transform.group-by",
        "typeVersion": "1.0",
        "display": {"label": "Group by Department"},
        "inputs": {
            "collection": "$vars.employees.output.items",
            "operations": [
                {
                    "id": "op1",
                    "type": "groupBy",
                    "config": {
                        "groupByField": "department",
                        "aggregations": [
                            {"id": "a1", "field": "", "operation": "count", "alias": "headcount"},
                            {"id": "a2", "field": "salary", "operation": "sum", "alias": "totalSalary"},
                        ],
                    },
                }
            ],
        },
        "outputs": {
            "output": {
                "type": "object",
                "description": "The return value of the transform",
                "source": "=result.response",
                "var": "output",
            },
            "error": {
                "type": "object",
                "description": "Error information if the transform fails",
                "source": "=Error",
                "var": "error",
            },
        },
    }


def _well_formed() -> dict[str, Any]:
    return {
        "version": "1.0.0",
        "nodes": [
            {"id": "start", "type": "core.trigger.manual"},
            _group_by_node(),
            {"id": "end", "type": "core.control.end"},
        ],
        "edges": [
            {"sourceNodeId": "start", "targetNodeId": "groupByDept"},
            {"sourceNodeId": "groupByDept", "targetNodeId": "end"},
        ],
        "variables": {
            "globals": [
                {
                    "id": "employees",
                    "direction": "in",
                    "type": "array",
                    "defaultValue": [
                        {"department": "eng", "salary": 100},
                        {"department": "eng", "salary": 120},
                        {"department": "sales", "salary": 90},
                    ],
                }
            ]
        },
    }


def test_well_formed_flow_passes(tmp_path: Path) -> None:
    _write_flow(tmp_path, _well_formed())
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_map_variant_fails(tmp_path: Path) -> None:
    """A core.action.transform.map node MUST fail the exact-type check."""
    payload = _well_formed()
    for n in payload["nodes"]:
        if n.get("type") == "core.action.transform.group-by":
            n["type"] = "core.action.transform.map"
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "core.action.transform.group-by" in (result.stdout + result.stderr)


def test_generic_transform_variant_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if n.get("type") == "core.action.transform.group-by":
            n["type"] = "core.action.transform"
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0


def test_collection_wrapped_in_js_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if n.get("type") == "core.action.transform.group-by":
            n["inputs"]["collection"] = "=js:$vars.employees.output.items"
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "=js:" in (result.stdout + result.stderr)


def test_inline_array_collection_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if n.get("type") == "core.action.transform.group-by":
            n["inputs"]["collection"] = '[{"department":"eng"}]'
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0


def test_empty_aggregations_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if n.get("type") == "core.action.transform.group-by":
            n["inputs"]["operations"][0]["config"]["aggregations"] = []
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "aggregations" in (result.stdout + result.stderr)


def test_aggregation_missing_alias_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if n.get("type") == "core.action.transform.group-by":
            n["inputs"]["operations"][0]["config"]["aggregations"] = [
                {"id": "a1", "operation": "count", "alias": ""}
            ]
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0


def test_empty_group_by_field_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if n.get("type") == "core.action.transform.group-by":
            n["inputs"]["operations"][0]["config"]["groupByField"] = ""
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0


def test_missing_type_version_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if n.get("type") == "core.action.transform.group-by":
            n.pop("typeVersion", None)
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "typeVersion" in (result.stdout + result.stderr)


def test_wrong_output_source_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if n.get("type") == "core.action.transform.group-by":
            n["outputs"]["output"]["source"] = "=response"
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0
