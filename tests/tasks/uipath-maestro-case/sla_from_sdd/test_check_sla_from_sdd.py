"""Unit tests for check_sla_from_sdd.py against synthetic caseplans.

The checker's whole point is catching shapes `uip maestro case validate` accepts but
that are semantically wrong — chiefly a `start-task` SLA response emitted as a
stage-entry rule instead of a task-entry rule. So these tests build a conformant plan
and then break it one way at a time, asserting the checker notices each break AND stays
quiet on the good plan.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_sla_from_sdd.py"


def sla(title: str, count: int, unit: str = "d", expr: str = "=js:true") -> dict:
    """Real shape from sla_response/templates/.../caseplan.json: flat count/unit plus
    `expression`, where the sentinel `=js:true` marks the default (ungated) row."""
    return {
        "id": f"sla_{title.replace(' ', '')[:8]}",
        "displayName": title,
        "expression": expr,
        "count": count,
        "unit": unit,
    }


def cond(rule: str, *, interrupting: bool = False, exit_type: str | None = None,
         marks: bool | None = None) -> dict:
    c: dict = {"id": f"c_{rule[:6]}", "rules": [[{"id": "r1", "rule": rule}]]}
    if interrupting:
        c["isInterrupting"] = True
    if exit_type:
        c["type"] = exit_type
    if marks is not None:
        c["marksStageComplete"] = marks
    return c


def task(name: str, entry: list[dict], *, required: bool = True) -> dict:
    """Real emitted shape (verified against a built plan): a TASK carries displayName,
    entryConditions and isRequired at the TOP level, with `data` left {} on an
    unresolved placeholder. Stages differ — they use data.label / data.tasks. Getting
    this wrong made every task look absent to the checker."""
    return {
        "id": f"t_{name.replace(' ', '')[:8]}",
        "type": "case-management:Task",
        "displayName": name,
        "isRequired": required,
        "entryConditions": entry,
        "data": {},
    }


def stage(name: str, tasks: list[dict], *, secondary: bool = False,
          slas: list[dict] | None = None, entry: list[dict] | None = None,
          exits: list[dict] | None = None) -> dict:
    data: dict = {
        "label": name,
        "tasks": [[t] for t in tasks],
        "entryConditions": entry or [cond("case-entered")],
        "exitConditions": exits or [cond("required-tasks-completed", exit_type="exit-only", marks=True)],
    }
    if secondary:
        data["stageType"] = "secondary"
        data["isRequired"] = False
    if slas:
        data["slaRules"] = slas
    return {"id": f"s_{name.replace(' ', '')[:8]}", "type": "case-management:Stage", "data": data}


def good_plan() -> dict:
    intake = stage(
        "Intake",
        [
            task("Validate Claim Details", [cond("runs-sequentially")]),
            task("Chase Missing Paperwork", [cond("sla-status-change")], required=False),
            task("Add Claim Evidence", [cond("adhoc")], required=False),
        ],
        slas=[sla("Intake SLA", 1)],
    )
    assessment = stage(
        "Assessment",
        [task("Assess Damage", [cond("runs-sequentially")])],
        slas=[sla("Assessment SLA high value", 4, "h", "=js:(vars.claimValue > 5000)"),
              sla("Assessment SLA", 2)],
        entry=[cond("selected-stage-completed")],
    )
    settlement = stage(
        "Settlement",
        [task("Issue Settlement", [cond("runs-sequentially")])],
        slas=[sla("Settlement SLA", 1)],
        entry=[cond("selected-stage-completed")],
    )
    escalation = stage(
        "Escalation Review",
        [task("Lead Escalation Review", [cond("current-stage-entered")])],
        secondary=True,
        entry=[cond("sla-status-change", interrupting=True)],
        exits=[cond("required-tasks-completed", exit_type="return-to-origin", marks=True)],
    )
    rejected = stage(
        "Claim Rejected",
        [task("Record Rejection", [cond("current-stage-entered")])],
        secondary=True,
        entry=[cond("selected-stage-exited", interrupting=True)],
    )
    return {
        "nodes": [intake, assessment, settlement, escalation, rejected],
        "edges": [],
        "metadata": {
            "slaRules": [sla("Claim resolution SLA", 5)],
            "caseExitRules": [
                {"id": "ce1", "marksCaseComplete": True,
                 "rules": [[{"rule": "required-stages-completed"}]]},
                {"id": "ce2", "marksCaseComplete": False,
                 "rules": [[{"rule": "selected-stage-completed"}]]},
            ],
        },
        "layout": {},
    }


def run(tmp_path: Path, plan: dict) -> subprocess.CompletedProcess[str]:
    (tmp_path / "caseplan.json").write_text(json.dumps(plan), encoding="utf-8")
    return subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path,
                          capture_output=True, text=True)


def find_task(plan: dict, name: str) -> dict:
    for node in plan["nodes"]:
        for group in node["data"].get("tasks") or []:
            for t in group:
                if t.get("displayName") == name:
                    return t
    raise AssertionError(f"no task {name}")


def find_stage(plan: dict, name: str) -> dict:
    for node in plan["nodes"]:
        if node["data"]["label"] == name:
            return node
    raise AssertionError(f"no stage {name}")


# --------------------------------------------------------------- control

def test_conformant_plan_passes(tmp_path: Path):
    r = run(tmp_path, good_plan())
    assert r.returncode == 0, f"conformant plan rejected:\n{r.stdout}\n{r.stderr}"


# --------------------------------------------------- the headline confusion

def test_start_task_emitted_as_stage_entry_is_caught(tmp_path: Path):
    """The defect the skill's references warn about: the start-task response emitted as
    a stage-entry rule re-enters the stage and re-runs its other tasks."""
    plan = good_plan()
    intake = find_stage(plan, "Intake")
    intake["data"]["entryConditions"].append(cond("sla-status-change", interrupting=True))
    chase = find_task(plan, "Chase Missing Paperwork")
    chase["entryConditions"] = [cond("current-stage-entered")]
    r = run(tmp_path, plan)
    assert r.returncode != 0
    out = r.stdout + r.stderr
    assert "STAGE-entry" in out or "task entry" in out


def test_start_task_in_the_wrong_stage_is_caught(tmp_path: Path):
    plan = good_plan()
    chase = find_task(plan, "Chase Missing Paperwork")
    find_stage(plan, "Intake")["data"]["tasks"] = [
        g for g in find_stage(plan, "Intake")["data"]["tasks"]
        if g[0].get("displayName") != "Chase Missing Paperwork"
    ]
    find_stage(plan, "Settlement")["data"]["tasks"].append([chase])
    r = run(tmp_path, plan)
    assert r.returncode != 0
    assert "INSIDE the breached stage" in (r.stdout + r.stderr)


# ------------------------------------------------------- other constructs

def test_flattened_condition_based_sla_is_caught(tmp_path: Path):
    plan = good_plan()
    find_stage(plan, "Assessment")["data"]["slaRules"] = [sla("Assessment SLA", 2)]
    r = run(tmp_path, plan)
    assert r.returncode != 0
    out = r.stdout + r.stderr
    # The override row is what disappeared; the message names the real field.
    assert "no gated slaRules entry" in out, out
    assert "high-value override" in out, out


def test_non_interrupting_enter_stage_lane_is_caught(tmp_path: Path):
    plan = good_plan()
    for c in find_stage(plan, "Escalation Review")["data"]["entryConditions"]:
        c.pop("isInterrupting", None)
    r = run(tmp_path, plan)
    assert r.returncode != 0
    assert "interrupting" in (r.stdout + r.stderr)


def test_missing_return_to_origin_is_caught(tmp_path: Path):
    plan = good_plan()
    find_stage(plan, "Escalation Review")["data"]["exitConditions"] = [
        cond("required-tasks-completed", exit_type="exit-only", marks=True)
    ]
    r = run(tmp_path, plan)
    assert r.returncode != 0
    assert "return-to-origin" in (r.stdout + r.stderr)


def test_missing_non_completing_case_exit_is_caught(tmp_path: Path):
    plan = good_plan()
    plan["metadata"]["caseExitRules"] = [
        c for c in plan["metadata"]["caseExitRules"] if c["marksCaseComplete"]
    ]
    r = run(tmp_path, plan)
    assert r.returncode != 0
    assert "marksCaseComplete false" in (r.stdout + r.stderr)


def test_adhoc_task_made_required_is_caught(tmp_path: Path):
    plan = good_plan()
    find_task(plan, "Add Claim Evidence")["isRequired"] = True
    r = run(tmp_path, plan)
    assert r.returncode != 0
    assert "must be optional" in (r.stdout + r.stderr)


def test_dropped_stage_sla_is_caught(tmp_path: Path):
    plan = good_plan()
    find_stage(plan, "Settlement")["data"].pop("slaRules")
    r = run(tmp_path, plan)
    assert r.returncode != 0
    assert "Settlement" in (r.stdout + r.stderr)


def test_dropped_case_sla_is_caught(tmp_path: Path):
    plan = good_plan()
    plan["metadata"].pop("slaRules")
    r = run(tmp_path, plan)
    assert r.returncode != 0
    assert "root carries no slaRules" in (r.stdout + r.stderr)


@pytest.mark.parametrize("stage_name", ["Escalation Review", "Claim Rejected"])
def test_missing_secondary_lane_is_caught(tmp_path: Path, stage_name: str):
    plan = good_plan()
    plan["nodes"] = [
        n for n in plan["nodes"] if n["data"]["label"] != stage_name
    ]
    r = run(tmp_path, plan)
    assert r.returncode != 0
    assert stage_name in (r.stdout + r.stderr)


def test_no_caseplan_fails_loudly(tmp_path: Path):
    r = subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path,
                       capture_output=True, text=True)
    assert r.returncode != 0
