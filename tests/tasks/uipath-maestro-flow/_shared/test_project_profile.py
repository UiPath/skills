"""Unit tests for ``project_profile.py`` across the terminal ``<Name>.flow``
layout and Studio Web's ``<Name>/new.flow`` layout."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project_profile import SENTINEL, main  # noqa: E402

import pytest  # noqa: E402


def _project(tmp_path, project="Demo", flow_file="Demo.flow", profile=None, sentinel=False):
    proj = tmp_path / "Sol" / project
    proj.mkdir(parents=True)
    (proj / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    (proj / flow_file).write_text(json.dumps({"nodes": [{"id": "n1"}]}))
    if profile:
        (proj / "operate.json").write_text(
            json.dumps({"runtimeOptions": {"profile": profile}})
        )
    if sentinel:
        (proj / SENTINEL).write_text("")
    return proj


def _run(monkeypatch, tmp_path, *argv):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["project_profile.py", *argv])
    return main()


@pytest.mark.parametrize("flow_file", ["Demo.flow", "new.flow"])
def test_finds_flow_in_either_layout(tmp_path, monkeypatch, flow_file):
    _project(tmp_path, flow_file=flow_file)

    assert _run(monkeypatch, tmp_path, "--flow-name", "Demo", "--expect-no-sentinel") == 0


def test_sentinel_is_read_from_the_new_flow_project(tmp_path, monkeypatch):
    _project(tmp_path, flow_file="new.flow", sentinel=True)

    assert _run(monkeypatch, tmp_path, "--flow-name", "Demo", "--expect-sentinel") == 0
    assert _run(monkeypatch, tmp_path, "--flow-name", "Demo", "--expect-no-sentinel") == 1


def test_profile_is_read_from_the_new_flow_project(tmp_path, monkeypatch):
    _project(tmp_path, flow_file="new.flow", profile="Lite")

    assert _run(monkeypatch, tmp_path, "--flow-name", "Demo", "--expect-profile", "Lite") == 0
    assert _run(monkeypatch, tmp_path, "--flow-name", "Demo", "--expect-profile", "Standard") == 1


def test_missing_operate_json_still_fails_the_profile_check(tmp_path, monkeypatch, capsys):
    _project(tmp_path, flow_file="new.flow")

    assert _run(monkeypatch, tmp_path, "--flow-name", "Demo", "--expect-profile", "Standard") == 1
    assert "no operate.json" in capsys.readouterr().err


def test_new_flow_in_another_project_is_not_a_match(tmp_path, monkeypatch, capsys):
    _project(tmp_path, project="Other", flow_file="new.flow")

    assert _run(monkeypatch, tmp_path, "--flow-name", "Demo", "--expect-no-sentinel") == 1
    assert "no Demo.flow" in capsys.readouterr().err


def _substantive(proj, flow_file):
    nodes = [{"id": f"n{i}"} for i in range(6)]
    (proj / flow_file).write_text(json.dumps({"nodes": nodes}))


@pytest.mark.parametrize("other_file", ["Other.flow", "new.flow"])
def test_flow_name_selects_one_of_several_projects(tmp_path, monkeypatch, other_file):
    demo = _project(tmp_path, flow_file="new.flow", sentinel=True)
    other = _project(tmp_path, project="Other", flow_file=other_file)
    _substantive(demo, "new.flow")
    _substantive(other, other_file)

    assert _run(monkeypatch, tmp_path, "--flow-name", "Demo", "--expect-sentinel") == 0
    assert _run(monkeypatch, tmp_path, "--flow-name", "Other", "--expect-no-sentinel") == 0
