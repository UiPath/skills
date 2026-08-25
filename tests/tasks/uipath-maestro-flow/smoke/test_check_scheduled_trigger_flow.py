"""Unit tests for check_scheduled_trigger_flow.py — purely structural, no CLI.

Run with ``pytest tests/tasks/uipath-maestro-flow/smoke/test_check_scheduled_trigger_flow.py``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

CHECKER = Path(__file__).resolve().parent / "check_scheduled_trigger_flow.py"


def _write_flow(tmp_path: Path, payload: dict[str, Any]) -> None:
    d = tmp_path / "ScheduledReport" / "ScheduledReport"
    d.mkdir(parents=True, exist_ok=True)
    (d / "ScheduledReport.flow").write_text(json.dumps(payload))
    (d / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))


def _run(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER)], cwd=str(cwd), capture_output=True, text=True
    )


def _out(r: subprocess.CompletedProcess[str]) -> str:
    return (r.stdout + r.stderr).lower()


def _scheduled_node(**inputs: Any) -> dict[str, Any]:
    base = {"entryPointId": "ep-1", "timerType": "timeCycle", "timerPreset": "R/PT1H"}
    base.update(inputs)
    return {
        "id": "start",
        "type": "core.trigger.scheduled",
        "typeVersion": "1.1",
        "display": {"label": "Every Hour"},
        "inputs": base,
        "outputs": {"output": {"type": "object", "source": "=result.response", "var": "output"}},
    }


def _well_formed() -> dict[str, Any]:
    """A single scheduled trigger that replaced the manual trigger (trigger-only flow)."""
    return {
        "version": "1.2",
        "nodes": [_scheduled_node()],
        "edges": [],
        "definitions": [
            {"nodeType": "core.trigger.scheduled", "version": "1.1",
             "model": {"type": "bpmn:StartEvent", "eventDefinition": "bpmn:TimerEventDefinition"}},
        ],
    }


def test_preset_passes(tmp_path: Path) -> None:
    _write_flow(tmp_path, _well_formed())
    r = _run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr


def test_custom_with_timer_value_passes(tmp_path: Path) -> None:
    p = _well_formed()
    p["nodes"][0] = _scheduled_node(timerPreset="custom", timerValue="R/PT45M")
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr


def test_manual_node_present_fails(tmp_path: Path) -> None:
    p = _well_formed()
    p["nodes"].append({"id": "m1", "type": "core.trigger.manual", "typeVersion": "1.0",
                       "display": {"label": "Manual trigger"}, "inputs": {"entryPointId": "ep-2"}})
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "manual" in _out(r)


def test_no_scheduled_node_fails(tmp_path: Path) -> None:
    p = _well_formed()
    p["nodes"] = [{"id": "s1", "type": "core.action.script", "typeVersion": "1.0",
                   "display": {"label": "X"}, "inputs": {"script": "return {};"}}]
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "core.trigger.scheduled" in (r.stdout + r.stderr)


def test_wrong_timer_type_fails(tmp_path: Path) -> None:
    p = _well_formed()
    p["nodes"][0] = _scheduled_node(timerType="timeDuration")
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "timecycle" in _out(r)


def test_bad_preset_fails(tmp_path: Path) -> None:
    p = _well_formed()
    p["nodes"][0] = _scheduled_node(timerPreset="hourly")
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "iso 8601" in _out(r)


def test_zero_duration_preset_fails(tmp_path: Path) -> None:
    p = _well_formed()
    p["nodes"][0] = _scheduled_node(timerPreset="R/PT0H")
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "all-zero" in _out(r)


def test_custom_missing_timer_value_fails(tmp_path: Path) -> None:
    p = _well_formed()
    p["nodes"][0] = _scheduled_node(timerPreset="custom")
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "timervalue" in _out(r)


def test_missing_type_version_fails(tmp_path: Path) -> None:
    p = _well_formed()
    p["nodes"][0].pop("typeVersion", None)
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "typeversion" in _out(r)


def test_incoming_edge_fails(tmp_path: Path) -> None:
    p = _well_formed()
    p["edges"] = [{"id": "e1", "sourceNodeId": "x", "sourcePort": "output",
                   "targetNodeId": "start", "targetPort": "input"}]
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "incoming" in _out(r)


def test_manual_definition_present_fails(tmp_path: Path) -> None:
    p = _well_formed()
    p["definitions"].append({"nodeType": "core.trigger.manual", "version": "1.0",
                             "model": {"type": "bpmn:StartEvent"}})
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "manual" in _out(r)


def test_missing_event_definition_fails(tmp_path: Path) -> None:
    p = _well_formed()
    for d in p["definitions"]:
        if d["nodeType"] == "core.trigger.scheduled":
            d["model"].pop("eventDefinition", None)
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "timereventdefinition" in _out(r)


def test_missing_scheduled_definition_fails(tmp_path: Path) -> None:
    p = _well_formed()
    p["definitions"] = []
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "definitions" in _out(r)
