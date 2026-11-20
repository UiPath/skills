"""Unit tests for policy_check.py. Run with ``pytest`` from any directory.

The grader is the answer key for the uipath-rules extraction tasks, so what
these pin is that a correct reading of the policy passes every scenario, that
each plausible misreading fails at least one, and that the box check accepts
real word-run boxes and rejects invented ones.
"""

import json
import sys
import xml.etree.ElementTree as ET
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


def test_quoted_string_lists_and_commas_inside_quotes():
    assert pc.cell_matches('"Hotel","Meal"', "Meal")
    assert not pc.cell_matches('"Hotel","Meal"', "Airfare")
    assert pc.cell_matches('"a, b"', "a, b")


def test_refs_must_hold_a_cited_quote_not_just_any_word_run():
    dom = json.loads(pc.DOM.read_text(encoding="utf-8"))
    texts = pc.word_run_texts(dom)
    box = "1536,380,576,44"                      # the run "at least 90 days of service" on page 1
    quote = pc.squash(texts[1][box])
    pages = {1: quote, 2: ""}
    good = [{"id": "r1", "page": 1, "quote": "at least 90 days of service"}]
    assert pc.check_refs([(1, box)], good, pages, texts) == []
    # a real box that no cited quote matches
    other = next(b for b, t in texts[1].items() if t != quote)
    assert pc.check_refs([(1, other)], good, pages, texts)
    # a quote that is not on the page
    assert pc.check_refs([(1, box)], [{"id": "r2", "page": 1, "quote": "not in the policy"}], pages, texts)
    # an invented box
    assert pc.check_refs([(1, "1,2,3,4")], good, pages, texts)


def test_boxes_without_cites_must_still_be_word_run_boxes():
    texts = pc.word_run_texts(json.loads(pc.DOM.read_text(encoding="utf-8")))
    box = next(iter(texts[1]))
    assert pc.check_boxes([(1, box)], texts) == []
    assert pc.check_boxes([(1, "1,2,3,4")], texts)


def test_a_rule_with_fewer_entries_than_columns_is_rejected():
    table = support.table("FIRST", [(("-", "-"), "Deny")])   # 2 entries for 4 columns
    with pytest.raises(SystemExit):
        pc.evaluate(table, dict(zip(pc.INPUTS, (1, 1, False, False))))


def test_page_only_source_refs_are_allowed_without_digitizer_positions():
    page_only = ET.fromstring('<sourceRef page="3"/>')
    boxed = ET.fromstring('<sourceRef page="3" box="1,2,3,4"/>')
    block = ET.fromstring('<sourceRef page="3" blockId="7"/>')
    assert pc.positioned_refs([page_only]) == []
    assert pc.positioned_refs([page_only, boxed, block]) == [boxed, block]


RECORD_DMN = """<definitions xmlns="https://www.omg.org/spec/DMN/20230324/MODEL/"
  xmlns:uipdm="http://uipath.com/schema/1.0/dmn-ext/decision-model">
  <extensionElements><uipdm:qualityWarning>Citations carry a page and no source box.</uipdm:qualityWarning></extensionElements>
  <decision id="d" name="d"><description>Remote-work policy v2, effective 2026-01-01.</description></decision>
</definitions>"""


def test_record_text_reads_descriptions_and_quality_warnings():
    text = pc.record_text(ET.fromstring(RECORD_DMN))
    assert "no source box" in text and "Remote-work policy v2" in text


def test_record_names_each_missing_fixture_item(monkeypatch):
    monkeypatch.setattr(pc, "RECORD_FIXTURE", [("the FAQ, not applied", r"faq")])
    assert pc.record_missing("Assumptions recorded.") == ["the FAQ, not applied"]
    assert pc.record_missing("The FAQ's verbal approval was not applied.") == []
