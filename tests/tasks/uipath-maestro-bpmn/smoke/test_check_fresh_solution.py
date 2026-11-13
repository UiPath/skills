#!/usr/bin/env python3
"""Unit tests for check_fresh_solution.py. Stdlib and pytest only."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("check_fresh_solution", HERE / "check_fresh_solution.py")
assert SPEC and SPEC.loader
fresh = importlib.util.module_from_spec(SPEC)
sys.modules["check_fresh_solution"] = fresh
SPEC.loader.exec_module(fresh)

TAKEN = "ReturnsIntakeSolution"


def _solution(root: Path, name: str, projects: list[str]) -> None:
    folder = root / name
    folder.mkdir(parents=True, exist_ok=True)
    entries = [
        {"Type": "processOrchestration", "ProjectRelativePath": f"{p}/project.uiproj", "Id": p}
        for p in projects
    ]
    (folder / f"{name}.uipx").write_text(json.dumps({"SolutionId": name, "Projects": entries}))
    for project in projects:
        (folder / project).mkdir(exist_ok=True)
        (folder / project / f"{project}.bpmn").write_text("<bpmn:definitions/>")


def _grade(root: Path) -> str:
    return fresh.check(root, "ReturnsIntake", TAKEN)


def test_passes_for_a_project_in_a_fresh_solution(tmp_path: Path) -> None:
    _solution(tmp_path, TAKEN, ["ReturnsLabels"])
    _solution(tmp_path, "ReturnsIntakeSolution2", ["ReturnsIntake"])
    assert "ReturnsIntakeSolution2" in _grade(tmp_path)


def test_fails_when_the_project_joins_the_taken_solution(tmp_path: Path, capsys) -> None:
    _solution(tmp_path, TAKEN, ["ReturnsLabels", "ReturnsIntake"])
    with pytest.raises(SystemExit):
        _grade(tmp_path)
    assert "existing ReturnsIntakeSolution" in capsys.readouterr().out


def test_fails_when_no_process_was_built(tmp_path: Path, capsys) -> None:
    _solution(tmp_path, TAKEN, ["ReturnsLabels"])
    with pytest.raises(SystemExit):
        _grade(tmp_path)
    assert "no ReturnsIntake.bpmn" in capsys.readouterr().out


def test_fails_when_no_solution_registers_the_project(tmp_path: Path, capsys) -> None:
    _solution(tmp_path, TAKEN, ["ReturnsLabels"])
    _solution(tmp_path, "Other", [])
    (tmp_path / "Other" / "ReturnsIntake").mkdir()
    (tmp_path / "Other" / "ReturnsIntake" / "ReturnsIntake.bpmn").write_text("<x/>")
    with pytest.raises(SystemExit):
        _grade(tmp_path)
    assert "no solution other than" in capsys.readouterr().out


def test_ignores_registrations_of_another_type(tmp_path: Path) -> None:
    _solution(tmp_path, TAKEN, ["ReturnsLabels"])
    _solution(tmp_path, "Fresh", ["ReturnsIntake"])
    uipx = tmp_path / "Fresh" / "Fresh.uipx"
    data = json.loads(uipx.read_text())
    data["Projects"][0]["Type"] = "Flow"
    uipx.write_text(json.dumps(data))
    with pytest.raises(SystemExit):
        _grade(tmp_path)


def test_fixture_starts_with_the_taken_solution_only(tmp_path: Path) -> None:
    fixture = HERE / "fixtures" / "new_solution_name_taken"
    uipx = json.loads((fixture / TAKEN / f"{TAKEN}.uipx").read_text())
    assert [p["ProjectRelativePath"] for p in uipx["Projects"]] == ["ReturnsLabels/project.uiproj"]
    with pytest.raises(SystemExit):
        fresh.check(fixture, "ReturnsIntake", TAKEN)
