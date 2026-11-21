"""The task's own setup and inline graders, run on a copy of the fixture.

Studio Web's harness opens the workspace's .uipx as the session's solution and
exports the agent's edits back to the workspace. A pre_run that moves the
fixture out of the workspace leaves Studio Web on an empty solution, so the
graders must read the workspace copy.
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


def _criterion_json(prefix: str) -> dict:
    return next(c for c in TASK["success_criteria"] if c["description"].startswith(prefix))


def _json_check(prefix: str, cwd: Path) -> bool:
    """A `json_check` criterion as the harness grades it: every `equals` assertion holds."""
    jmespath = pytest.importorskip("jmespath")
    criterion = _criterion_json(prefix)
    data = json.loads((cwd / criterion["path"]).read_text())
    return all(jmespath.search(a["expression"], data) == a["expected"] for a in criterion["assertions"])


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    shutil.copytree(HERE / "fixtures" / "ExpenseDesignerSaved", tmp_path / "ExpenseDesignerSaved")
    return tmp_path


def _add_cool_off(
    workspace: Path, duration: str = "PT10M", entry: str | None = "current-stage-entered"
) -> None:
    path = workspace / PLAN
    plan = json.loads(path.read_text())
    stage = next(n for n in plan["nodes"] if n["data"].get("label") == "Stage 7 - user select")
    stage["data"]["tasks"].append([{
        "id": "tCoolOff1", "displayName": "Final cool-off", "type": "wait-for-timer",
        "isRequired": False, "data": {"timeDuration": duration},
        **({"entryConditions": [{"rules": [[{"rule": entry}]]}]} if entry else {}),
    }])
    path.write_text(json.dumps(plan))


def test_pre_run_keeps_the_solution_in_the_workspace():
    for step in TASK["pre_run"]:
        assert "ExpenseDesignerSaved" not in step["command"], step["command"]


def test_edit_check_fails_on_the_untouched_fixture(workspace: Path):
    assert not _json_check("The edit landed", workspace)


def test_edit_check_passes_once_the_optional_timer_is_added(workspace: Path):
    _add_cool_off(workspace)
    assert _json_check("The edit landed", workspace)


@pytest.mark.parametrize("kwargs", [{"duration": "PT5M"}, {"duration": "PT10S"}, {"entry": "adhoc"}, {"entry": "runs-sequentially"}, {"entry": None}])
def test_edit_check_fails_on_the_wrong_wait_or_entry_rule(workspace: Path, kwargs: dict):
    _add_cool_off(workspace, **kwargs)
    assert not _json_check("The edit landed", workspace)


def test_designer_fields_check_passes_on_the_fixture_and_fails_on_a_lowered_version(workspace: Path):
    assert _json_check("What the Designer wrote survives", workspace)
    path = workspace / PLAN
    plan = json.loads(path.read_text())
    plan["version"] = "32.0.3"
    path.write_text(json.dumps(plan))
    assert not _json_check("What the Designer wrote survives", workspace)


def test_second_plan_file_check(workspace: Path):
    command = _criterion("No second plan file")
    assert _run(command, workspace).returncode == 0
    (workspace / PLAN).with_name("caseplan.json").write_text("{}")
    assert _run(command, workspace).returncode != 0
