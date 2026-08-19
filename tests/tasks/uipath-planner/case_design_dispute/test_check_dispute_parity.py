#!/usr/bin/env python3
"""Behavioral tests for the dispute-design parity checker.

Every check is exercised against a compliant SDD AND against the regression it
exists to catch, so a check that silently passes everything fails here first.

Runs with no model and no tenant:

    python3 -m pytest tests/tasks/uipath-planner/case_design_dispute/test_check_dispute_parity.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_dispute_parity import (  # noqa: E402
    Sdd,
    check_adhoc_stage_exit,
    check_dropped_terminal,
    check_ondemand_actions,
    check_send_back_loop,
    check_wait_for_user_pairing,
)

ADHOC_TASK = """
##### Task 1.2: Ask the cardholder a question

**Type:** action
**Activation Mode:** adhoc

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `adhoc` | — | Manual |

**Task envelope**

| Required | Run Only Once | Skip Condition |
|---|---|---|
| No | No | — |
"""

ACTION_TASK = """
##### Task 1.1: Check the dispute details

**Type:** action
**Activation Mode:** parallel

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `current-stage-entered` | — | Entry |

**Task envelope**

| Required | Run Only Once | Skip Condition |
|---|---|---|
| Yes | No | — |
"""

FRAUD_TASK = ADHOC_TASK.replace("Ask the cardholder a question", "Order a fraud team check").replace(
    "Task 1.2", "Task 1.3"
)


def stage(exit_rows: str, tasks: str = ACTION_TASK + ADHOC_TASK, label: str = "Stage 1: Checking the dispute") -> str:
    return f"""
### {label}

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|---|---|---|---|
| `case-entered` | — | No | Start |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|---|---|---|---|---|
{exit_rows}
{tasks}
"""


CLEAN_EXIT = "| `required-tasks-completed` | — | exit-only | Yes | Complete |"
ADHOC_EXIT = '| `selected-tasks-completed("Ask the cardholder a question")` | — | exit-only | No | Divert |'
GOOD_EXIT = '| `selected-tasks-completed("Check the dispute details")` | — | exit-only | No | Divert |'


def sdd(text: str) -> Sdd:
    return Sdd(text, "sdd.md")


# -- adhoc-stage-exit -------------------------------------------------------

def test_stage_exit_selecting_an_adhoc_task_is_flagged():
    issues = check_adhoc_stage_exit(sdd(stage(f"{CLEAN_EXIT}\n{ADHOC_EXIT}")))
    assert len(issues) == 1
    assert "Ask the cardholder a question" in issues[0]


def test_stage_exit_selecting_a_flow_started_task_is_accepted():
    assert check_adhoc_stage_exit(sdd(stage(f"{CLEAN_EXIT}\n{GOOD_EXIT}"))) == []


def test_task_entry_selecting_an_adhoc_task_is_not_flagged():
    """Only stage exit is restricted — a task-entry selector may name an adhoc task."""
    text = stage(CLEAN_EXIT) + """
##### Task 1.4: Summarize findings

**Type:** action
**Activation Mode:** conditional-gate

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `selected-tasks-completed("Ask the cardholder a question")` | — | After ask |
"""
    assert check_adhoc_stage_exit(sdd(text)) == []


# -- ondemand-actions -------------------------------------------------------

def test_missing_ondemand_actions_is_flagged():
    issues = check_ondemand_actions(sdd(stage(CLEAN_EXIT, tasks=ACTION_TASK)))
    assert len(issues) == 1
    assert "at least 2 adhoc tasks" in issues[0]


def test_required_adhoc_task_is_flagged():
    blocking = ADHOC_TASK.replace("| No | No | — |", "| Yes | No | — |")
    issues = check_ondemand_actions(sdd(stage(CLEAN_EXIT, tasks=blocking + FRAUD_TASK)))
    assert len(issues) == 1
    assert "Required: Yes" in issues[0]


def test_two_optional_adhoc_tasks_pass():
    assert check_ondemand_actions(sdd(stage(CLEAN_EXIT, tasks=ADHOC_TASK + FRAUD_TASK))) == []


# -- wait-for-user pairing --------------------------------------------------

WAIT_EXIT = "| `required-tasks-completed` | — | wait-for-user | Yes | Park |"
PICKER_STAGE = """
### Stage 4: Refunding the cardholder

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|---|---|---|---|
| `user-selected-stage` | — | No | Chosen |
"""


def test_wait_for_user_without_picker_entry_is_flagged():
    issues = check_wait_for_user_pairing(sdd(stage(WAIT_EXIT)))
    assert len(issues) == 1
    assert "user-selected-stage entry" in issues[0]


def test_neither_half_modeled_is_flagged():
    issues = check_wait_for_user_pairing(sdd(stage(CLEAN_EXIT)))
    assert len(issues) == 1
    assert "park until a person picks" in issues[0]


def test_both_halves_pass():
    assert check_wait_for_user_pairing(sdd(stage(WAIT_EXIT) + PICKER_STAGE)) == []


# -- dropped terminal + send-back ------------------------------------------

def test_missing_dropped_lane_is_flagged():
    assert len(check_dropped_terminal(sdd(stage(CLEAN_EXIT)))) == 1


def test_dropped_lane_present_passes():
    text = stage(CLEAN_EXIT) + "\n### Secondary Stage: Dispute dropped\n"
    assert check_dropped_terminal(sdd(text)) == []


def test_send_back_loop_detected(tmp_path):
    path = tmp_path / "sdd.md"
    path.write_text(stage("| `required-tasks-completed` | — | return-to-origin | Yes | Back |"), encoding="utf-8")
    parsed = Sdd(path.read_text(encoding="utf-8"), str(path))
    assert check_send_back_loop(parsed) == []


# -- draft-shaped documents -------------------------------------------------
# A pre-finalization draft carries per-task Entry Condition tables and a
# per-stage Tasks summary, but no `**Activation Mode:**` line and no
# `**Task envelope**` block (see case_finalize_draft/fixtures/sdd.draft.md).
# Both checks must still work off that shape.

DRAFT_STAGE = """
### Stage 1: Checking the dispute (`stage-checking`)

**Type:** Stage
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `case-entered` | — | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | wait-for-user | Yes |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Check the dispute details | action | Yes | No | Analyst | — |
| 2 | Ask the cardholder a question | action | No | No | Analyst | — |
| 3 | Order a fraud team check | action | No | No | Analyst | — |

##### Task 1.1: Check the dispute details (`t01`)

**Type:** action

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

##### Task 1.2: Ask the cardholder a question (`t02`)

**Type:** action

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `adhoc` | — |

##### Task 1.3: Order a fraud team check (`t03`)

**Type:** action

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `adhoc` | — |

### Secondary Stage: Dispute dropped (`stage-dropped`)

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `user-selected-stage` | — | Yes |
"""


def test_draft_shape_detects_adhoc_tasks_and_required_from_the_summary_table():
    parsed = sdd(DRAFT_STAGE)
    assert set(parsed.adhoc_tasks) == {"Ask the cardholder a question", "Order a fraud team check"}
    assert parsed.task_required["Check the dispute details"] == "Yes"
    assert parsed.task_required["Ask the cardholder a question"] == "No"
    assert check_ondemand_actions(parsed) == []


def test_draft_shape_pairing_and_selectors():
    parsed = sdd(DRAFT_STAGE)
    assert check_wait_for_user_pairing(parsed) == []
    assert check_adhoc_stage_exit(parsed) == []
    assert check_dropped_terminal(parsed) == []


def test_draft_shape_flags_an_adhoc_selector_on_stage_exit():
    text = DRAFT_STAGE.replace(
        "| `required-tasks-completed` | — | wait-for-user | Yes |",
        '| `required-tasks-completed` | — | wait-for-user | Yes |\n'
        '| `selected-tasks-completed("Order a fraud team check")` | — | exit-only | No |',
    )
    issues = check_adhoc_stage_exit(sdd(text))
    assert len(issues) == 1
    assert "Order a fraud team check" in issues[0]


def test_draft_shape_flags_a_required_adhoc_task():
    text = DRAFT_STAGE.replace("| 3 | Order a fraud team check | action | No |", "| 3 | Order a fraud team check | action | Yes |")
    issues = check_ondemand_actions(sdd(text))
    assert len(issues) == 1
    assert "Required: Yes" in issues[0]
