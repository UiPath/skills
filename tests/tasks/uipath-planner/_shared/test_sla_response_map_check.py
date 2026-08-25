"""Unit tests for the SDD SLA Response Map contract guard."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sla_response_map_check import check, entry_condition_interrupting, parse_map_rows  # noqa: E402

HEADER = (
    "| Scope | SLA | Status | Response | Target | Interrupting | Rationale |\n"
    "|---|---|---|---|---|---|---|\n"
)


def sdd(rows: str, extra: str = "") -> str:
    return "### SLA Response Map\n\n" + HEADER + rows + "\n" + extra


def test_notify_only_rows_are_accepted():
    text = sdd(
        "| case | Case Resolution SLA | At-Risk | notify-only | — | — | owner just wants a heads-up |\n"
        "| case | Case Resolution SLA | Breached | notify-only | — | — | leadership tier notified |\n"
    )
    assert check(text) == []


def test_missing_section_is_reported():
    issues = check("## Section 1\n\nno map here\n")
    assert len(issues) == 1
    assert "no `SLA Response Map` section" in issues[0]


def test_notify_only_may_not_name_a_target():
    text = sdd(
        "| stage: Review | Review SLA | Breached | notify-only | Escalation Review | Yes | invented |\n"
    )
    issues = check(text)
    assert any("notify-only but names Target" in i for i in issues)
    assert any("notify-only but sets Interrupting" in i for i in issues)


def test_unknown_response_is_rejected():
    text = sdd("| case | Case Resolution SLA | Breached | escalate-somehow | X | Yes | freeform |\n")
    assert any("allowed:" in i for i in check(text))


def test_graph_response_without_entry_rule_is_reported():
    text = sdd("| case | Case Resolution SLA | Breached | enter-stage | Case SLA Review | Yes | takeover |\n")
    assert any("no `sla-status-change(...)` entry condition exists" in i for i in check(text))


def test_entry_rule_without_map_row_is_reported():
    text = sdd(
        "| case | Case Resolution SLA | At-Risk | notify-only | — | — | heads-up only |\n",
        "#### Stage Entry Conditions\n"
        "| WHEN | IF | Interrupting |\n|---|---|---|\n"
        '| sla-status-change("root","Case Resolution SLA","Case SLA breached") | - | Yes |\n',
    )
    assert any("with no matching SLA Response Map row" in i for i in check(text))


def test_interrupting_must_match_the_entry_row():
    text = sdd(
        "| case | Case Resolution SLA | Breached | enter-stage | Case SLA Oversight | No | parallel oversight |\n",
        "#### Stage Entry Conditions\n"
        "| WHEN | IF | Interrupting |\n|---|---|---|\n"
        '| sla-status-change("root","Case Resolution SLA","Case SLA breached") | - | Yes |\n',
    )
    issues = check(text)
    assert any("Interrupting mismatch" in i for i in issues), issues


def test_matching_interrupting_passes():
    text = sdd(
        "| case | Case Resolution SLA | Breached | enter-stage | Case SLA Oversight | No | parallel oversight |\n",
        "#### Stage Entry Conditions\n"
        "| WHEN | IF | Interrupting |\n|---|---|---|\n"
        '| sla-status-change("root","Case Resolution SLA","Case SLA breached") | - | No |\n',
    )
    assert check(text) == []


def test_start_task_via_task_entry_needs_no_interrupting_cell():
    """A Task Entry Condition table has no Interrupting column — a task entry interrupts nothing."""
    text = sdd(
        "| stage: Assess | Assess SLA | Breached | start-task | Assess | — | manager check, assessor keeps working |\n",
        "**Entry Condition:**\n"
        "| WHEN | IF | Display Name |\n|---|---|---|\n"
        '| sla-status-change("Assess","Assess SLA","Assess SLA Breached") | — | Start Senior Assessor Check |\n',
    )
    assert check(text) == []


def test_start_task_via_stage_re_entry_is_rejected():
    """`No` implies the stage-re-entry shape, which re-runs the breached stage's tasks.

    A start-task response is the follow-up task's own task-entry rule, so `—` is the
    only legal Interrupting value. See sla-response-shapes.md section 5, defect 4.
    """
    text = sdd(
        "| stage: Assess | Assess SLA | Breached | start-task | Assess | No | manager check, assessor keeps working |\n",
        "#### Stage Entry Conditions\n"
        "| WHEN | IF | Interrupting |\n|---|---|---|\n"
        '| sla-status-change("Assess","Assess SLA","Assess SLA Breached") | - | No |\n',
    )
    issues = check(text)
    assert issues, "start-task with Interrupting No must be rejected"
    assert any("start-task with Interrupting" in i for i in issues), issues


def test_start_task_may_not_interrupt():
    text = sdd(
        "| stage: Assess | Assess SLA | Breached | start-task | Assess | Yes | wrong |\n",
        "#### Stage Entry Conditions\n"
        "| WHEN | IF | Interrupting |\n|---|---|---|\n"
        '| sla-status-change("Assess","Assess SLA","Assess SLA Breached") | - | Yes |\n',
    )
    issues = check(text)
    assert any("start-task with Interrupting" in i for i in issues), issues


def test_enter_stage_without_interrupting_cell_is_still_reported():
    text = sdd(
        "| case | Case SLA | Breached | enter-stage | Case Escalation | Yes | lane takes over |\n",
        "#### Stage Entry Conditions\n"
        "| WHEN | IF | Display Name |\n|---|---|---|\n"
        '| sla-status-change("root","Case SLA","Case SLA Breached") | — | Enter Lane |\n',
    )
    assert any("no Yes/No Interrupting cell" in i for i in check(text))


def test_start_task_row_needs_a_target():
    text = sdd(
        "| stage: Review | Review SLA | Breached | start-task | — | No | manager check in Review |\n",
        "#### Stage Entry Conditions\n"
        "| WHEN | IF | Interrupting |\n|---|---|---|\n"
        '| sla-status-change("Review","Review SLA","Review breached") | - | No |\n',
    )
    assert any("names no Target" in i for i in check(text))


def test_template_placeholder_row_is_skipped():
    text = sdd("| {case} | {SLA Title} | {At-Risk} | {notify-only} | {—} | {—} | {why} |\n")
    issues = check(text)
    assert any("no data rows" in i for i in issues)


def test_parse_map_rows_flags_missing_columns():
    text = "### SLA Response Map\n\n| Scope | SLA | Response |\n|---|---|---|\n| case | X | notify-only |\n"
    _rows, issues = parse_map_rows(text)
    assert any("missing column(s)" in i for i in issues)


def test_entry_condition_interrupting_reads_the_last_yes_no_cell():
    line = '| sla-status-change("root","Case SLA","Breach") | - | No |\n'
    assert entry_condition_interrupting(line) == {'"root","Case SLA","Breach"': "no"}


def test_shared_title_wrong_scope_fails_closure():
    """P2 (PR #2718 review): a case-level and stage-level SLA sharing a title — a map row
    scoped to the wrong target must NOT satisfy closure for the entry's target."""
    text = sdd(
        "| case | Review SLA | Breached | enter-stage | Escalation | Yes | case handover |\n"
        + "\n#### Stage Entry Conditions\n\n"
        + "| WHEN | IF | Interrupting | Display Name |\n|---|---|---|---|\n"
        + '| `sla-status-change("Assess","Review SLA")` | — | Yes | Breach entry |\n'
    )
    issues = check(text)
    assert any("scoped" in i and "'Assess'" in i for i in issues), issues


def test_matching_scope_passes_closure():
    text = sdd(
        "| stage: Assess | Review SLA | Breached | enter-stage | Escalation | Yes | handover |\n"
        + "\n#### Stage Entry Conditions\n\n"
        + "| WHEN | IF | Interrupting | Display Name |\n|---|---|---|---|\n"
        + '| `sla-status-change("Assess","Review SLA")` | — | Yes | Breach entry |\n'
    )
    issues = [i for i in check(text) if "scoped" in i or "no SLA Response Map row" in i]
    assert not issues, issues
