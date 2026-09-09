"""Guard: a task's Activation Mode must produce the entry rule that mode implies.

`skills/uipath-planner/scripts/case/audit_sdd.py` is the design lane's gate. The
mode->rule table in case-design-layers-guide.md § Sequencing & activation was read
in full by the agent on run skill-case-phase-0-case-reasoning-regressions/00 and
still violated: every Activation Mode label was correct while not one entry rule
matched it (0 `runs-sequentially` rows in a 716-line SDD). The agent had
translated the requirement phrases positionally instead — "stage enters" ->
`current-stage-entered`, "after Collect Fees" ->
`selected-tasks-completed("Collect Fees")` — which emits the two
parallel-after-predecessor siblings as separate event-driven tasks rather than
one shared task set. It then self-verified with this auditor, got AUDIT OK, and
stopped. Re-reading the guide cannot fix what re-reading the guide already
failed to prevent; a gate names the contradiction at the point of repair.

    python3 -m pytest tests/scripts/test_audit_sdd_activation_mode_rule.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "skills" / "uipath-planner" / "scripts" / "case" / "audit_sdd.py"

spec = importlib.util.spec_from_file_location("audit_sdd", AUDIT)
audit_sdd = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(audit_sdd)


def _sdd(*tasks: str) -> str:
    body = "".join(tasks)
    return f"""### Stage 1: Issuing Permit

**Type:** Primary

#### Tasks
{body}"""


def _task(name: str, mode: str, *entry_rows: str) -> str:
    rows = "\n".join(f"| {row} | — | Entry Rule |" for row in entry_rows)
    return f"""
##### Task 1.1: {name}

**Type:** process
**Activation Mode:** {mode}

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
{rows}

**Task envelope**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |
"""


def _mode_findings(text: str) -> list[str]:
    return [
        f
        for f in audit_sdd.contract_findings(text, {})
        if "Activation Mode" in f
        and ("entry row" in f or "gates on selected-tasks-completed" in f)
    ]


def test_parallel_after_predecessor_gated_on_its_predecessor_is_flagged():
    """The observed defect: the mode label is right, the rule translates the phrase."""
    text = _sdd(
        _task(
            "Wait for Payment Confirmation",
            "parallel-after-predecessor",
            'selected-tasks-completed("Collect Fees")',
        )
    )
    findings = _mode_findings(text)
    assert findings, "a predecessor gate under parallel-after-predecessor must be reported"
    assert any("gates on selected-tasks-completed" in f for f in findings), findings
    assert all("Wait for Payment Confirmation" in f for f in findings), findings


def test_parallel_after_predecessor_on_the_shared_task_set_is_clean():
    """The negative control: the correct authoring must not be flagged."""
    text = _sdd(_task("Payment Deadline", "parallel-after-predecessor", "runs-sequentially"))
    assert _mode_findings(text) == []


def test_sequential_first_in_run_needs_runs_sequentially():
    """`runs-sequentially` goes on EVERY task in the run, including the first."""
    text = _sdd(_task("Collect Fees", "sequential", "current-stage-entered"))
    findings = _mode_findings(text)
    assert findings, "a sequential task entering on stage entry must be reported"
    assert "no runs-sequentially entry row" in findings[0], findings


def test_each_mode_paired_with_its_own_rule_is_clean():
    """Every row of the guide's mode->rule table, authored correctly."""
    pairs = [
        ("sequential", "runs-sequentially"),
        ("parallel-after-predecessor", "runs-sequentially"),
        ("parallel", "current-stage-entered"),
        ("event-triggered", 'wait-for-connector("Payment Confirmed")'),
        ("adhoc", "adhoc"),
        ("fan-in", 'selected-tasks-completed("Score", "Verify")'),
        ("conditional-gate", 'selected-tasks-completed("Wait for Payment Confirmation")'),
    ]
    for mode, rule in pairs:
        assert _mode_findings(_sdd(_task("T", mode, rule))) == [], f"{mode} + {rule}"


def test_fan_in_may_or_branches_with_a_no_branch_path():
    """Presence, not exclusivity — a convergence task legally carries both rules."""
    text = _sdd(
        _task(
            "Resolve Outcome",
            "fan-in",
            'selected-tasks-completed("Approve")',
            'selected-tasks-completed("Reject")',
            "current-stage-entered",
        )
    )
    assert _mode_findings(text) == []


def test_an_unknown_or_placeholder_mode_is_not_graded():
    """The template ships `<sequential | parallel | ...>`; a placeholder is not a defect."""
    text = _sdd(_task("T", "<sequential \\| parallel \\| adhoc>", "current-stage-entered"))
    assert _mode_findings(text) == []
