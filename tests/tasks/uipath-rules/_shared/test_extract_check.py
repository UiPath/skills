"""Unit tests for extract_check.py. Run with ``pytest`` from any directory.

The grader is the answer key for the extraction tasks, so these pin that a table laid out as the Extraction Guide
asks (deny rows, approval rows that restate each criterion, a missing-information row last) passes every scenario,
that the usual misreadings each fail one, and that the tests.json check accepts the guide's format.
"""

import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import extract_check as ec  # noqa: E402

DMN = "https://www.omg.org/spec/DMN/20230324/MODEL/"

# serviceDays, requestAmount, hasDirectorPreApproval, hasMedicalAccommodation -> outcome
GOLD = [
    ("refer_service_missing", ("null", "-", "-", "-"), "Refer"),
    ("refer_amount_missing", ("-", "null", "-", "-"), "Refer"),
    ("deny_over_cap", ("-", "> 2000", "-", "-"), "Deny"),
    ("deny_short_service", ("< 90", "-", "-", "false"), "Deny"),
    ("deny_no_preapproval", ("-", "(500..2000]", "false", "-"), "Deny"),
    ("approve_small", (">= 90", "<= 500", "-", "-"), "Approve"),
    ("approve_small_accommodation", ("-", "<= 500", "-", "true"), "Approve"),
    ("approve_mid", (">= 90", "(500..2000]", "true", "-"), "Approve"),
    ("approve_mid_accommodation", ("-", "(500..2000]", "true", "true"), "Approve"),
    ("missing_info", ("-", "-", "-", "-"), "Refer"),
]


def table(rows, hit_policy="FIRST"):
    t = ET.Element(f"{{{DMN}}}decisionTable", hitPolicy=hit_policy)
    for name in ec.INPUTS:
        expr = ET.SubElement(ET.SubElement(t, f"{{{DMN}}}input"), f"{{{DMN}}}inputExpression")
        ET.SubElement(expr, f"{{{DMN}}}text").text = name
    ET.SubElement(t, f"{{{DMN}}}output", name=ec.OUTPUT)
    for rule_id, cells, out in rows:
        r = ET.SubElement(t, f"{{{DMN}}}rule", id=rule_id)
        for cell in cells:
            ET.SubElement(ET.SubElement(r, f"{{{DMN}}}inputEntry"), f"{{{DMN}}}text").text = cell
        ET.SubElement(ET.SubElement(r, f"{{{DMN}}}outputEntry"), f"{{{DMN}}}text").text = f'"{out}"'
    return t


def wrong(rows):
    t = table(rows)
    return [label for label, values, expected in ec.SCENARIOS if ec.evaluate(t, dict(zip(ec.INPUTS, values))) != expected]


def test_the_guide_layout_passes_every_scenario():
    assert wrong(GOLD) == []


def test_an_approval_row_that_tests_nothing_fails_on_missing_facts():
    catch_all = [r for r in GOLD if not r[0].startswith(("refer", "approve", "missing"))] + [("approve", ("-",) * 4, "Approve")]
    assert "S15 nothing stated" in wrong(catch_all) and "S09 service length not stated" in wrong(catch_all)


def test_letting_the_accommodation_waive_pre_approval_fails():
    rows = [r for r in GOLD if r[0] != "deny_no_preapproval"]
    rows.insert(4, ("deny_no_preapproval", ("-", "(500..2000]", "false", "false"), "Deny"))
    assert "S14 accommodation does not waive director pre-approval" in wrong(rows)


def test_an_exclusive_500_boundary_fails():
    rows = [(i, (c[0], "< 500", c[2], c[3]) if c[1] == "<= 500" else c, o) for i, c, o in GOLD]
    assert "S02 boundaries: 90 days, $500" in wrong(rows)


def test_sending_missing_facts_to_a_default_deny_fails():
    rows = GOLD[2:-1] + [("default_deny", ("-",) * 4, "Deny")]
    assert {"S09 service length not stated", "S10 amount not stated", "S15 nothing stated"} <= set(wrong(rows))


TESTS = {
    "base": {"serviceDays": 120, "requestAmount": 300, "hasDirectorPreApproval": False, "hasMedicalAccommodation": False},
    "cases": [
        {"name": "small", "rule": "approve_small", "page": 1, "checks": "A request of $500 or less is approved.", "expected": "Approve"},
        {"name": "short", "rule": "deny_short_service", "page": 1, "checks": "at least 90 days of service",
         "inputs": {"serviceDays": 89}, "expected": "Deny"},
        {"name": "no_days", "rule": "refer_service_missing", "page": 1, "checks": "length of service is not stated",
         "omit": ["serviceDays"], "expected": "Refer"},
    ],
}


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    project = tmp_path / "ReimbursementRules"
    project.mkdir()
    (project / "project.uiproj").write_text(json.dumps({"Name": "ReimbursementRules", "ProjectType": "BusinessRules"}))
    root = ET.Element(f"{{{DMN}}}definitions")
    decision = ET.SubElement(root, f"{{{DMN}}}decision", id="d")
    decision.append(table(GOLD))
    ET.ElementTree(root).write(project / "rules.dmn")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(ec, "load", lambda: (project, project / "rules.dmn", root))
    return tmp_path


def write_tests(path, data):
    (path / "tests.json").write_text(json.dumps(data))


def test_the_guide_tests_format_passes(sandbox, capsys):
    write_tests(sandbox, TESTS)
    ec.grade_tests()
    assert "3 cases" in capsys.readouterr().out


@pytest.mark.parametrize("change, message", [
    (lambda d: d["cases"][2].pop("omit"), "missing-input case"),
    (lambda d: d["cases"].pop(1), "no case for ['Deny']"),
    (lambda d: d["cases"][0].pop("checks"), "lacks ['checks']"),
    (lambda d: d["cases"][0].update(rule="no_such_row"), "does not have"),
    (lambda d: d["base"].pop("serviceDays"), "expected every input"),
])
def test_a_tests_json_problem_fails(sandbox, capsys, change, message):
    data = json.loads(json.dumps(TESTS))
    change(data)
    write_tests(sandbox, data)
    with pytest.raises(SystemExit):
        ec.grade_tests()
    assert message in capsys.readouterr().out


def test_a_bare_list_is_not_the_guide_format(sandbox, capsys):
    write_tests(sandbox, TESTS["cases"])
    with pytest.raises(SystemExit):
        ec.grade_tests()
    assert '"base"' in capsys.readouterr().out


def test_the_skill_scripts_are_found_from_this_checkout():
    assert ec.skill_script("cite.mjs").is_file() and os.path.basename(ec.skill_script("check-uipdm.mjs")) == "check-uipdm.mjs"


def test_a_negated_cell_matches_a_missing_input_as_the_engine_does():
    t = table([("deny_short_service", ("-", "-", "-", "not(true)"), "Deny"), ("refer", ("-",) * 4, "Refer")])
    assert ec.evaluate(t, dict(zip(ec.INPUTS, (None, None, None, None)))) == "Deny"
