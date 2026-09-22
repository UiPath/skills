"""Unit tests for check_scheduled_trigger_flow.py — purely structural, no CLI.

Run with ``pytest tests/tasks/uipath-maestro-flow/smoke/test_check_scheduled_trigger_flow.py``.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

CHECKER = Path(__file__).resolve().parent / "check_scheduled_trigger_flow.py"

_spec = importlib.util.spec_from_file_location("_check_scheduled_trigger", CHECKER)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
CYCLE_RE = _mod.CYCLE_RE
REQUESTED_CYCLE = _mod.REQUESTED_CYCLE


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
    base = {"entryPointId": "ep-1", "timerType": "timeCycle", "timerValue": "R/PT1H"}
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


def test_interval_passes(tmp_path: Path) -> None:
    _write_flow(tmp_path, _well_formed())
    r = _run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr


def test_valid_but_wrong_cadence_fails(tmp_path: Path) -> None:
    """Grammar validity is not the bar. The task asks for hourly; a daily flow
    is well-formed and the wrong answer, and must not score full credit."""
    p = _well_formed()
    p["nodes"][0] = _scheduled_node(timerValue="R/P1D")
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "not the one the task asked for" in _out(r)


def test_requested_cycle_matches_the_task_yaml() -> None:
    """The pinned cadence must stay in step with the prompt that asks for it."""
    yaml = (Path(__file__).resolve().parent / "scheduled_trigger.yaml").read_text()
    assert f"`{REQUESTED_CYCLE}`" in yaml


def test_stray_timer_preset_is_ignored(tmp_path: Path) -> None:
    """`timerPreset` is not in the node's schema; validate tolerates it as an
    extra key, so an agent that writes both must not be docked here."""
    p = _well_formed()
    p["nodes"][0] = _scheduled_node(timerPreset="R/PT1H")
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr


def test_cycle_in_timer_preset_only_fails(tmp_path: Path) -> None:
    """The exact regression this checker missed: the cycle expression written to
    `timerPreset` with no `timerValue` passed the old checker but failed
    `uip maestro flow validate` with REQUIRED_FIELD timerValue."""
    p = _well_formed()
    node = _scheduled_node(timerPreset="R/PT1H")
    node["inputs"].pop("timerValue")
    p["nodes"][0] = node
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "timervalue" in _out(r)


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


def test_missing_timer_type_fails(tmp_path: Path) -> None:
    """`validate` tolerates a missing `timerType` (the definition's `required`
    array names only `timerValue`), but `model.values` consumes it, so the task
    and this checker both demand it."""
    p = _well_formed()
    node = _scheduled_node()
    node["inputs"].pop("timerType")
    p["nodes"][0] = node
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "timecycle" in _out(r)


def test_bad_cycle_fails(tmp_path: Path) -> None:
    p = _well_formed()
    p["nodes"][0] = _scheduled_node(timerValue="hourly")
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "iso 8601" in _out(r)


def test_zero_duration_fails(tmp_path: Path) -> None:
    """R/PT0H is a never-firing schedule; the registry pattern rejects a zero
    duration outright, so no separate all-zero guard is needed."""
    p = _well_formed()
    p["nodes"][0] = _scheduled_node(timerValue="R/PT0H")
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "iso 8601" in _out(r)


def test_multi_unit_duration_fails(tmp_path: Path) -> None:
    """The registry pattern allows exactly one duration unit — R/PT2H30M is
    rejected by `validate`, so the checker must reject it too."""
    p = _well_formed()
    p["nodes"][0] = _scheduled_node(timerValue="R/PT2H30M")
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "iso 8601" in _out(r)


def test_out_of_range_duration_fails(tmp_path: Path) -> None:
    p = _well_formed()
    p["nodes"][0] = _scheduled_node(timerValue="R/PT24H")
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "iso 8601" in _out(r)


def test_missing_timer_value_fails(tmp_path: Path) -> None:
    p = _well_formed()
    node = _scheduled_node()
    node["inputs"].pop("timerValue")
    p["nodes"][0] = node
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


# ── Cycle-expression grammar (registry pattern, independent of cadence) ──────


def test_grammar_accepts_midnight_cron_with_no_digit_one_to_nine() -> None:
    """Regression for the deleted all-zero guard. The old checker rejected any
    cycle expression containing no digit 1-9 as "never-firing"; that reasoning
    holds for an interval but not for cron, where `0 0 0 * * ? *` is daily at
    midnight. Every other cron fixture here contains a 9 or a 2, so only this
    case would catch the guard being reintroduced."""
    assert CYCLE_RE.fullmatch("0 0 0 * * ? *")


def test_grammar_accepts_cron_and_anchored_intervals() -> None:
    for value in (
        "0 0 */1 * * ? *",              # hourly on the hour
        "0 0 9 ? * MON-FRI",            # weekdays at 09:00
        "0 0 2 1 * ? *",                # 02:00 on the 1st
        "R/2026-05-14T09:00:00Z/P1W",   # weekly, anchored to a start instant
        "R/PT5M",
        "R/P1W",
    ):
        assert CYCLE_RE.fullmatch(value), value


def test_grammar_rejects_a_trailing_newline() -> None:
    """`fullmatch`, not `match`: Python's `$` also matches before a trailing
    newline, the JavaScript `$` the platform runs the same pattern under does
    not."""
    assert not CYCLE_RE.fullmatch(f"{REQUESTED_CYCLE}\n")


def test_grammar_rejects_multi_unit_out_of_range_and_zero_durations() -> None:
    """The interval form takes exactly ONE non-zero, in-range unit — so no
    arbitrary period (every 2.5 hours, every 90 minutes) is expressible."""
    for value in ("R/PT2H30M", "R/PT150M", "R/PT90M", "R/PT24H", "R/PT60M", "R/PT0H", "custom", "hourly"):
        assert not CYCLE_RE.fullmatch(value), value
