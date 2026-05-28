"""Unit tests for check_transform_map_flow.py — purely structural, no CLI.

Run with ``pytest tests/tasks/uipath-maestro-flow/single_node/transform_map``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


CHECKER = Path(__file__).resolve().parent / "check_transform_map_flow.py"


def _flow_dir(tmp_path: Path) -> Path:
    d = tmp_path / "TransformMapDemo" / "TransformMapDemo"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_flow(tmp_path: Path, payload: dict[str, Any]) -> None:
    d = _flow_dir(tmp_path)
    (d / "TransformMapDemo.flow").write_text(json.dumps(payload))
    # A Flow project.uiproj alongside the .flow keeps the fixture realistic.
    (d / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))


def _run(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def _map_node(node_type: str = "core.action.transform.map") -> dict[str, Any]:
    return {
        "id": "mapNames",
        "type": node_type,
        "typeVersion": "1.0",
        "display": {"label": "Uppercase Names"},
        "inputs": {
            "collection": "$vars.people.output",
            "operations": [
                {
                    "id": "op1",
                    "type": "map",
                    "config": {
                        "keepOriginalFields": False,
                        "mappings": [
                            {
                                "id": "m1",
                                "field": "name",
                                "transformation": "uppercase",
                                "renameTo": "",
                            }
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
            _map_node(),
            {"id": "end", "type": "core.control.end"},
        ],
        "edges": [
            {"sourceNodeId": "start", "targetNodeId": "mapNames"},
            {"sourceNodeId": "mapNames", "targetNodeId": "end"},
        ],
    }


def test_well_formed_flow_passes(tmp_path: Path) -> None:
    _write_flow(tmp_path, _well_formed())
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_filter_variant_fails(tmp_path: Path) -> None:
    # Negative fixture: the .filter variant must NOT satisfy the exact-map pin.
    payload = _well_formed()
    payload["nodes"] = [
        n for n in payload["nodes"] if n.get("type") != "core.action.transform.map"
    ]
    payload["nodes"].insert(1, _map_node(node_type="core.action.transform.filter"))
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0


def test_generic_transform_variant_fails(tmp_path: Path) -> None:
    # Negative fixture: the generic core.action.transform must also fail —
    # substring matching would wrongly accept it, exact == must reject it.
    payload = _well_formed()
    payload["nodes"] = [
        n for n in payload["nodes"] if n.get("type") != "core.action.transform.map"
    ]
    payload["nodes"].insert(1, _map_node(node_type="core.action.transform"))
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0


def test_js_collection_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if n.get("type") == "core.action.transform.map":
            n["inputs"]["collection"] = "=js:$vars.people.output"
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0


def test_inline_array_collection_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if n.get("type") == "core.action.transform.map":
            n["inputs"]["collection"] = '[{"name": "alice"}]'
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0


def test_empty_mappings_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if n.get("type") == "core.action.transform.map":
            n["inputs"]["operations"][0]["config"]["mappings"] = []
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0


def test_mapping_missing_field_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if n.get("type") == "core.action.transform.map":
            n["inputs"]["operations"][0]["config"]["mappings"] = [
                {"id": "m1", "transformation": "uppercase"}
            ]
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0


def test_wrong_output_source_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if n.get("type") == "core.action.transform.map":
            n["outputs"]["output"]["source"] = "=response"
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0


def test_missing_type_version_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if n.get("type") == "core.action.transform.map":
            n.pop("typeVersion", None)
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0
