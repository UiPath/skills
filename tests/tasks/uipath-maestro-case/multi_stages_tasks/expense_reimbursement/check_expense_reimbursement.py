#!/usr/bin/env python3
"""ExpenseReimbursement: bug-bash case structure and routing checks."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    assert_count,
    assert_tasks_nested,
    find_node_by_label,
    find_stages,
    find_transitions,
    find_triggers,
    first_rule_of_condition,
    get_case_exit_conditions,
    get_default_sla,
    get_variables,
    iter_stage_entry_conditions,
    iter_stage_exit_conditions,
    read_caseplan,
)


STAGE_SLA_MINUTES = {
    "Submission": 3,
    "Manager Approval": 5,
    "Finance Approval": 5,
    "Payment": 4,
    "Approved": 2,
    "Rejected": 2,
    "Withdrawn": 2,
}

EXPECTED_STAGE_TASK_TYPES = {
    "Submission": {"api-workflow", "execute-connector-activity", "agent", "action"},
    "Manager Approval": {
        "execute-connector-activity",
        "wait-for-connector",
        "action",
        "wait-for-timer",
    },
    "Finance Approval": {"api-workflow", "agent", "process", "action"},
    "Payment": {"rpa", "case-management", "wait-for-connector"},
    "Approved": {"execute-connector-activity"},
    "Rejected": {"rpa", "execute-connector-activity"},
    "Withdrawn": {"execute-connector-activity", "rpa"},
}

EXPECTED_VARIABLES = {
    "expense_id",
    "employee_name",
    "employee_email",
    "department",
    "expense_type",
    "amount",
    "currency",
    "description",
    "receipt_url",
    "submitted_date",
    "cost_center",
    "manager_email",
    "validation_result",
    "manager_decision",
    "finance_decision",
    "payment_reference",
    "payment_status",
    "rejection_reason",
}


def _stage_tasks(stage: dict) -> list[dict]:
    lanes = (stage.get("data") or {}).get("tasks") or []
    return [t for lane in lanes for t in (lane or []) if isinstance(t, dict)]


def _entry_rule_names(stage: dict) -> set[str]:
    return {
        (first_rule_of_condition(cond) or {}).get("rule")
        for cond in iter_stage_entry_conditions(stage)
    }


def _exit_targets(stage: dict) -> set[str]:
    return {
        cond.get("exitToStageId")
        for cond in iter_stage_exit_conditions(stage)
        if cond.get("exitToStageId")
    }


def _stage_label(stage: dict) -> str:
    return (stage.get("data") or {}).get("label") or stage.get("id") or "?"


def _assert_transition(plan: dict, source: dict, target: dict) -> None:
    if not find_transitions(plan, source=source["id"], target=target["id"]):
        sys.exit(
            f"FAIL: no condition-derived transition from {_stage_label(source)!r} "
            f"to {_stage_label(target)!r}; expected selected-stage entry or "
            f"exitToStageId routing"
        )


def _assert_stage_has_types(stage: dict, want_types: set[str]) -> None:
    tasks = _stage_tasks(stage)
    seen = {t.get("type") for t in tasks}
    missing = want_types - seen
    if missing:
        sys.exit(
            f"FAIL: stage {_stage_label(stage)!r} missing task type(s) "
            f"{sorted(missing)}; saw {sorted(t for t in seen if t)}"
        )


def _assert_terminal_has_no_outbound(stage: dict) -> None:
    targets = _exit_targets(stage)
    if targets:
        sys.exit(
            f"FAIL: terminal stage {_stage_label(stage)!r} should not route to "
            f"another stage; got exitToStageId target(s) {sorted(targets)}"
        )


def _variable_names(plan: dict) -> set[str]:
    variables = get_variables(plan)
    names: set[str] = set()
    for section in ("inputs", "outputs", "inputOutputs"):
        for item in variables.get(section) or []:
            if item.get("name"):
                names.add(item["name"])
            if item.get("id"):
                names.add(item["id"])
    return names


def main():
    plan = read_caseplan()
    assert_tasks_nested(plan)

    triggers = find_triggers(plan)
    assert_count(len(triggers), 1, "trigger node(s)")
    trigger_uipath = (triggers[0].get("data") or {}).get("uipath") or {}
    if trigger_uipath.get("serviceType") != "Intsvc.EventTrigger":
        sys.exit(
            "FAIL: ExpenseReimbursement must start from an event trigger for "
            "expense_requests record creation, not a manual/timer trigger; "
            f"got data.uipath.serviceType={trigger_uipath.get('serviceType')!r}"
        )

    stages = find_stages(plan, include_exception=False)
    assert_count(len(stages), 7, "regular stage(s)")
    stage_by_label = {(_stage_label(stage)): stage for stage in stages}
    expected_labels = set(STAGE_SLA_MINUTES)
    missing_labels = expected_labels - set(stage_by_label)
    if missing_labels:
        sys.exit(
            f"FAIL: missing expected stage label(s) {sorted(missing_labels)}; "
            f"saw {sorted(stage_by_label)}"
        )

    root_sla = get_default_sla(plan)
    if not root_sla:
        sys.exit("FAIL: root case is missing default metadata.slaRules entry")
    if root_sla.get("count") != 15 or root_sla.get("unit") != "min":
        sys.exit(
            f"FAIL: root case SLA should be 15 min; got "
            f"count={root_sla.get('count')!r}, unit={root_sla.get('unit')!r}"
        )

    for label, minutes in STAGE_SLA_MINUTES.items():
        stage = stage_by_label[label]
        sla = get_default_sla(stage)
        if not sla:
            sys.exit(f"FAIL: stage {label!r} missing default data.slaRules entry")
        if sla.get("count") != minutes or sla.get("unit") != "min":
            sys.exit(
                f"FAIL: stage {label!r} SLA should be {minutes} min; got "
                f"count={sla.get('count')!r}, unit={sla.get('unit')!r}"
            )

    names = _variable_names(plan)
    missing_vars = EXPECTED_VARIABLES - names
    if missing_vars:
        sys.exit(
            f"FAIL: variables block missing expense case variable(s) "
            f"{sorted(missing_vars)}; saw {sorted(names)}"
        )

    for label, want_types in EXPECTED_STAGE_TASK_TYPES.items():
        _assert_stage_has_types(stage_by_label[label], want_types)

    submission = find_node_by_label(plan, "Submission")
    manager = find_node_by_label(plan, "Manager Approval")
    finance = find_node_by_label(plan, "Finance Approval")
    payment = find_node_by_label(plan, "Payment")
    approved = find_node_by_label(plan, "Approved")
    rejected = find_node_by_label(plan, "Rejected")
    withdrawn = find_node_by_label(plan, "Withdrawn")

    if "case-entered" not in _entry_rule_names(submission):
        sys.exit(
            f"FAIL: Submission must carry a case-entered entry rule; got "
            f"{sorted(r for r in _entry_rule_names(submission) if r)}"
        )
    if "user-selected-stage" not in _entry_rule_names(payment):
        sys.exit(
            f"FAIL: Payment must carry a user-selected-stage entry rule; got "
            f"{sorted(r for r in _entry_rule_names(payment) if r)}"
        )

    _assert_transition(plan, submission, manager)
    _assert_transition(plan, manager, finance)
    _assert_transition(plan, payment, approved)

    manager_targets = _exit_targets(manager)
    if rejected["id"] not in manager_targets or submission["id"] not in manager_targets:
        sys.exit(
            "FAIL: Manager Approval exits must route to both Rejected and "
            "Submission (return for corrections); got target IDs "
            f"{sorted(manager_targets)}"
        )
    finance_targets = _exit_targets(finance)
    if rejected["id"] not in finance_targets or withdrawn["id"] not in finance_targets:
        sys.exit(
            "FAIL: Finance Approval exits must route to Rejected and Withdrawn; "
            f"got target IDs {sorted(finance_targets)}"
        )
    payment_targets = _exit_targets(payment)
    if rejected["id"] not in payment_targets:
        sys.exit(
            "FAIL: Payment exit must route failed payments to Rejected; got "
            f"target IDs {sorted(payment_targets)}"
        )
    submission_targets = _exit_targets(submission)
    if withdrawn["id"] not in submission_targets:
        sys.exit(
            "FAIL: Submission exit must route employee withdrawal to Withdrawn; "
            f"got target IDs {sorted(submission_targets)}"
        )

    for terminal in (approved, rejected, withdrawn):
        _assert_terminal_has_no_outbound(terminal)

    case_exit_rules = get_case_exit_conditions(plan)
    withdrawn_exit = False
    for cond in case_exit_rules:
        rule = first_rule_of_condition(cond) or {}
        if (
            rule.get("rule") == "selected-stage-completed"
            and rule.get("selectedStageId") == withdrawn["id"]
            and cond.get("marksCaseComplete") is False
        ):
            withdrawn_exit = True
            break
    if not withdrawn_exit:
        sys.exit(
            "FAIL: case exit rules must include selected-stage-completed on "
            "Withdrawn with marksCaseComplete=false"
        )

    print(
        "OK: ExpenseReimbursement has event trigger placeholder/resolved shape, "
        "7 bug-bash stages, root 15min SLA plus stage SLAs "
        "(3/5/5/4/2/2/2 min), expense_request variables, broad task coverage "
        "across api-workflow/connector/agent/action/timer/wait/rpa/process/"
        "case-management, Payment user-selected-stage entry, and terminal "
        "routing to Approved/Rejected/Withdrawn with Withdrawn as non-completing "
        "case exit"
    )


if __name__ == "__main__":
    main()
