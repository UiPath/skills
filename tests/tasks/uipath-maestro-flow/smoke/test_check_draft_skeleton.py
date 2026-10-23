"""Shape checks of check_draft_skeleton.py, with product validate stubbed out."""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_draft_skeleton as cds  # noqa: E402


def _flow(nodes, layout=True):
    doc = {"nodes": nodes, "edges": []}
    if layout:
        doc["layout"] = {"nodes": {n["id"]: {} for n in nodes}}
    return doc


def _box(i, label):
    return {"id": i, "type": "core.logic.mock", "display": {"label": label}}


GOOD = [
    {"id": "start", "type": "core.trigger.manual"},
    _box("record", "Record invoice [Data Fabric] → invoiceId"),
    {"id": "large", "type": "core.logic.decision",
     "inputs": {"trueLabel": "review", "falseLabel": "auto-approve"}},
    _box("review", "Manager review [Human task]"),
    _box("approve", "Approve invoice [Script]"),
    {"id": "end", "type": "core.control.end"},
]


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cds.validate_flow, "main", lambda paths: 0)
    proj = tmp_path / "Sol" / "Sketch"
    proj.mkdir(parents=True)
    (proj / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow", "Name": "Sketch"}))

    def write(doc):
        (proj / "Sketch.flow").write_text(json.dumps(doc))
    return write


def test_good_skeleton_passes(sandbox):
    sandbox(_flow(GOOD))
    assert cds.main(["Sketch"]) == 0


@pytest.mark.parametrize("mutate, needle", [
    (lambda n: n + [{"id": "x", "type": "uipath.agent.autonomous"}], "real activity"),
    (lambda n: [x for x in n if x["id"] != "approve"], ">= 3"),
    (lambda n: [_box("record", "Record invoice") if x["id"] == "record" else x for x in n], "label"),
    (lambda n: [dict(x, inputs={"trueLabel": "True", "falseLabel": "False"})
                if x["id"] == "large" else x for x in n], "outcome-labelled"),
])
def test_bad_skeletons_fail(sandbox, capsys, mutate, needle):
    sandbox(_flow(mutate(GOOD)))
    assert cds.main(["Sketch"]) == 1
    assert needle in capsys.readouterr().err


def test_event_start_box_and_terminate_pass(sandbox):
    nodes = [GOOD[0], _box("evt", "New ticket created [Trigger]")] + GOOD[1:] + [
        {"id": "stop", "type": "core.logic.terminate"}]
    sandbox(_flow(nodes))
    assert cds.main(["Sketch"]) == 0


def test_unformatted_fails(sandbox, capsys):
    sandbox(_flow(GOOD, layout=False))
    assert cds.main(["Sketch"]) == 1
    assert "format" in capsys.readouterr().err


def test_trigger_flag(sandbox, capsys):
    sandbox(_flow(GOOD))
    assert cds.main(["Sketch", "--trigger", "scheduled"]) == 1
    assert "core.trigger.scheduled" in capsys.readouterr().err
