#!/usr/bin/env python3
"""Secondary stages: two secondary stages (Issues + Critical), interrupting entries, return-to-origin (edges retired)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    find_node_by_label,
    find_stages,
    first_rule_of_condition,
    get_default_sla,
    iter_stage_entry_conditions,
    iter_stage_exit_conditions,
    partition_return_to_origin_conditions,
    read_caseplan,
)


def main():
    plan = read_caseplan()

    process = find_node_by_label(plan, "Process")
    if process.get("type") != "case-management:Stage":
        sys.exit(
            f"FAIL: 'Process' node should be regular Stage, got type={process.get('type')!r}"
        )

    process_exits = list(iter_stage_exit_conditions(process))
    process_exit_only = [
        ec
        for ec in process_exits
        if ec.get("type") == "exit-only"
        and ec.get("marksStageComplete") is True
        and (first_rule_of_condition(ec) or {}).get("rule") == "required-tasks-completed"
    ]
    if not process_exit_only:
        sys.exit(
            "FAIL: 'Process' should have an explicit exit-only exit condition "
            "(required-tasks-completed, marksStageComplete=true); "
            f"got exit types {[ec.get('type') for ec in process_exits]}"
        )

    def _is_secondary(n):
        return (
            (n.get("data") or {}).get("stageType") == "secondary"
            or n.get("type") == "case-management:ExceptionStage"
        )

    secondary_nodes = [n for n in find_stages(plan, include_exception=True) if _is_secondary(n)]
    labels = sorted((n.get("data") or {}).get("label") for n in secondary_nodes)
    if len(secondary_nodes) != 2:
        sys.exit(
            f"FAIL: expected 2 secondary stages (Issues + Critical); "
            f"got {len(secondary_nodes)} with labels {labels}"
        )
    if "Issues" not in labels or "Critical" not in labels:
        sys.exit(
            f"FAIL: secondary stage labels must include 'Issues' and 'Critical'; "
            f"got {labels}"
        )

    issues = find_node_by_label(plan, "Issues")
    critical = find_node_by_label(plan, "Critical")

    # Edges retired: exception stages were never edge-wired anyway. Their
    # reachability contract is an interrupting entry condition + a
    # return-to-origin exit — both asserted below. Nothing edge-shaped remains.

    issues_entry = list(iter_stage_entry_conditions(issues))
    issues_interrupting = [c for c in issues_entry if c.get("isInterrupting") is True]
    if not issues_interrupting:
        sys.exit("FAIL: 'Issues' has no interrupting entry condition")
    issues_rule = first_rule_of_condition(issues_interrupting[0])
    if not issues_rule or issues_rule.get("rule") != "selected-stage-exited":
        sys.exit(
            f"FAIL: 'Issues' interrupting rule should be 'selected-stage-exited'; "
            f"got {issues_rule and issues_rule.get('rule')!r}"
        )
    if issues_rule.get("selectedStageId") != process["id"]:
        sys.exit(
            f"FAIL: 'Issues' rule.selectedStageId should be Process id "
            f"({process['id']}), got {issues_rule.get('selectedStageId')!r}"
        )

    critical_entry = list(iter_stage_entry_conditions(critical))
    critical_interrupting = [c for c in critical_entry if c.get("isInterrupting") is True]
    if not critical_interrupting:
        sys.exit("FAIL: 'Critical' has no interrupting entry condition")
    critical_rule = first_rule_of_condition(critical_interrupting[0])
    if not critical_rule or critical_rule.get("rule") != "selected-stage-exited":
        sys.exit(
            f"FAIL: 'Critical' interrupting rule should be 'selected-stage-exited'; "
            f"got {critical_rule and critical_rule.get('rule')!r}"
        )
    if critical_rule.get("selectedStageId") != process["id"]:
        sys.exit(
            f"FAIL: 'Critical' rule.selectedStageId should be Process id "
            f"({process['id']}), got {critical_rule.get('selectedStageId')!r}"
        )

    for label, node in (("Issues", issues), ("Critical", critical)):
        exits = list(iter_stage_exit_conditions(node))
        returns, invalid_returns = partition_return_to_origin_conditions(
            exits,
            allowed_rules=frozenset({"required-tasks-completed"}),
        )
        if not returns:
            sys.exit(
                f"FAIL: {label!r} missing canonical return-to-origin exit "
                f"(marksStageComplete=true + required-tasks-completed); "
                f"got {[(ec.get('type'), ec.get('marksStageComplete'), (first_rule_of_condition(ec) or {}).get('rule')) for ec in exits]}"
            )
        if invalid_returns:
            sys.exit(
                f"FAIL: {label!r} has malformed additional return-to-origin "
                f"exit(s); expected every return to use marksStageComplete=true "
                f"+ required-tasks-completed; got "
                f"{[(ec.get('marksStageComplete'), (first_rule_of_condition(ec) or {}).get('rule')) for ec in invalid_returns]}"
            )

    default = get_default_sla(issues)
    if not default:
        sys.exit(
            f"FAIL: 'Issues' has no default SLA on data.slaRules; "
            f"got {(issues.get('data') or {}).get('slaRules')!r}"
        )
    if default.get("count") != 2 or default.get("unit") != "h":
        sys.exit(
            f"FAIL: 'Issues' default SLA should be 2h "
            f"(count=2, unit=h); got count={default.get('count')!r}, "
            f"unit={default.get('unit')!r}"
        )

    escalations = default.get("escalationRule") or []
    if not escalations:
        sys.exit("FAIL: 'Issues' default SLA has no escalationRule[]")
    esc = escalations[0]
    if (esc.get("triggerInfo") or {}).get("type") != "sla-breached":
        sys.exit(
            f"FAIL: escalation triggerInfo.type should be 'sla-breached'; "
            f"got {(esc.get('triggerInfo') or {}).get('type')!r}"
        )
    recipients = ((esc.get("action") or {}).get("recipients")) or []
    if not any(r.get("scope") == "UserGroup" for r in recipients):
        sys.exit(
            f"FAIL: escalation should have a UserGroup recipient; "
            f"got scopes {[r.get('scope') for r in recipients]}"
        )

    issues_lanes = (issues.get("data") or {}).get("tasks") or []
    issues_tasks = [t for lane in issues_lanes for t in (lane or [])]
    timer_tasks = [t for t in issues_tasks if t.get("type") == "wait-for-timer"]
    if not timer_tasks:
        types_seen = sorted({t.get("type", "?") for t in issues_tasks})
        sys.exit(
            f"FAIL: 'Issues' secondary stage has no wait-for-timer task; "
            f"types seen: {types_seen}"
        )
    ack = timer_tasks[0]
    ack_conds = ack.get("entryConditions") or []
    if not ack_conds:
        sys.exit(
            "FAIL: 'Acknowledge Issue' has no task-entry conditions; "
            "expected current-stage-entered"
        )
    ack_rule = first_rule_of_condition(ack_conds[0])
    if not ack_rule or ack_rule.get("rule") != "current-stage-entered":
        sys.exit(
            f"FAIL: 'Acknowledge Issue' task-entry rule should be "
            f"'current-stage-entered'; got {ack_rule and ack_rule.get('rule')!r}"
        )

    ack_data = ack.get("data") or {}
    if ack_data.get("timerType") != "timeDate":
        sys.exit(
            f"FAIL: 'Acknowledge Issue' wait-for-timer should use the timeDate "
            f"branch (data.timerType='timeDate'); got "
            f"{ack_data.get('timerType')!r}"
        )
    ack_date = ack_data.get("timeDate") or ""
    if "2026-05-01" not in ack_date:
        sys.exit(
            f"FAIL: 'Acknowledge Issue' data.timeDate should include the "
            f"'2026-05-01' wait-until datetime; got {ack_date!r}"
        )

    print(
        "OK: Process is a regular Stage with an explicit exit-only exit condition "
        "(required-tasks-completed, marks complete); 2 secondary stages (Issues + "
        "Critical) reached via interrupting entries (edges retired); Issues has "
        "interrupting selected-stage-exited entry referencing Process, "
        "return-to-origin exit, 2h SLA + sla-breached UserGroup escalation, AND a "
        "wait-for-timer task using timeDate (wait until 2026-05-01) with "
        "current-stage-entered task-entry; Critical has a second interrupting "
        "selected-stage-exited entry referencing Process + return-to-origin exit"
    )


if __name__ == "__main__":
    main()
