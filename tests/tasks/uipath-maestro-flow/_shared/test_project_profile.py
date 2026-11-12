"""Unit tests for ``project_profile.py``'s flow lookup and profile source."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project_profile import find_flow, main, read_profile  # noqa: E402


def _write(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")


def test_finds_the_cli_named_flow(tmp_path, monkeypatch):
    _write(tmp_path / "ShipmentTracker" / "ShipmentTracker" / "ShipmentTracker.flow")
    monkeypatch.chdir(tmp_path)

    assert [p.name for p in find_flow("ShipmentTracker")] == ["ShipmentTracker.flow"]


def test_finds_studio_web_new_flow_in_the_named_project(tmp_path, monkeypatch):
    _write(tmp_path / "ShipmentTracker" / "ShipmentTracker" / "new.flow")
    _write(tmp_path / "Other" / "Other" / "new.flow")
    monkeypatch.chdir(tmp_path)

    assert [str(p) for p in find_flow("ShipmentTracker")] == ["ShipmentTracker/ShipmentTracker/new.flow"]


def _project(tmp_path, flow_file, *, profile=None, marker=False):
    """A project folder holding ``flow_file`` and, optionally, operate.json and the marker."""
    project = tmp_path / "Sol" / "Proj"
    _write(project / "project.uiproj")
    _write(project / flow_file)
    if profile is not None:
        (project / "operate.json").write_text(json.dumps({"runtimeOptions": {"profile": profile}}), encoding="utf-8")
    if marker:
        (project / ".maestro_automate").write_text("", encoding="utf-8")
    return project


def test_profile_comes_from_operate_json_when_the_project_has_one(tmp_path):
    project = _project(tmp_path, "Proj.flow", profile="Lite")

    assert read_profile(project, project / "Proj.flow")[0] == "Lite"


def test_operate_json_wins_over_the_marker_in_a_studio_web_project(tmp_path):
    project = _project(tmp_path, "new.flow", profile="Standard", marker=True)

    assert read_profile(project, project / "new.flow")[0] == "Standard"


@pytest.mark.parametrize(("marker", "expected"), [(False, "Standard"), (True, "Lite")])
def test_studio_web_project_without_operate_json_takes_the_profile_from_the_marker(tmp_path, marker, expected):
    project = _project(tmp_path, "new.flow", marker=marker)

    assert read_profile(project, project / "new.flow")[0] == expected


def test_cli_project_without_operate_json_still_fails(tmp_path):
    project = _project(tmp_path, "Proj.flow", marker=True)

    with pytest.raises(ValueError, match="no operate.json"):
        read_profile(project, project / "Proj.flow")


def _run(monkeypatch, tmp_path, *argv):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["project_profile.py", "--flow-name", "Proj", *argv])
    return main()


def test_plain_studio_web_project_passes_as_standard_with_no_marker(tmp_path, monkeypatch):
    _project(tmp_path, "new.flow")

    assert _run(monkeypatch, tmp_path, "--expect-profile", "Standard", "--expect-no-sentinel") == 0


def test_cli_project_without_operate_json_fails_the_task_check(tmp_path, monkeypatch):
    _project(tmp_path, "Proj.flow")

    assert _run(monkeypatch, tmp_path, "--expect-profile", "Standard", "--expect-no-sentinel") == 1


def test_plain_studio_web_project_fails_a_maestro_automate_expectation(tmp_path, monkeypatch):
    _project(tmp_path, "new.flow")

    assert _run(monkeypatch, tmp_path, "--expect-profile", "Lite", "--expect-sentinel") == 1
