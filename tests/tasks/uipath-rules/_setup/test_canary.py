"""Unit tests for canary.py, with `uip` stubbed. Run with ``pytest`` from any directory."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import canary  # noqa: E402


def debug_response(band):
    return json.dumps({"Data": {"result": {"decisions": [{"decisionName": "Decision", "outputs": {"riskBand": band}}]}}})


@pytest.fixture
def uip(monkeypatch, tmp_path):
    """Stubs `uip`. `rules debug` writes a solution manifest the way the CLI does; the test sets its answer."""
    monkeypatch.chdir(tmp_path)
    state = {"band": "High", "returncode": 0, "calls": []}

    def run(command, **_):
        state["calls"].append(command)
        if command[:3] == ["uip", "rules", "debug"]:
            project = Path(command[3])
            state["project"] = project
            state["cwd"] = Path.cwd()
            (project.parent / "CanaryRulesSolution.uipx").write_text(json.dumps({"SolutionId": "new-solution"}))
            return subprocess.CompletedProcess(command, state["returncode"], stdout=debug_response(state["band"]), stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")

    monkeypatch.setattr(canary.subprocess, "run", run)
    monkeypatch.setattr(canary.solution_cleanup.subprocess, "run", run)
    return state


def deletes(state):
    return [c for c in state["calls"] if c[:3] == ["uip", "solution", "delete"]]


def test_passes_when_the_engine_answers_the_expected_band(uip, tmp_path):
    assert canary.main() == 0
    # Built outside the sandbox, with a real manifest, and the sandbox is left as it was.
    assert tmp_path not in uip["project"].parents
    assert (uip["project"] / "project.uiproj").is_file() is False  # removed with the scratch folder
    assert Path.cwd() == tmp_path and list(tmp_path.iterdir()) == []


def test_fails_on_a_wrong_band(uip):
    uip["band"] = "Low"
    assert canary.main() == 1


def test_fails_when_debug_fails(uip):
    uip["returncode"] = 1
    assert canary.main() == 1


def test_deletes_the_solution_its_run_uploaded(uip):
    canary.main()
    assert [c[3] for c in deletes(uip)] == ["new-solution"]


def test_deletes_the_solution_on_failure_too(uip):
    uip["band"] = "Low"
    canary.main()
    assert [c[3] for c in deletes(uip)] == ["new-solution"]


def test_the_committed_project_is_not_a_live_project():
    # The sandbox mounts `_setup/`, and graders find every `project.uiproj`.
    assert not list(canary.SOURCE.rglob("project.uiproj"))
    assert json.loads((canary.SOURCE / "project.uiproj.canary").read_text())["ProjectType"] == "BusinessRules"
