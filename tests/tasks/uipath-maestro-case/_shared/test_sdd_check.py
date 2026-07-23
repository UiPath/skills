"""Deterministic guards for Phase-0/Phase-1 case authoring."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sdd_check import (  # noqa: E402
    _colon_issues,
    _return_to_origin_pairing_issue,
    _sdd_frontend_issues,
    _tasks_frontend_issues,
)


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


def test_return_to_origin_requires_canonical_completion_pairing():
    text = """
## Case Variables
| Name | Category | Type | Source Trigger | Source Field | Default | Description |
|---|---|---|---|---|---|---|
| caseId | In | String | Manual | caseId | — | Case identifier |

### Secondary Stage: Escalation
**Stage Kind:** secondary
**Interrupting:** Yes

#### Entry Conditions
| WHEN | IF |
|---|---|
| selected-stage-exited("Review") | — |

#### Exit Conditions
| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|---|---|---|---|---|
| selected-tasks-completed("Notify") | — | return-to-origin | No | Return |

### Case Exit Conditions
| WHEN | IF | Marks Case Complete | Display Name |
|---|---|---|---|
| required-stages-completed | — | Yes | Complete |
"""
    checker = Path(__file__).with_name("sdd_check.py")
    with tempfile.TemporaryDirectory() as workdir:
        Path(workdir, "sdd.md").write_text(text, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(checker)],
            cwd=workdir,
            capture_output=True,
            text=True,
            check=False,
        )

    assert result.returncode != 0
    assert (
        "return-to-origin requires 'required-tasks-completed' or "
        "'wait-for-connector' with Marks=Yes"
        in result.stdout + result.stderr
    )


def test_return_to_origin_accepts_both_completing_triggers():
    assert _return_to_origin_pairing_issue(
        "required-tasks-completed", True, "Escalation"
    ) is None
    assert _return_to_origin_pairing_issue(
        "wait-for-connector", True, "Escalation"
    ) is None
    assert _return_to_origin_pairing_issue(
        "selected-tasks-completed", False, "Escalation"
    )


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
