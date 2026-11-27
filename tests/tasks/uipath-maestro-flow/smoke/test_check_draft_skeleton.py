"""Shape checks of check_draft_skeleton.py, with `flow validate` stubbed out."""

from __future__ import annotations

import copy
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import check_draft_skeleton as cds  # noqa: E402
from _shared import draft_fixtures as fx  # noqa: E402


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cds, "validate", lambda path: 0)
    return lambda doc, name="Sketch.flow": fx.write_project(tmp_path, doc, name)


def node(doc, node_id):
    return next(n for n in doc["nodes"] if n["id"] == node_id)


def test_valid_skeleton_passes(sandbox):
    sandbox(fx.SKELETON)
    assert cds.main(["--loop"]) == 0


def test_studio_web_file_name_passes(sandbox):
    sandbox(fx.SKELETON, "new.flow")
    assert cds.main([]) == 0


def test_scheduled_switch_skeleton_passes(sandbox):
    sandbox(fx.SCHEDULED_SWITCH)
    assert cds.main(["--trigger", "scheduled", "--switch-arms", "3"]) == 0


def test_validate_failure_propagates(sandbox, monkeypatch):
    sandbox(fx.SKELETON)
    monkeypatch.setattr(cds, "validate", lambda path: 1)
    assert cds.main([]) == 1


def test_unlabelled_decision_arm_fails(sandbox, capsys):
    doc = copy.deepcopy(fx.SKELETON)
    node(doc, "large")["inputs"]["falseLabel"] = "False"
    sandbox(doc)
    assert cds.main([]) == 1
    assert "'false' has no outcome label" in capsys.readouterr().err


def test_default_switch_case_label_fails(sandbox, capsys):
    doc = copy.deepcopy(fx.SCHEDULED_SWITCH)
    node(doc, "route")["inputs"]["cases"][1]["label"] = 'Case "b"'
    sandbox(doc)
    assert cds.main([]) == 1
    assert "case_2" in capsys.readouterr().err


def test_too_few_switch_arms_fail(sandbox, capsys):
    sandbox(fx.SCHEDULED_SWITCH)
    assert cds.main(["--switch-arms", "4"]) == 1
    assert "labelled cases" in capsys.readouterr().err


def test_routing_on_mock_output_fails(sandbox, capsys):
    doc = copy.deepcopy(fx.SKELETON)
    node(doc, "large")["inputs"]["expression"] = "$vars.record.output.total >= 1000"
    sandbox(doc)
    assert cds.main([]) == 1
    assert "large reads record" in capsys.readouterr().err


def test_real_action_node_fails(sandbox, capsys):
    doc = copy.deepcopy(fx.SKELETON)
    node(doc, "notify")["type"] = "core.action.script"
    sandbox(doc)
    assert cds.main([]) == 1
    assert "real action nodes" in capsys.readouterr().err


def test_box_without_kind_fails(sandbox, capsys):
    doc = copy.deepcopy(fx.SKELETON)
    node(doc, "record")["display"]["label"] = "Record invoice"
    sandbox(doc)
    assert cds.main([]) == 1
    assert "'<Action> [<Kind>]'" in capsys.readouterr().err


def test_missing_loop_fails_only_when_required(sandbox, capsys):
    sandbox(fx.SCHEDULED_SWITCH)
    assert cds.main([]) == 0
    assert cds.main(["--loop"]) == 1
    assert "loop" in capsys.readouterr().err


def test_no_branching_fails(sandbox, capsys):
    doc = copy.deepcopy(fx.SKELETON)
    doc["nodes"] = [n for n in doc["nodes"] if n["id"] != "large"]
    sandbox(doc)
    assert cds.main([]) == 1
    assert "no decision or switch" in capsys.readouterr().err


def test_wrong_trigger_fails(sandbox, capsys):
    sandbox(fx.SKELETON)
    assert cds.main(["--trigger", "scheduled"]) == 1
    assert "core.trigger.scheduled" in capsys.readouterr().err


def test_unplaced_node_fails(sandbox, capsys):
    doc = copy.deepcopy(fx.SKELETON)
    del node(doc, "record")["ui"]["position"]
    sandbox(doc)
    assert cds.main([]) == 1
    err = capsys.readouterr().err
    assert "layout" in err and "record" in err


def test_variable_suffix_after_kind_passes(sandbox):
    doc = copy.deepcopy(fx.SKELETON)
    node(doc, "record")["display"]["label"] = "Record invoice [Data Fabric] \u2192 invoiceId"
    sandbox(doc)
    assert cds.main([]) == 0


def test_real_label_starting_with_case_passes(sandbox):
    doc = copy.deepcopy(fx.SCHEDULED_SWITCH)
    node(doc, "route")["inputs"]["cases"][0]["label"] = "Case closed"
    sandbox(doc)
    assert cds.main(["--switch-arms", "3"]) == 0


def test_lowercase_kind_fails(sandbox, capsys):
    doc = copy.deepcopy(fx.SKELETON)
    node(doc, "record")["display"]["label"] = "Record invoice [foo]"
    sandbox(doc)
    assert cds.main([]) == 1
    assert "'<Action> [<Kind>]'" in capsys.readouterr().err
