"""Deterministic naming guards for Phase-0/Phase-1 case authoring."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sdd_check import _colon_issues  # noqa: E402


def test_stage_label_colon_is_rejected_but_heading_separator_is_allowed():
    text = "### Stage 1: Intake\n### Stage 2: Review: Legal"
    issues = _colon_issues(text)
    assert len(issues) == 1
    assert "stage name contains ':'" in issues[0]


def test_sla_title_colon_is_rejected():
    text = "| SLA Title | Notify: Manager |\n- display-name: \"Notify: Manager\""
    issues = _colon_issues(text)
    assert len(issues) == 2
    assert all("SLA title" in issue for issue in issues)


def test_names_without_colons_are_allowed():
    assert _colon_issues("### Secondary Stage: Exception Handling") == []
