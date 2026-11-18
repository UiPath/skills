"""The task's own setup and inline graders, run on a copy of the fixture.

Studio Web's harness opens the workspace's .uipx as the session's solution and
exports the agent's edits back to the workspace. A pre_run that moves the
fixture out of the workspace leaves Studio Web on an empty solution
(adhoc-2026-11-18_14-40-01: "The sandbox changed after the bridge opened it",
then the agent found /solution empty). The graders must read the workspace copy.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

HERE = Path(__file__).parent
TASK = yaml.safe_load((HERE / "designer_saved_plan.yaml").read_text())
PLAN = Path("ExpenseDesignerSaved/CMGoldenExpense/caseplan.case")


def _criterion(prefix: str) -> str:
    return next(c["command"] for c in TASK["success_criteria"] if c["description"].startswith(prefix))


def _run(command: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, timeout=60)


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    shutil.copytree(HERE / "fixtures" / "ExpenseDesignerSaved", tmp_path / "ExpenseDesignerSaved")
    return tmp_path


def _add_cool_off(workspace: Path) -> None:
    path = workspace / PLAN
    plan = json.loads(path.read_text())
    stage = next(n for n in plan["nodes"] if n["data"].get("label") == "Stage 7 - user select")
    stage["data"]["tasks"].append([{
        "id": "tCoolOff1", "displayName": "Final cool-off", "type": "wait-for-timer",
        "isRequired": False, "data": {"timeDuration": "PT10M"},
    }])
    path.write_text(json.dumps(plan))


def test_pre_run_keeps_the_solution_in_the_workspace():
    for step in TASK["pre_run"]:
        assert "ExpenseDesignerSaved" not in step["command"], step["command"]


def test_edit_check_fails_on_the_untouched_fixture(workspace: Path):
    result = _run(_criterion("The edit landed"), workspace)
    assert result.returncode == 1, result.stderr
    assert "cooloff=0 optional=0 total=15" in result.stdout


def test_edit_check_passes_once_the_optional_timer_is_added(workspace: Path):
    _add_cool_off(workspace)
    result = _run(_criterion("The edit landed"), workspace)
    assert result.returncode == 0, result.stdout + result.stderr


def test_designer_fields_check_passes_on_the_fixture_and_fails_on_a_lowered_version(workspace: Path):
    command = _criterion("What the Designer wrote survives")
    assert _run(command, workspace).returncode == 0
    path = workspace / PLAN
    plan = json.loads(path.read_text())
    plan["version"] = "32.0.3"
    path.write_text(json.dumps(plan))
    assert _run(command, workspace).returncode == 1


def test_second_plan_file_check(workspace: Path):
    command = _criterion("No second plan file")
    assert _run(command, workspace).returncode == 0
    (workspace / PLAN).with_name("caseplan.json").write_text("{}")
    assert _run(command, workspace).returncode != 0
