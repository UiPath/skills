"""Unit tests for check_sequential_activation.py."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).parent / "check_sequential_activation.py"


def run(tmp_path: Path, sdd: str):
    p = tmp_path / "sdd.md"
    p.write_text(sdd, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(CHECKER), str(p)],
        capture_output=True, text=True,
    )


def task(name: str, mode: str, when: str, num: str = "1.1") -> str:
    return f"""
##### Task {num}: {name}

**Type:** action
**Activation Mode:** {mode}
**Description:** x

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| {when} | — | — |

**Task envelope**
"""


def stage(name: str, *tasks: str) -> str:
    return f"\n### Stage 1: {name}\n" + "".join(tasks)


# ---------------------------------------------------------------- passing cases

def test_sequential_with_runs_sequentially_passes(tmp_path):
    sdd = stage("Intake",
                task("A", "sequential", "runs-sequentially", "1.1"),
                task("B", "sequential", "runs-sequentially", "1.2"))
    r = run(tmp_path, sdd)
    assert r.returncode == 0, r.stderr
    assert "PASS" in r.stdout


def test_parallel_with_stage_entered_passes(tmp_path):
    sdd = stage("Intake",
                task("A", "parallel", "current-stage-entered", "1.1"),
                task("B", "parallel", "current-stage-entered", "1.2"))
    assert run(tmp_path, sdd).returncode == 0


def test_parallel_after_predecessor_with_runs_sequentially_passes(tmp_path):
    sdd = stage("Intake",
                task("A", "sequential", "runs-sequentially", "1.1"),
                task("B", "parallel-after-predecessor", "runs-sequentially", "1.2"),
                task("C", "parallel-after-predecessor", "runs-sequentially", "1.3"))
    assert run(tmp_path, sdd).returncode == 0


def test_fan_in_selecting_two_tasks_is_allowed(tmp_path):
    sdd = stage("Intake",
                task("A", "sequential", "runs-sequentially", "1.1"),
                task("B", "sequential", "runs-sequentially", "1.2"),
                task("C", "fan-in", 'selected-tasks-completed("A", "B")', "1.3"))
    assert run(tmp_path, sdd).returncode == 0


def test_non_immediate_dependency_is_allowed(tmp_path):
    """Selecting a task that is NOT the immediate predecessor is a legitimate gate."""
    sdd = stage("Intake",
                task("A", "sequential", "runs-sequentially", "1.1"),
                task("B", "sequential", "runs-sequentially", "1.2"),
                task("C", "conditional-gate", 'selected-tasks-completed("A")', "1.3"))
    assert run(tmp_path, sdd).returncode == 0


def test_event_triggered_task_is_not_graded(tmp_path):
    sdd = stage("Intake", task("A", "event-triggered", "wait-for-connector", "1.1"))
    assert run(tmp_path, sdd).returncode == 0


# ---------------------------------------------------------------- failing cases

def test_first_sequential_task_with_stage_entered_fails(tmp_path):
    """The observed defect: first task of a sequential run takes current-stage-entered."""
    sdd = stage("Intake",
                task("A", "sequential", "current-stage-entered", "1.1"),
                task("B", "sequential", "runs-sequentially", "1.2"))
    r = run(tmp_path, sdd)
    assert r.returncode == 1
    assert "including the first task" in r.stderr


def test_follower_selecting_immediate_predecessor_fails(tmp_path):
    """The other observed defect: selected-tasks-completed on the task directly above."""
    sdd = stage("Intake",
                task("A", "sequential", "runs-sequentially", "1.1"),
                task("B", "sequential", 'selected-tasks-completed("A")', "1.2"))
    r = run(tmp_path, sdd)
    assert r.returncode == 1
    assert "immediately previous task" in r.stderr


def test_sequential_carrying_both_rules_fails(tmp_path):
    sdd = f"""
### Stage 1: Intake

##### Task 1.1: A

**Type:** action
**Activation Mode:** sequential

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| runs-sequentially | — | — |
| current-stage-entered | — | — |

**Task envelope**
"""
    r = run(tmp_path, sdd)
    assert r.returncode == 1
    assert "must not also carry current-stage-entered" in r.stderr


def test_sequential_with_no_entry_rule_fails(tmp_path):
    sdd = "\n### Stage 1: Intake\n" + """
##### Task 1.1: A

**Type:** action
**Activation Mode:** sequential

**Task envelope**
"""
    assert run(tmp_path, sdd).returncode == 1


def test_counts_every_violation_not_just_the_first(tmp_path):
    sdd = stage("Intake",
                task("A", "sequential", "current-stage-entered", "1.1"),
                task("B", "sequential", 'selected-tasks-completed("A")', "1.2"))
    r = run(tmp_path, sdd)
    assert r.returncode == 1
    assert "2 sequential-activation violation(s)" in r.stderr


def test_violations_span_multiple_stages(tmp_path):
    sdd = (stage("Intake", task("A", "sequential", "current-stage-entered", "1.1"))
           + "\n### Stage 2: Closing\n"
           + task("Z", "sequential", "current-stage-entered", "2.1"))
    r = run(tmp_path, sdd)
    assert r.returncode == 1
    assert "2 sequential-activation violation(s)" in r.stderr


# ---------------------------------------------------------------- guard cases

def test_unfilled_template_fails_rather_than_passing_vacuously(tmp_path):
    sdd = stage("Intake", task("<TASK_NAME>", "<sequential \\| parallel>", "<current-stage-entered>", "1.1"))
    r = run(tmp_path, sdd)
    assert r.returncode == 1
    assert "placeholder" in r.stderr


def test_no_tasks_fails(tmp_path):
    r = run(tmp_path, "# Design\n\nNo stages here.\n")
    assert r.returncode == 1
    assert "zero task detail blocks" in r.stderr


def test_missing_file_fails(tmp_path):
    r = subprocess.run(
        [sys.executable, str(CHECKER), str(tmp_path / "nope.md")],
        capture_output=True, text=True,
    )
    assert r.returncode == 1


def test_secondary_stage_heading_is_parsed(tmp_path):
    sdd = "\n### Secondary Stage: Escalation\n" + task("A", "sequential", "current-stage-entered", "1.1")
    r = run(tmp_path, sdd)
    assert r.returncode == 1
    assert "Escalation" in r.stderr
