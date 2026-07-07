#!/usr/bin/env python3
"""ExpenseReimbursement SDD -> case generation logical-integrity grader.

Checks that the generated caseplan.json encodes the intended employee expense
reimbursement process, not just a structurally valid case:

  - 5 primary stages exist with the expected names
  - Submission -> Manager Approval -> Finance Approval -> Payment -> Approved
    exists as a condition-driven transition path
  - Rejected and Withdrawn terminal lanes exist and are reachable from approval
    stages
  - Payment is gated by an approved Finance Approval decision and consumes the
    finance-selected payment method
  - the case starts from an expense_requests event trigger, not Manual
  - terminal lanes do not route back into the happy path
  - case-exit conditions cover happy-path completion and terminal dispositions
  - required task-type mix is present, including Payment Tracking as a child case
  - payment-specific data survives into the caseplan
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
from _shared.case_check import (  # noqa: E402
    assert_tasks_nested,
    find_stages,
    find_transitions,
    find_triggers,
    first_rule_of_condition,
    get_case_exit_conditions,
    iter_tasks,
    read_caseplan,
)


PRIMARY_STAGES = [
    "Submission",
    "Manager Approval",
    "Finance Approval",
    "Payment",
    "Approved",
]
TERMINAL_LANES = ["Rejected", "Withdrawn"]
EXPECTED_CASEPLAN = os.path.join(
    "ExpenseReimbursement",
    "ExpenseReimbursement",
    "caseplan.json",
)
REQUIRED_TASK_TYPES = {
    "api-workflow",
    "agent",
    "action",
    "execute-connector-activity",
    "wait-for-connector",
    "wait-for-timer",
    "process",
    "rpa",
    "case-management",
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _label(node: dict) -> str:
    return (node.get("data") or {}).get("label") or ""


def _find_stage_by_name(stages: list[dict], target: str) -> dict | None:
    tnorm = _norm(target)
    for stage in stages:
        if tnorm in _norm(_label(stage)):
            return stage
    return None


def _has_path(plan: dict, src_id: str, dst_id: str, max_hops: int = 8) -> bool:
    if src_id == dst_id:
        return True
    frontier = {src_id}
    seen = {src_id}
    for _ in range(max_hops):
        nxt = set()
        for node_id in frontier:
            for transition in find_transitions(plan, source=node_id):
                target = transition.get("target")
                if target == dst_id:
                    return True
                if target and target not in seen:
                    seen.add(target)
                    nxt.add(target)
        if not nxt:
            return False
        frontier = nxt
    return False


def _stage_tasks(stage: dict) -> list[dict]:
    tasks: list[dict] = []
    for lane in ((stage.get("data") or {}).get("tasks") or []):
        if isinstance(lane, dict):
            tasks.append(lane)
        elif isinstance(lane, list):
            tasks.extend(task for task in lane if isinstance(task, dict))
    return tasks


def _task_label(task: dict) -> str:
    data = task.get("data") or {}
    return (
        data.get("label")
        or data.get("name")
        or task.get("label")
        or task.get("name")
        or task.get("id")
        or ""
    )


def _task_text(task: dict) -> str:
    return repr(task).lower()


def _read_expense_caseplan() -> dict:
    if os.path.exists(EXPECTED_CASEPLAN):
        return read_caseplan(EXPECTED_CASEPLAN)
    return read_caseplan()


def _conditions_text(stage: dict) -> str:
    data = stage.get("data") or {}
    conditions = (data.get("entryConditions") or []) + (
        data.get("exitConditions") or []
    )
    return repr(conditions).lower()


def _node_by_id(plan: dict, node_id: str) -> dict | None:
    for node in plan.get("nodes") or []:
        if node.get("id") == node_id:
            return node
    return None


def _condition_references_stage(condition: dict, stage_id: str) -> bool:
    for group in condition.get("rules") or []:
        for rule in group or []:
            if (rule or {}).get("selectedStageId") == stage_id:
                return True
    return False


def _transition_condition_text(plan: dict, source_id: str, target_id: str) -> str:
    source = _node_by_id(plan, source_id) or {}
    target = _node_by_id(plan, target_id) or {}
    source_data = source.get("data") or {}
    target_data = target.get("data") or {}
    conditions = [
        cond
        for cond in source_data.get("exitConditions") or []
        if cond.get("exitToStageId") == target_id
    ]
    conditions.extend(
        cond
        for cond in target_data.get("entryConditions") or []
        if _condition_references_stage(cond, source_id)
    )
    return repr(conditions).lower()


def _has_incoming_from_any(plan: dict, target_id: str, source_ids: set[str]) -> bool:
    return any(
        transition.get("source") in source_ids
        for transition in find_transitions(plan, target=target_id)
    )


def _assert_expense_event_trigger(plan: dict) -> None:
    triggers = find_triggers(plan)
    if len(triggers) != 1:
        _fail(f"expected exactly 1 expense_requests trigger; got {len(triggers)}")

    trigger = triggers[0]
    uipath = ((trigger.get("data") or {}).get("uipath")) or {}
    service_type = uipath.get("serviceType")
    if service_type != "Intsvc.EventTrigger":
        _fail(
            "ExpenseReimbursement must start from an Intsvc.EventTrigger, "
            f"not {service_type or 'Manual'}"
        )

    trigger_text = repr(trigger).lower()
    if "expense_requests" not in trigger_text:
        _fail("event trigger must preserve source object expense_requests")
    if "record" not in trigger_text or "created" not in trigger_text:
        _fail("event trigger must preserve record-created intent")


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")


def main():
    plan = _read_expense_caseplan()
    assert_tasks_nested(plan)
    _assert_expense_event_trigger(plan)

    all_stages = find_stages(plan, include_exception=True)
    if not all_stages:
        _fail("no stages found in caseplan")
    stage_labels = [_label(stage) for stage in all_stages]

    primary_nodes: dict[str, dict] = {}
    missing_primary = []
    for name in PRIMARY_STAGES:
        node = _find_stage_by_name(all_stages, name)
        if not node:
            missing_primary.append(name)
        else:
            primary_nodes[name] = node
    if missing_primary:
        _fail(
            f"missing primary stage(s) {missing_primary}; stages present: {stage_labels}"
        )

    terminal_nodes: dict[str, dict] = {}
    missing_terminal = []
    for name in TERMINAL_LANES:
        node = _find_stage_by_name(all_stages, name)
        if not node:
            missing_terminal.append(name)
        else:
            terminal_nodes[name] = node
    if missing_terminal:
        _fail(
            f"missing terminal lane(s) {missing_terminal}; stages present: {stage_labels}"
        )

    for src, dst in zip(PRIMARY_STAGES, PRIMARY_STAGES[1:]):
        if not _has_path(plan, primary_nodes[src]["id"], primary_nodes[dst]["id"]):
            _fail(f"no transition path from {src!r} to {dst!r}; happy path is broken")

    manager_id = primary_nodes["Manager Approval"]["id"]
    finance_id = primary_nodes["Finance Approval"]["id"]
    payment = primary_nodes["Payment"]
    payment_id = payment["id"]
    if not _has_incoming_from_any(
        plan,
        terminal_nodes["Rejected"]["id"],
        {manager_id, finance_id, payment_id},
    ):
        _fail(
            "Rejected lane exists but is not reachable from Manager Approval, "
            "Finance Approval, or Payment"
        )
    if not _has_incoming_from_any(
        plan,
        terminal_nodes["Withdrawn"]["id"],
        {manager_id, finance_id},
    ):
        _fail(
            "Withdrawn lane exists but is not reachable from Manager Approval "
            "or Finance Approval"
        )

    primary_ids = {node["id"] for node in primary_nodes.values()}
    for name, node in {**terminal_nodes, "Approved": primary_nodes["Approved"]}.items():
        leaks = [
            transition.get("target")
            for transition in find_transitions(plan, source=node["id"])
            if transition.get("target") in primary_ids
            and transition.get("target") != node["id"]
        ]
        if leaks:
            _fail(
                f"terminal stage/lane {name!r} should not route back into the "
                f"primary chain; transitions to {leaks}"
            )

    case_exits = get_case_exit_conditions(plan)
    if len(case_exits) < 3:
        _fail(
            f"expected >=3 case-exit conditions (happy + Rejected + Withdrawn); "
            f"got {len(case_exits)}"
        )
    happy_exit = False
    terminal_exit_ids: set[str] = set()
    terminal_ids = {node["id"] for node in terminal_nodes.values()}
    terminal_ids.add(primary_nodes["Approved"]["id"])
    for case_exit in case_exits:
        rule = first_rule_of_condition(case_exit) or {}
        rule_name = rule.get("rule")
        if rule_name == "required-stages-completed" and case_exit.get("marksCaseComplete") is True:
            happy_exit = True
        if rule_name in ("selected-stage-completed", "selected-stage-exited"):
            selected_id = rule.get("selectedStageId")
            if selected_id in terminal_ids:
                terminal_exit_ids.add(selected_id)
    if not happy_exit:
        _fail(
            "missing happy-path case-exit 'required-stages-completed' with "
            "marksCaseComplete=true"
        )
    missing_terminal_exits = [
        name for name, node in terminal_nodes.items() if node["id"] not in terminal_exit_ids
    ]
    if missing_terminal_exits:
        _fail(
            "case-exit conditions do not reference terminal lane(s): "
            + ", ".join(missing_terminal_exits)
        )

    tasks = list(iter_tasks(plan))
    if len(tasks) < 16:
        _fail(
            f"task volume too low: got {len(tasks)}, expected >=16 for the "
            "expense reimbursement case"
        )
    types_seen = {task.get("type") for task in tasks}
    missing_types = sorted(REQUIRED_TASK_TYPES - types_seen)
    if missing_types:
        _fail(
            f"missing required task type(s) {missing_types}; "
            f"types seen: {sorted(t for t in types_seen if t)}"
        )

    finance_conditions = _conditions_text(primary_nodes["Finance Approval"])
    if not all(
        term in finance_conditions
        for term in ("financedecision", "approved", "rejected")
    ):
        _fail(
            "Finance Approval must capture financeDecision with approved and "
            "rejected outcomes before downstream routing"
        )

    finance_to_payment_gate = _transition_condition_text(plan, finance_id, payment_id)
    if (
        "financedecision" not in finance_to_payment_gate
        or "approved" not in finance_to_payment_gate
    ):
        _fail("Payment transition must be gated by an approved financeDecision")

    payment_tasks = _stage_tasks(payment)
    payment_tasks_text = repr(payment_tasks).lower()
    if "selectedpaymentmethod" not in payment_tasks_text:
        _fail("Payment tasks must consume selectedPaymentMethod chosen by finance")
    if not any(task.get("type") == "rpa" for task in payment_tasks):
        _fail("Payment stage must contain an ERP reimbursement RPA task")
    if not any(task.get("type") == "wait-for-connector" for task in payment_tasks):
        _fail("Payment stage must wait for a payment-confirmation connector/webhook")
    payment_child_tasks = [
        task for task in payment_tasks if task.get("type") == "case-management"
    ]
    if not payment_child_tasks:
        _fail("Payment stage must contain a case-management child task")
    if not any(
        "payment" in _task_text(task) and "tracking" in _task_text(task)
        for task in payment_child_tasks
    ):
        labels = [_task_label(task) for task in payment_child_tasks]
        _fail(
            "Payment stage case-management task must reference Payment Tracking; "
            f"case-management task labels: {labels}"
        )

    plan_text = repr(plan).lower()
    required_terms = [
        "selectedpaymentmethod",
        "financedecision",
        "expense_requests",
        "expense_documents",
        "expense_comments",
        "workday",
        "outlook",
        "slack",
        "sap",
        "servicenow",
    ]
    missing_terms = [term for term in required_terms if term not in plan_text]
    if missing_terms:
        _fail(
            "caseplan lost expected expense-domain terms: "
            + ", ".join(missing_terms)
        )

    print(
        "OK: ExpenseReimbursement caseplan preserves 5-stage happy path, "
        "expense_requests event trigger, Rejected/Withdrawn terminal lanes, "
        "happy + terminal case-exits, "
        f"{len(tasks)} tasks across required types, and Payment Tracking child case"
    )


if __name__ == "__main__":
    main()
