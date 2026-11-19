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
TASK = yaml.safe_load((HERE / "designer_stale_bindings.yaml").read_text())
FIXTURE = HERE.parent / "designer_saved_plan" / "fixtures" / "ExpenseDesignerSaved"
PROJECT = Path("ExpenseDesignerSaved/CMGoldenExpense")


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
    """The fixture after this task's own pre_run (tenant-id localization skipped)."""
    shutil.copytree(FIXTURE, tmp_path / "ExpenseDesignerSaved")
    for step in TASK["pre_run"]:
        if "localize_tenant_ids" in step["command"]:
            continue
        result = _run(step["command"], tmp_path)
        assert result.returncode == 0, step["command"] + result.stderr
    return tmp_path


def test_pre_run_keeps_the_solution_in_the_workspace(workspace: Path):
    assert (workspace / PROJECT / "caseplan.case").is_file()


def test_edit_check_fails_until_the_timer_waits_15_minutes(workspace: Path):
    assert not _json_check("The edit landed", workspace)

    path = workspace / PROJECT / "caseplan.case"
    plan = json.loads(path.read_text())
    timer = next(
        t for n in plan["nodes"] for ts in n["data"].get("tasks", []) for t in ts
        if t["displayName"] == "Wait for timer - S5"
    )
    timer["data"]["timeDuration"] = "PT15M"
    path.write_text(json.dumps(plan))
    assert _json_check("The edit landed", workspace)


def test_sidecar_check_fails_on_the_stripped_sidecar_and_passes_once_regenerated(workspace: Path):
    assert not _json_check("bindings_v2.json carries the RPA Workflow resource", workspace)

    shutil.copy(FIXTURE / "CMGoldenExpense" / "bindings_v2.json", workspace / PROJECT / "bindings_v2.json")
    assert _json_check("bindings_v2.json carries the RPA Workflow resource", workspace)
