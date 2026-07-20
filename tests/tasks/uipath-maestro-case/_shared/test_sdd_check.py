"""Deterministic naming guards for Phase-0/Phase-1 case authoring."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sdd_check import _colon_issues, _sdd_frontend_issues, _tasks_frontend_issues  # noqa: E402


def test_stage_label_colon_is_rejected_but_heading_separator_is_allowed():
    text = "### Stage 1: Intake\n### Stage 2: Review: Legal"
    issues = _colon_issues(text)
    assert len(issues) == 1
    assert "stage name contains ':'" in issues[0]


def test_sla_title_colon_is_rejected():
    text = "| SLA Title | Notify: Manager |\n- display-name: \"Notify: Manager\""
    issues = _colon_issues(text)
    assert len(issues) == 1
    assert "SLA title contains ':'" in issues[0]


def test_names_without_colons_are_allowed():
    assert _colon_issues("### Secondary Stage: Exception Handling") == []


def test_stage_names_must_be_unique_and_present():
    issues = _sdd_frontend_issues("### Stage 1: Intake\n### Stage 2: Intake\n### Secondary Stage:")
    assert any("duplicate stage name" in issue for issue in issues)
    assert any("stage name is missing" in issue for issue in issues)


def test_task_names_are_checked_for_colons():
    issues = _sdd_frontend_issues("##### Task 1.1: Review: Legal")
    assert any("task name contains ':'" in issue for issue in issues)


def test_sdd_sla_duration_bounds_are_checked():
    text = """
| Case-Level SLA | 0 d |
#### Stage SLA
| 1001 | min | 80% | Notify | Notify |
"""
    issues = _sdd_frontend_issues(text)
    assert any("count must be positive" in issue for issue in issues)
    assert any("minute count" in issue for issue in issues)


def test_tasks_sla_validation_matches_frontend_contract():
    tasks = '''
## T01: Set default SLA for "root"
- target: "root"
- display-name: "Default SLA"
- count: 10
- unit: min

## T02: Add conditional SLA rule for root case — urgent
- target: "root"
- display-name: "Default SLA"
- condition: ""
- count: 0
- unit: d

## T03: Add escalation rule for "root" — breach
- target: "root"
- display-name: "Notify: Manager"
- trigger-type: at-risk
'''
    issues = _tasks_frontend_issues(tasks, "tasks.md")
    assert any("minute count" in issue for issue in issues)
    assert any("conditional rule requires" in issue for issue in issues)
    assert any("count must be positive" in issue for issue in issues)
    assert any("escalation title contains ':'" in issue for issue in issues)
    assert any("requires at least one recipient" in issue for issue in issues)
    assert any("requires at-risk-percentage" in issue for issue in issues)
