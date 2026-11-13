"""Unit tests for ``check_single_flow.py``: one built ``.flow`` per Flow project."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_single_flow import main, single_flow_problem  # noqa: E402


def _flow(path, nodes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"nodes": [{"id": f"n{i}"} for i in range(nodes)]}), encoding="utf-8")


def _project(tmp_path, **flows):
    """A Flow project holding ``<file name>: <node count>`` for each of ``flows``."""
    project = tmp_path / "Sol" / "Proj"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}), encoding="utf-8")
    for name, nodes in flows.items():
        _flow(project / name, nodes)
    return project


def test_one_built_flow_passes_under_either_file_name(tmp_path):
    assert single_flow_problem(str(_project(tmp_path / "cli", **{"Proj.flow": 3}))) is None
    assert single_flow_problem(str(_project(tmp_path / "web", **{"new.flow": 3}))) is None


def test_built_flow_beside_the_studio_web_seed_fails(tmp_path):
    project = _project(tmp_path, **{"new.flow": 1, "Proj.flow": 3})

    problem = single_flow_problem(str(project))

    assert "holds 2 .flow files" in problem
    assert "new.flow (1 node(s))" in problem and "Proj.flow (3 node(s))" in problem


def test_two_built_flows_fail(tmp_path):
    assert "holds 2 .flow files" in single_flow_problem(str(_project(tmp_path, **{"new.flow": 3, "Proj.flow": 3})))


def test_lone_trigger_only_flow_fails(tmp_path):
    assert "unbuilt" in single_flow_problem(str(_project(tmp_path, **{"new.flow": 1})))


def test_unreadable_flow_fails(tmp_path):
    project = _project(tmp_path)
    (project / "new.flow").write_text("", encoding="utf-8")

    assert "unreadable" in single_flow_problem(str(project))


def test_sdk_working_copies_are_not_counted(tmp_path):
    project = _project(tmp_path, **{"new.flow": 3})
    _flow(project / ".flow-sdk" / "original" / "new.flow", 1)

    assert single_flow_problem(str(project)) is None


def test_main_finds_the_project_from_the_sandbox_root(tmp_path, monkeypatch, capsys):
    _project(tmp_path, **{"new.flow": 1, "Proj.flow": 3})
    monkeypatch.chdir(tmp_path)

    assert main() == 1
    assert "FAIL: Sol/Proj holds 2 .flow files" in capsys.readouterr().err
