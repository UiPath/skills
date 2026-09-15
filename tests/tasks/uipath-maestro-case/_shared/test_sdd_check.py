"""Deterministic guards for case-design SDD authoring and plan checks."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sdd_check import (  # noqa: E402
    _colon_issues,
    _name_only,
    _return_to_origin_pairing_issue,
    _sdd_frontend_issues,
    _sdd_template_shape_issues,
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


def test_summary_sdd_is_rejected_as_non_template_shape():
    text = """
# Supplier Onboarding - Solution Design Document

## Source
/Users/example/Downloads/supplier-onboarding-bpmn-requirements.md

## Case Objective
Manage supplier onboarding.

## Stages
- Intake
- Review

## Task Plan
- T01 create case
"""
    issues = _sdd_template_shape_issues(text)
    assert any("first heading must be '# SDD" in issue for issue in issues)
    assert any("missing required heading '## Section 1: Case Definition'" in issue for issue in issues)
    assert any("summary-only heading '## Source'" in issue for issue in issues)
    assert any("summary-only heading '## Task Plan'" in issue for issue in issues)


def test_template_shaped_sdd_is_accepted_by_shape_check():
    text = """
# SDD — SupplierOnboarding

Case Definition Blueprint.

## Table of Contents

1. [Case Definition](#section-1-case-definition)
2. [Stages & Tasks](#section-2-stages--tasks)
3. [Personas & App Views](#section-3-personas--app-views)
4. [Integrations](#section-4-integrations)

## Section 1: Case Definition

### Case Metadata

| Property | Value |
|---|---|
| Case Name | SupplierOnboarding |

### Case Triggers

| T# | Trigger Type | Source | Configuration |
|---|---|---|---|
| T02 | Manual | Manual | N/A |

### Case Exit Conditions

| WHEN | IF | Marks Case Complete | Display Name |
|---|---|---|---|
| required-stages-completed | — | Yes | Complete |

### Case Variables

| Name | Category | Type | Source Trigger | Source Field | Default | Description |
|---|---|---|---|---|---|---|
| supplierId | In | string | T02 | supplierId | — | Supplier identifier |

## Section 2: Stages & Tasks

### Stage 1: Intake

**Type:** Stage
**Design Rationale:** Intake starts the case and captures supplier details.
**Description:** Capture the supplier request.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|---|---|---|---|
| case-entered | — | No | Entry |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|---|---|---|---|---|
| required-tasks-completed | — | exit-only | Yes | Complete |

#### Tasks

| # | Task Name | Type | Activation Mode | Starts When | Required | Run Only Once | Persona | SLA |
|---|---|---|---|---|---|---|---|---|
| 1 | Capture Supplier Details | action | parallel | stage enters | Yes | Yes | Supplier Manager | — |

##### Task 1.1: Capture Supplier Details

**Type:** action
**Activation Mode:** parallel
**Design Rationale:** A person reviews submitted supplier details.
**Description:** Capture and review supplier details.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| current-stage-entered | — | Entry |

**Task envelope** (every task — render after the Entry Condition table):

| Required | Run Only Once | Skip Condition |
|---|---|---|
| Yes | Yes | — |

###### Action Task Detail (type: `action`)

**HITL Implementation:** Action App: Supplier Intake

## Section 3: Personas & App Views

### Personas

| Persona | Stage Scope | Permissions | Description |
|---|---|---|---|
| Supplier Manager | Intake | View, Act | Reviews supplier requests |

### Process App Views

| App | View | Persona | Purpose | Key Components |
|---|---|---|---|---|
| Supplier App | Case List | Supplier Manager | Track work | List |

## Section 4: Integrations

### Integration Service Connectors

> None.
"""
    assert _sdd_template_shape_issues(text) == []


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


def test_stage_variable_sla_rules_are_checked():
    text = """
#### Stage SLA
| 1 | m | 80% | Notify | Notify |
##### Stage Variable SLA Rules
| Expression | SLA | Unit | Display Name |
|---|---|---|---|
| - | 0 | d | - |
| priority is Urgent | 10 | min | Urgent: SLA |
| priority is Standard | 5 | d | Standard SLA |
| priority is Escalated | 2 | w | Standard SLA |
"""
    issues = _sdd_frontend_issues(text)
    assert any("conditional rule requires an expression" in issue for issue in issues)
    assert any("count must be positive" in issue for issue in issues)
    assert any("minute count" in issue for issue in issues)
    assert any("SLA title is missing" in issue for issue in issues)
    assert any("SLA title contains ':'" in issue for issue in issues)
    assert any("duplicate SLA title 'Standard SLA'" in issue for issue in issues)


def test_sla_title_colon_ban_ignores_the_provenance_annotation():
    """A `_(source: ...)_` annotation is not part of the name.

    Nightly 2026-08-31 failed a finalized SDD with "SLA title contains ':'" for
    `| SLA Title | LoanOrigination Case SLA _(source: inferred-default:no title
    stated)_ |` — the colon was in the template's own provenance dialect, not
    in the title.
    """
    annotated = (
        "| SLA Title | LoanOrigination Case SLA "
        "_(source: inferred-default:no title stated)_ |"
    )
    assert _colon_issues(annotated) == []

    # A colon in the name itself is still a violation, annotation or not.
    violating = "| SLA Title | Loan: Origination _(source: inferred-default)_ |"
    assert any("SLA title contains ':'" in issue for issue in _colon_issues(violating))


def test_name_only_strips_annotations_but_keeps_the_name():
    assert (
        _name_only("LoanOrigination Case SLA _(source: inferred-default:no title stated)_")
        == "LoanOrigination Case SLA"
    )
    assert _name_only("Title (qualifier)") == "Title"
    assert _name_only("Plain Title") == "Plain Title"
    assert _name_only("Foo: Bar _(source: x:y)_") == "Foo: Bar"
