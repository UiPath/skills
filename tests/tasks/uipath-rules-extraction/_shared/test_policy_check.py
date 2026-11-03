"""Unit tests for policy_check.py. Run with ``pytest`` from any directory.

The grader is the answer key for the uipath-rules-extraction tasks, so what
these pin is that a correct reading of the policy passes every scenario, that
each plausible misreading fails at least one, and that the box check accepts
real word-run boxes and rejects invented ones.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import policy_check as pc  # noqa: E402
import test_rules_support as support  # noqa: E402

GOLD = [  # serviceDays, requestAmount, hasDirectorPreApproval, hasMedicalAccommodation -> outcome
    (("null", "-", "-", "-"), "Refer"),
    (("-", "null", "-", "-"), "Refer"),
    (("-", "> 2000", "-", "-"), "Deny"),
    (("< 90", "-", "-", "false"), "Deny"),
    (("-", "<= 500", "-", "-"), "Approve"),
    (("-", "(500..2000]", "true", "-"), "Approve"),
    (("-", "-", "-", "-"), "Deny"),
]


def evaluate_all(rows):
    table = support.table("FIRST", rows)
    return [(label, pc.evaluate(table, dict(zip(pc.INPUTS, values))), expected)
            for label, values, expected in pc.SCENARIOS]


def test_gold_table_matches_every_scenario():
    assert [(label, got) for label, got, want in evaluate_all(GOLD) if got != want] == []


@pytest.mark.parametrize("name, rows", [
    ("no refer row: null falls through to Deny", GOLD[2:]),
    ("accommodation waives the cap", [GOLD[0], GOLD[1], (("-", "-", "-", "true"), "Approve")] + GOLD[2:]),
    ("approves by default", GOLD[:-1] + [(("-", "-", "-", "-"), "Approve")]),
    ("pre-approval ignored", [r for r in GOLD if r[0][2] != "true"] + []),
])
def test_misreadings_fail(name, rows):
    assert any(got != want for _, got, want in evaluate_all(rows)), name


def test_null_matches_only_wildcard_or_null():
    assert pc.cell_matches("-", None)
    assert pc.cell_matches("null", None)
    assert not pc.cell_matches("<= 500", None)
    assert not pc.cell_matches("not(null)", None)


def test_word_runs_accept_real_boxes_and_reject_invented_ones():
    dom = json.loads(pc.DOM.read_text(encoding="utf-8"))
    runs = pc.word_runs(dom)
    assert "1536,380,576,44" in runs[1]          # "at least 90 days of service" (page 1)
    assert "1536,380,577,44" not in runs[1]      # one pixel off is an invented box
    assert "1536,380,576,44" not in runs[2]      # right box, wrong page


def test_vendored_rules_check_matches_the_uipath_rules_original():
    original = Path(__file__).resolve().parent.parent.parent / "uipath-rules" / "_shared" / "rules_check.py"
    if original.exists():  # the grader sandbox stages only this skill's folder
        assert original.read_bytes() == (Path(__file__).resolve().parent / "rules_check.py").read_bytes()


def test_quoted_string_lists_and_commas_inside_quotes():
    assert pc.cell_matches('"Hotel","Meal"', "Meal")
    assert not pc.cell_matches('"Hotel","Meal"', "Airfare")
    assert pc.cell_matches('"a, b"', "a, b")
