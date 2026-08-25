"""Unit tests for check_transform_filter_flow.py — purely structural, no CLI.

Run with ``pytest tests/tasks/uipath-maestro-flow/single_node/transform_filter``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


CHECKER = Path(__file__).resolve().parent / "check_transform_filter_flow.py"


def _flow_dir(tmp_path: Path) -> Path:
    d = tmp_path / "TransformFilterDemo" / "TransformFilterDemo"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_flow(tmp_path: Path, payload: dict[str, Any]) -> None:
    d = _flow_dir(tmp_path)
    (d / "TransformFilterDemo.flow").write_text(json.dumps(payload))
    # Sibling Flow manifest, matching the api_workflow test style.
    (d / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))


def _run(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def _filter_node(node_type: str = "core.action.transform.filter") -> dict[str, Any]:
    return {
        "id": "filterAmount",
        "type": node_type,
        "typeVersion": "1.0",
        "display": {"label": "Filter Big Orders"},
        "inputs": {
            "collection": "$vars.items.output",
            "operations": [
                {
                    "id": "op1",
                    "type": "filter",
                    "config": {
                        "operation": "and",
                        "filters": [
                            {
                                "id": "f1",
                                "field": "amount",
                                "condition": "greater_equal",
                                "value": 100,
                            }
                        ],
                    },
                }
            ],
        },
        "outputs": {
            "output": {"type": "object", "source": "=result.response", "var": "output"},
            "error": {"type": "object", "source": "=Error", "var": "error"},
        },
    }


def _well_formed() -> dict[str, Any]:
    return {
        "version": "1.0.0",
        "nodes": [
            {"id": "start", "type": "core.trigger.manual"},
            _filter_node(),
            {"id": "end", "type": "core.control.end"},
        ],
        "edges": [
            {"sourceNodeId": "start", "targetNodeId": "filterAmount"},
            {"sourceNodeId": "filterAmount", "targetNodeId": "end"},
        ],
    }


def test_well_formed_flow_passes(tmp_path: Path) -> None:
    _write_flow(tmp_path, _well_formed())
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


# ── Acceptance: wrong transform variants must FAIL ──────────────────────────


def test_map_variant_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    payload["nodes"] = [
        {"id": "start", "type": "core.trigger.manual"},
        _filter_node("core.action.transform.map"),
        {"id": "end", "type": "core.control.end"},
    ]
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0, result.stdout + result.stderr


def test_generic_transform_variant_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    payload["nodes"] = [
        {"id": "start", "type": "core.trigger.manual"},
        _filter_node("core.action.transform"),
        {"id": "end", "type": "core.control.end"},
    ]
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0, result.stdout + result.stderr


def test_group_by_variant_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    payload["nodes"] = [
        {"id": "start", "type": "core.trigger.manual"},
        _filter_node("core.action.transform.group-by"),
        {"id": "end", "type": "core.control.end"},
    ]
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0, result.stdout + result.stderr


# ── Field-level rejections ──────────────────────────────────────────────────


def test_js_wrapped_collection_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    payload["nodes"][1]["inputs"]["collection"] = "=js:$vars.items.output"
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "=js:" in (result.stdout + result.stderr)


def test_inline_array_collection_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    payload["nodes"][1]["inputs"]["collection"] = '[{"amount": 100}]'
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0


def test_expression_filter_value_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    flt = payload["nodes"][1]["inputs"]["operations"][0]["config"]["filters"][0]
    flt["value"] = "$vars.threshold"
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "literal" in (result.stdout + result.stderr).lower()


def test_bad_condition_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    flt = payload["nodes"][1]["inputs"]["operations"][0]["config"]["filters"][0]
    flt["condition"] = "greater"
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0


def test_empty_filters_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    payload["nodes"][1]["inputs"]["operations"][0]["config"]["filters"] = []
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0


def test_missing_error_source_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    del payload["nodes"][1]["outputs"]["error"]
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0


def test_empty_type_version_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    payload["nodes"][1]["typeVersion"] = ""
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0
