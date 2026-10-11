"""The round-trip harness refuses to call a planted break 'no change'.

A small project stands in for the golden. Each case plants one change in the 'after'
copy and asserts where the scorer files it. Run: python3 -m pytest tests/probes/case-roundtrip -q
"""

from __future__ import annotations

import copy
import json
import os
import shutil

import pytest

import consistency
import roundtrip_diff as rd

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = {"id": "case-x", "version": "32.0.3", "bindings": [{"id": "b1", "name": "name"}],
        "nodes": [{"id": "trigger_1", "type": "uipath.case.trigger", "data": {"label": "Trigger 1"}},
                  {"id": "Stage_a", "type": "case-management:Stage", "data": {"tasks": [[
                      {"id": "t1", "type": "execute-connector-activity", "displayName": "List Emails",
                       "data": {"context": [{"name": "connectionId", "value": "c1"}],
                                "outputs": [{"id": "o1", "var": "o1", "elementId": "Stage_a-t1"}]}}]]}}],
        "edges": []}
EP = {"entryPoints": [{"filePath": "/content/caseplan.json.bpmn#trigger_1", "uniqueId": "u-1",
                       "displayName": "Trigger 1"}]}


def project(root, plan=PLAN, ep=EP):
    os.makedirs(root, exist_ok=True)
    json.dump(plan, open(os.path.join(root, "caseplan.json"), "w"))
    json.dump(ep, open(os.path.join(root, "entry-points.json"), "w"))
    return root


def rules():
    return json.load(open(os.path.join(HERE, "PREDICTION.json")))["rules"]


def run(tmp_path, plan=PLAN, ep=EP):
    before, after = project(str(tmp_path / "a")), project(str(tmp_path / "b"), plan, ep)
    return rd.score(rd.diff(before, after), rules()), before, after


def test_identical_copies_have_no_divergence(tmp_path):
    (hits, misses, violated, surprises), before, after = run(tmp_path)
    assert not violated and not surprises
    assert {r["id"] for r in misses} >= {"C1-layout"}, "an unedited save with no layout is a MISS"
    assert not consistency.entry_points(before, after)


def test_a_rewritten_unique_id_violates_entry_points(tmp_path):
    ep = copy.deepcopy(EP)
    ep["entryPoints"][0]["uniqueId"] = "u-2"
    (_, _, violated, _), before, after = run(tmp_path, ep=ep)
    assert "S3-entry-points" in {r["id"] for r, _ in violated}
    assert any("uniqueIds changed" in p for p in consistency.entry_points(before, after))


def test_a_dropped_connector_field_violates_connector_config(tmp_path):
    plan = copy.deepcopy(PLAN)
    plan["nodes"][1]["data"]["tasks"][0][0]["data"]["context"] = []
    (_, _, violated, _), _, _ = run(tmp_path, plan=plan)
    assert "S6-connector-config" in {r["id"] for r, _ in violated}


def test_added_layout_is_predicted_not_a_surprise(tmp_path):
    plan = copy.deepcopy(PLAN)
    plan["layout"] = {"Stage_a": {"x": 1, "y": 2}}
    (hits, misses, violated, surprises), _, _ = run(tmp_path, plan=plan)
    assert not surprises and not violated and "C1-layout" not in {r["id"] for r in misses}


def test_an_unnamed_new_field_is_caught_by_the_catch_all(tmp_path):
    plan = copy.deepcopy(PLAN)
    plan["designerVersion"] = "9.9"
    (_, _, violated, _), _, _ = run(tmp_path, plan=plan)
    assert "S9-rest-of-plan" in {r["id"] for r, _ in violated}


def test_a_dropped_plan_file_is_not_absorbed_as_noise(tmp_path):
    (_, _, _, _), before, after = run(tmp_path)
    os.remove(os.path.join(after, "caseplan.json"))
    _, _, violated, surprises = rd.score(rd.diff(before, after), rules())
    flagged = surprises + [d for _, h in violated for d in h]
    assert any(s["change"] == "file-dropped" and s["file"] == "caseplan.json" for s in flagged)


def test_a_sidecar_missing_a_node_is_inconsistent(tmp_path):
    (_, _, _, _), before, after = run(tmp_path)
    json.dump({"trigger_1": {"x": 0}}, open(os.path.join(after, "caseplan.layout.json"), "w"))
    assert consistency.sidecar(before, after)


@pytest.mark.parametrize("path,pattern,ok", [
    ("nodes[Stage_a].data.tasks[0][t1].data.context", "nodes[*].data.tasks*.data.*", True),
    ("nodes[Stage_a].position.x", "nodes[*].position*", True),
    ("nodes[Stage_a].data.label", "nodes[*].position*", False),
    ("entryPoints[0].uniqueId", "*", True),
])
def test_path_patterns_treat_brackets_literally(path, pattern, ok):
    assert rd.path_matches(path, pattern) is ok
