"""Unit tests for the draft-mode skeleton and build graders (no CLI, no tenant)."""

import copy
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "..", "_shared"))

import check_draft_skeleton  # noqa: E402
import check_draft_word_build  # noqa: E402
import check_no_blank_boxes  # noqa: E402
import draft_case  # noqa: E402
from draft_fixtures import SKELETON, TIMER_SKELETON, built, write_project  # noqa: E402


def test_skeleton_passes():
    assert check_draft_skeleton.problems(SKELETON, trigger="manual", routed=True) == []


def test_timer_skeleton_passes_and_names_its_trigger():
    assert check_draft_skeleton.problems(TIMER_SKELETON, trigger="timer", routed=True) == []
    assert any("trigger" in p for p in check_draft_skeleton.problems(TIMER_SKELETON, trigger="manual"))


def test_built_task_fails_the_skeleton():
    doc = copy.deepcopy(SKELETON)
    doc["nodes"][1]["data"]["tasks"][0][0]["data"] = {"name": "x", "folderPath": "Shared"}
    assert any("built tasks" in p for p in check_draft_skeleton.problems(doc))


def test_box_without_kind_suffix_fails():
    doc = copy.deepcopy(SKELETON)
    doc["nodes"][1]["data"]["tasks"][0][0]["displayName"] = "Extract claim data"
    assert any("[<Kind>]" in p for p in check_draft_skeleton.problems(doc))


def test_producer_hint_is_part_of_the_label():
    assert draft_case.BOX_LABEL.fullmatch("Adjuster review [Human task] → decision")
    assert draft_case.BOX_LABEL.fullmatch("Adjuster review [Human task] -> decision")
    assert not draft_case.BOX_LABEL.fullmatch("[Agent]")


def test_routed_needs_an_expression_and_an_outcome_name():
    doc = copy.deepcopy(SKELETON)
    for node in doc["nodes"][1:]:
        for cond in node["data"]["entryConditions"]:
            for group in cond["rules"]:
                for rule in group:
                    rule.pop("conditionExpression", None)
    assert any("routes on an expression" in p for p in check_draft_skeleton.problems(doc, routed=True))
    doc = copy.deepcopy(SKELETON)
    doc["nodes"][3]["data"]["entryConditions"][0]["displayName"] = ""
    assert any("outcome name" in p for p in check_draft_skeleton.problems(doc, routed=True))


def test_stage_without_entry_condition_fails():
    doc = copy.deepcopy(SKELETON)
    doc["nodes"][2]["data"]["entryConditions"] = []
    assert any("entry condition" in p for p in check_draft_skeleton.problems(doc))


def test_too_few_boxes_or_stages_fail():
    assert any("blank boxes" in p for p in check_draft_skeleton.problems(SKELETON, min_boxes=9))
    assert any("stages" in p for p in check_draft_skeleton.problems(SKELETON, min_stages=9))


def test_tasks_reads_lanes_in_plan_order_with_stage_labels():
    rows = draft_case.tasks(SKELETON)
    assert [stage for stage, _ in rows][:3] == ["Intake", "Intake", "Review"]
    assert draft_case.label_of(rows[0][1]) == "Extract claim data [Agent]"


def test_word_build_wants_a_built_task_and_no_outline_name():
    assert check_draft_word_build.problems(built(SKELETON)) == []
    assert any("no built task" in p for p in check_draft_word_build.problems(SKELETON))
    doc = built(SKELETON)
    doc["nodes"][1]["data"]["tasks"][0][0]["displayName"] = "Extract claim data [Agent]"
    assert any("outline boxes" in p for p in check_draft_word_build.problems(doc))


def test_no_blank_boxes_after_build_it(tmp_path, monkeypatch):
    write_project(tmp_path, built(SKELETON))
    monkeypatch.chdir(tmp_path)
    assert check_no_blank_boxes.main() == 0


def test_no_blank_boxes_fails_on_a_skeleton(tmp_path, monkeypatch):
    write_project(tmp_path, SKELETON)
    monkeypatch.chdir(tmp_path)
    assert check_no_blank_boxes.main() == 1


def test_no_blank_boxes_fails_on_a_kept_suffix(tmp_path, monkeypatch):
    doc = built(SKELETON)
    doc["nodes"][2]["data"]["tasks"][0][0]["displayName"] = "Adjuster review [Human task]"
    write_project(tmp_path, doc)
    monkeypatch.chdir(tmp_path)
    assert check_no_blank_boxes.main() == 1
