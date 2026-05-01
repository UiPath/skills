#!/usr/bin/env python3
"""ExceptionStage: two ExceptionStages (Issues + Critical), no edges, interrupting entries."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    find_edges,
    find_node_by_label,
    first_rule_of_condition,
    get_default_sla,
    iter_nodes_of_type,
    iter_stage_entry_conditions,
    iter_stage_exit_conditions,
    read_caseplan,
)


def main():
    plan = read_caseplan()

    process = find_node_by_label(plan, "Process")
    if process.get("type") != "case-management:Stage":
        sys.exit(
            f"FAIL: 'Process' node should be regular Stage, got type={process.get('type')!r}"
        )

    exception_nodes = list(iter_nodes_of_type(plan, "case-management:ExceptionStage"))
    labels = sorted((n.get("data") or {}).get("label") for n in exception_nodes)
    if len(exception_nodes) != 2:
        sys.exit(
            f"FAIL: expected 2 ExceptionStage nodes (Issues + Critical); "
            f"got {len(exception_nodes)} with labels {labels}"
        )
    if "Issues" not in labels or "Critical" not in labels:
        sys.exit(
            f"FAIL: ExceptionStage labels must include 'Issues' and 'Critical'; "
            f"got {labels}"
        )

    issues = find_node_by_label(plan, "Issues")
    critical = find_node_by_label(plan, "Critical")

    for label, node in (("Issues", issues), ("Critical", critical)):
        inbound = find_edges(plan, target=node["id"])
        outbound = find_edges(plan, source=node["id"])
        if inbound or outbound:
            sys.exit(
                f"FAIL: exception stage {label!r} must have no edges; "
                f"got inbound={len(inbound)} outbound={len(outbound)}"
            )

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
    if not critical_rule or critical_rule.get("rule") != "wait-for-connector":
        sys.exit(
            f"FAIL: 'Critical' interrupting rule should be 'wait-for-connector'; "
            f"got {critical_rule and critical_rule.get('rule')!r}"
        )
    critical_expr = critical_rule.get("conditionExpression") or ""
    if "critical_fault" not in critical_expr and "fault" not in critical_expr.lower():
        sys.exit(
            f"FAIL: 'Critical' wait-for-connector conditionExpression should mention "
            f"the fault event; got {critical_expr!r}"
        )

    for label, node in (("Issues", issues), ("Critical", critical)):
        exits = list(iter_stage_exit_conditions(node))
        if not any(ec.get("type") == "return-to-origin" for ec in exits):
            sys.exit(
                f"FAIL: {label!r} missing return-to-origin exit; "
                f"types={[ec.get('type') for ec in exits]}"
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
            f"FAIL: 'Issues' exception stage has no wait-for-timer task; "
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
        "OK: 2 ExceptionStages (Issues + Critical) with 0 edges each; Issues has "
        "interrupting selected-stage-exited entry referencing Process, "
        "return-to-origin exit, 2h SLA + sla-breached UserGroup escalation, AND a "
        "wait-for-timer task using timeDate (wait until 2026-05-01) with "
        "current-stage-entered task-entry; Critical has interrupting "
        "wait-for-connector entry on a fault event + return-to-origin exit"
    )


if __name__ == "__main__":
    main()
