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
