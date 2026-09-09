"""Unit tests for check_timer_connector.py against synthetic caseplans.

Builds a conformant plan and breaks it one way at a time, asserting the checker
notices each break AND stays quiet on the good plan. The fixture mirrors the REAL
emitted shape: stages carry data.label / data.tasks, tasks carry displayName /
entryConditions / isRequired / shouldRunOnlyOnce at the TOP level with data left {}
on an unresolved placeholder.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_timer_connector.py"
TIME_CYCLE = "R10/2026-09-01T06:00:00Z/P1D"


def cond(rule: str) -> dict:
    return {"id": f"c_{rule[:8]}", "rules": [[{"id": "r1", "rule": rule}]]}


def task(name: str, ttype: str, rule: str, *, required: bool = True,
         run_once: bool = False) -> dict:
    return {
        "id": f"t_{name.replace(' ', '')[:8]}",
        "type": ttype,
        "displayName": name,
        "isRequired": required,
        "shouldRunOnlyOnce": run_once,
        "entryConditions": [cond(rule)],
        "data": {},
    }


def stage(name: str, tasks: list[dict], entry: str) -> dict:
    return {
        "id": f"s_{name.replace(' ', '')[:8]}",
        "type": "case-management:Stage",
        "data": {
            "label": name,
            "tasks": [[t] for t in tasks],
            "entryConditions": [cond(entry)],
            "exitConditions": [{**cond("required-tasks-completed"),
                                "type": "exit-only", "marksStageComplete": True}],
        },
    }


def good_plan() -> dict:
    collect = stage("Collect Records", [
        task("Extract Account Records", "rpa", "runs-sequentially"),
        task("Score Account Records", "process", "runs-sequentially"),
    ], "case-entered")
    signals = stage("External Signals", [
        task("Wait For Regulator Feed", "wait-for-connector", "runs-sequentially"),
        task("Fetch Regulator Notices", "execute-connector-activity", "runs-sequentially"),
    ], "selected-stage-completed")
    disp = stage("Disposition", [
        task("Hold For Corrections", "wait-for-timer", "runs-sequentially", run_once=True),
        task("Record Sweep Outcome", "api-workflow", "runs-sequentially"),
        task("Attach Late Evidence", "action", "adhoc", required=False),
    ], "selected-stage-completed")
    return {
        "nodes": [
            {"id": "trigger_1", "type": "uipath.case.trigger",
             "data": {"typeVersion": "1.0.0", "display": {"label": "Trigger 1"},
                      "inputs": {"serviceType": "timer", "timerType": "timeCycle",
                                 "timeCycle": TIME_CYCLE}}},
            collect, signals, disp,
        ],
        "edges": [],
        "metadata": {"caseExitRules": [
            {"id": "ce1", "marksCaseComplete": True,
             "rules": [[{"rule": "required-stages-completed"}]]}]},
        "layout": {},
    }


def run(tmp_path: Path, plan: dict) -> subprocess.CompletedProcess[str]:
    (tmp_path / "caseplan.json").write_text(json.dumps(plan), encoding="utf-8")
    return subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path,
                          capture_output=True, text=True)


def find_task(plan: dict, name: str) -> dict:
    for node in plan["nodes"]:
        for group in (node.get("data") or {}).get("tasks") or []:
            for t in group:
                if t.get("displayName") == name:
                    return t
    raise AssertionError(f"no task {name}")


# ------------------------------------------------------------------ control

def test_conformant_plan_passes(tmp_path: Path):
    r = run(tmp_path, good_plan())
    assert r.returncode == 0, f"conformant plan rejected:\n{r.stdout}\n{r.stderr}"


# ------------------------------------------------------- the headline gaps

def test_manual_trigger_instead_of_timer_is_caught(tmp_path: Path):
    """The gap this task exists to close: 8 of 11 greenfield SDDs declare Manual,
    so emitting a manual trigger is the likely wrong answer."""
    plan = good_plan()
    plan["nodes"][0]["data"]["inputs"] = {"serviceType": "None"}
    r = run(tmp_path, plan)
    assert r.returncode != 0
    assert "no timer trigger" in (r.stdout + r.stderr)


def test_rewritten_timecycle_is_caught(tmp_path: Path):
    """timeCycle is consumed verbatim — decomposing or normalising it is a defect."""
    plan = good_plan()
    plan["nodes"][0]["data"]["inputs"]["timeCycle"] = "R/P1D"
    r = run(tmp_path, plan)
    assert r.returncode != 0
    assert "timeCycle" in (r.stdout + r.stderr)


def test_run_once_nested_in_data_is_caught(tmp_path: Path):
    """case-schema.md: an envelope field misplaced inside `data` passes validate
    silently and is dead config the platform never reads."""
    plan = good_plan()
    hold = find_task(plan, "Hold For Corrections")
    del hold["shouldRunOnlyOnce"]
    hold["data"]["shouldRunOnlyOnce"] = True
    r = run(tmp_path, plan)
    assert r.returncode != 0
    out = r.stdout + r.stderr
    assert "shouldRunOnlyOnce" in out and "data" in out


def test_run_once_dropped_is_caught(tmp_path: Path):
    plan = good_plan()
    find_task(plan, "Hold For Corrections")["shouldRunOnlyOnce"] = False
    r = run(tmp_path, plan)
    assert r.returncode != 0
    assert "Run Only Once" in (r.stdout + r.stderr)


# --------------------------------------------------------- task type cover

@pytest.mark.parametrize("name,wrong", [
    ("Wait For Regulator Feed", "action"),
    ("Fetch Regulator Notices", "api-workflow"),
    ("Hold For Corrections", "process"),
])
def test_substituted_task_type_is_caught(tmp_path: Path, name: str, wrong: str):
    plan = good_plan()
    find_task(plan, name)["type"] = wrong
    r = run(tmp_path, plan)
    assert r.returncode != 0
    assert name in (r.stdout + r.stderr)


def test_namespaced_task_type_still_passes(tmp_path: Path):
    """Emitted types may be namespaced; the checker compares the trailing segment."""
    plan = good_plan()
    find_task(plan, "Extract Account Records")["type"] = "case-management:rpa"
    r = run(tmp_path, plan)
    assert r.returncode == 0, r.stdout + r.stderr


# ------------------------------------------------------------- sequencing

def test_stage_entered_instead_of_sequential_is_caught(tmp_path: Path):
    plan = good_plan()
    find_task(plan, "Score Account Records")["entryConditions"] = [cond("current-stage-entered")]
    r = run(tmp_path, plan)
    assert r.returncode != 0
    assert "runs-sequentially" in (r.stdout + r.stderr)


def test_sequential_plus_stage_entered_is_caught(tmp_path: Path):
    plan = good_plan()
    find_task(plan, "Score Account Records")["entryConditions"] = [
        cond("runs-sequentially"), cond("current-stage-entered")]
    r = run(tmp_path, plan)
    assert r.returncode != 0
    assert "current-stage-entered" in (r.stdout + r.stderr)


# ------------------------------------------------------------------ adhoc

def test_adhoc_given_an_entry_event_is_caught(tmp_path: Path):
    plan = good_plan()
    find_task(plan, "Attach Late Evidence")["entryConditions"] = [cond("current-stage-entered")]
    r = run(tmp_path, plan)
    assert r.returncode != 0
    assert "adhoc" in (r.stdout + r.stderr)


def test_adhoc_made_required_is_caught(tmp_path: Path):
    plan = good_plan()
    find_task(plan, "Attach Late Evidence")["isRequired"] = True
    r = run(tmp_path, plan)
    assert r.returncode != 0
    assert "must be optional" in (r.stdout + r.stderr)


# ------------------------------------------------------------------ shape

def test_missing_stage_is_caught(tmp_path: Path):
    plan = good_plan()
    plan["nodes"] = [n for n in plan["nodes"]
                     if (n.get("data") or {}).get("label") != "External Signals"]
    r = run(tmp_path, plan)
    assert r.returncode != 0
    assert "External Signals" in (r.stdout + r.stderr)


def test_uncompletable_case_is_caught(tmp_path: Path):
    plan = good_plan()
    plan["metadata"]["caseExitRules"] = [
        {"id": "ce1", "marksCaseComplete": False, "rules": [[{"rule": "required-stages-completed"}]]}]
    r = run(tmp_path, plan)
    assert r.returncode != 0
    assert "can never complete" in (r.stdout + r.stderr)


def test_no_caseplan_fails_loudly(tmp_path: Path):
    r = subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path,
                       capture_output=True, text=True)
    assert r.returncode != 0
