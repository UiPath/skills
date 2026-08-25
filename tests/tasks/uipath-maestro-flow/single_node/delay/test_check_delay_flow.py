"""Unit tests for check_delay_flow.py — purely structural, no CLI.

Run with ``pytest tests/tasks/uipath-maestro-flow/single_node/delay``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


CHECKER = Path(__file__).resolve().parent / "check_delay_flow.py"


def _flow_dir(tmp_path: Path) -> Path:
    d = tmp_path / "DelayDemo" / "DelayDemo"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_flow(tmp_path: Path, payload: dict[str, Any]) -> None:
    d = _flow_dir(tmp_path)
    (d / "DelayDemo.flow").write_text(json.dumps(payload))
    # A Flow project.uiproj alongside the .flow keeps the fixture realistic.
    (d / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))


def _run(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def _well_formed() -> dict[str, Any]:
    """Trigger -> Delay -> End, fixed-duration preset."""
    return {
        "version": "1.0.0",
        "nodes": [
            {"id": "start", "type": "core.trigger.manual"},
            {
                "id": "wait15min",
                "type": "core.logic.delay",
                "typeVersion": "1.0",
                "display": {"label": "Wait 15 Minutes"},
                "inputs": {
                    "timerType": "timeDuration",
                    "timerPreset": "PT15M",
                },
            },
            {"id": "end", "type": "core.control.end"},
        ],
        "edges": [
            {"sourceNodeId": "start", "targetNodeId": "wait15min"},
            {"sourceNodeId": "wait15min", "targetNodeId": "end"},
        ],
    }


def test_well_formed_flow_passes(tmp_path: Path) -> None:
    _write_flow(tmp_path, _well_formed())
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_custom_duration_with_timer_value_passes(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if n["type"] == "core.logic.delay":
            n["inputs"] = {
                "timerType": "timeDuration",
                "timerPreset": "custom",
                "timerValue": "P1DT5H30M",
            }
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_time_date_with_timer_date_passes(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if n["type"] == "core.logic.delay":
            n["inputs"] = {
                "timerType": "timeDate",
                "timerPreset": "custom",
                "timerDate": "=js:$vars.scheduledDate",
            }
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_missing_timer_type_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if n["type"] == "core.logic.delay":
            n["inputs"] = {"timerPreset": "PT15M"}
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "timertype" in (result.stdout + result.stderr).lower()


def test_missing_delay_node_fails(tmp_path: Path) -> None:
    """Only non-trigger node is some other type — no core.logic.delay present."""
    payload = _well_formed()
    for n in payload["nodes"]:
        if n["type"] == "core.logic.delay":
            n["type"] = "core.logic.script"
            n["inputs"] = {}
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "core.logic.delay" in (result.stdout + result.stderr)


def test_custom_duration_missing_timer_value_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if n["type"] == "core.logic.delay":
            n["inputs"] = {"timerType": "timeDuration", "timerPreset": "custom"}
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "timervalue" in (result.stdout + result.stderr).lower()


def test_missing_type_version_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    for n in payload["nodes"]:
        if n["type"] == "core.logic.delay":
            n.pop("typeVersion", None)
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "typeversion" in (result.stdout + result.stderr).lower()


def test_missing_outgoing_edge_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    payload["edges"] = [{"sourceNodeId": "start", "targetNodeId": "wait15min"}]
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "outgoing" in (result.stdout + result.stderr).lower()


def test_missing_incoming_edge_fails(tmp_path: Path) -> None:
    payload = _well_formed()
    payload["edges"] = [{"sourceNodeId": "wait15min", "targetNodeId": "end"}]
    _write_flow(tmp_path, payload)
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "incoming" in (result.stdout + result.stderr).lower()
