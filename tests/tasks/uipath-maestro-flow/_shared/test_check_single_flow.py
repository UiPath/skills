"""Unit tests for ``check_single_flow.py``: one built ``.flow`` per Flow project."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_single_flow import main, single_flow_problem  # noqa: E402


# The one node `uip maestro flow init` seeds, as written by a 2026-11-24 nightly run.
SCAFFOLD_TRIGGER = {
    "id": "start",
    "type": "core.trigger.manual",
    "typeVersion": "1.0",
    "ui": {"position": {"x": 256, "y": 144}, "size": {"width": 96, "height": 96}, "collapsed": False, "placeholder": False},
    "display": {"label": "Manual trigger", "icon": "play"},
    "model": {"type": "bpmn:StartEvent", "entryPointId": True},
    "outputs": {
        "output": {
            "type": "object",
            "description": "Data passed when manually triggering the process.",
            "source": "null",
            "var": "output",
        }
    },
    "inputs": {},
}


def _flow(path, nodes):
    """Write a ``.flow`` holding ``nodes``: a list of node dicts, or a count of untyped nodes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(nodes, int):
        nodes = [{"id": f"n{i}"} for i in range(nodes)]
    path.write_text(json.dumps({"nodes": nodes}), encoding="utf-8")


def _project(tmp_path, **flows):
    """A Flow project holding ``<file name>: <nodes>`` for each of ``flows`` (see ``_flow``)."""
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


def test_allow_unbuilt_accepts_the_init_scaffold_but_not_two_files(tmp_path):
    one = _project(tmp_path / "one", **{"Proj.flow": [SCAFFOLD_TRIGGER]})
    assert single_flow_problem(str(one), allow_unbuilt=True) is None
    two = _project(tmp_path / "two", **{"new.flow": [SCAFFOLD_TRIGGER], "Proj.flow": [SCAFFOLD_TRIGGER]})
    assert "holds 2 .flow files" in single_flow_problem(str(two), allow_unbuilt=True)


def test_allow_unbuilt_still_rejects_a_flow_with_no_nodes(tmp_path):
    assert "unbuilt" in single_flow_problem(str(_project(tmp_path, **{"new.flow": 0})), allow_unbuilt=True)


@pytest.mark.parametrize(
    "node",
    [
        {"id": "n0"},  # no type
        {"id": "start", "type": None},
        {"id": "greet", "type": "core.action.script"},  # a lone action
        {"id": "end", "type": "core.control.end"},
        {"id": "start", "type": "core.trigger.scheduled"},  # not what the scaffold seeds
        {"id": "start", "type": " core.trigger.manual"},
        "core.trigger.manual",  # not a node object
    ],
)
def test_allow_unbuilt_rejects_a_lone_node_that_is_not_the_scaffold_trigger(tmp_path, node):
    problem = single_flow_problem(str(_project(tmp_path, **{"Proj.flow": [node]})), allow_unbuilt=True)
    assert "not a core.trigger.manual scaffold" in problem


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

    assert main([]) == 1
    assert "FAIL: Sol/Proj holds 2 .flow files" in capsys.readouterr().err


def test_main_allow_unbuilt_passes_the_init_scaffold(tmp_path, monkeypatch, capsys):
    _project(tmp_path, **{"Proj.flow": [SCAFFOLD_TRIGGER]})
    monkeypatch.chdir(tmp_path)

    assert main(["--allow-unbuilt"]) == 0
    assert "OK: Sol/Proj holds one .flow" in capsys.readouterr().out
