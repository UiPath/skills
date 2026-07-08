#!/usr/bin/env python3
"""AgedInvoicePayment SDD -> case generation logical-integrity grader."""

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
    first_rule_of_condition,
    get_case_exit_conditions,
    iter_tasks,
    read_caseplan,
)


PRIMARY_STAGE_PATTERNS = [
    ("Intake", r"intake|registration"),
    ("Enrichment", r"enrichment|context"),
    ("Triage", r"triage"),
    ("AP Review", r"ap review|accounts payable|ownership"),
    ("Exception Resolution", r"exception resolution|resolution"),
    ("Supplier Collaboration", r"supplier collaboration|supplier"),
    ("Payment Risk", r"payment risk|risk"),
    ("Approval", r"approval"),
    ("Closure", r"closure|close"),
]

EXCEPTION_PATTERNS = {
    "SLA Escalation": r"sla.*escalation|escalation",
    "Automation Incident": r"automation.*incident|incident|automation failure|failed (api|rpa|automation)",
    "Reopen": r"reopen|supplier dispute",
    "Compliance Hold": r"compliance.*hold|payment.?risk.*hold|hold",
}

EXPECTED_CASEPLAN = os.path.join(
    "AgedInvoicePayment",
    "AgedInvoicePayment",
    "caseplan.json",
)


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _label(node: dict) -> str:
    return (node.get("data") or {}).get("label") or ""


def _text(value: object) -> str:
    return repr(value).lower()


def _find_stage(stages: list[dict], pattern: str) -> dict | None:
    rx = re.compile(pattern, re.I)
    for stage in stages:
        if rx.search(_label(stage)):
            return stage
    return None


def _stage_tasks(stage: dict) -> list[dict]:
    tasks: list[dict] = []
    for lane in ((stage.get("data") or {}).get("tasks") or []):
        if isinstance(lane, dict):
            tasks.append(lane)
        elif isinstance(lane, list):
            tasks.extend(task for task in lane if isinstance(task, dict))
    return tasks


def _has_path(plan: dict, src_id: str, dst_id: str, max_hops: int = 12) -> bool:
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


def _read_aged_caseplan() -> dict:
    if os.path.exists(EXPECTED_CASEPLAN):
        return read_caseplan(EXPECTED_CASEPLAN)
    return read_caseplan()


def _stage_condition_text(stage: dict) -> str:
    data = stage.get("data") or {}
    return _text((data.get("entryConditions") or []) + (data.get("exitConditions") or []))


def _case_exit_stage_ids(case_exits: list[dict]) -> set[str]:
    out: set[str] = set()
    for case_exit in case_exits:
        rule = first_rule_of_condition(case_exit) or {}
        if rule.get("rule") in ("selected-stage-completed", "selected-stage-exited"):
            selected_id = rule.get("selectedStageId")
            if selected_id:
                out.add(selected_id)
    return out


def main() -> None:
    plan = _read_aged_caseplan()
    assert_tasks_nested(plan)

    all_stages = find_stages(plan, include_exception=True)
    primary_stages = find_stages(plan, include_exception=False)
    if len(primary_stages) < 8:
        _fail(
            f"expected >=8 primary stages from the PDD's 9-stage design; "
            f"got {len(primary_stages)}: {[_label(s) for s in primary_stages]}"
        )

    primary_nodes: dict[str, dict] = {}
    for name, pattern in PRIMARY_STAGE_PATTERNS:
        stage = _find_stage(primary_stages, pattern)
        if not stage:
            _fail(
                f"missing primary stage family {name!r}; "
                f"stages present: {[_label(s) for s in primary_stages]}"
            )
        primary_nodes[name] = stage

    for (src, _), (dst, _) in zip(PRIMARY_STAGE_PATTERNS, PRIMARY_STAGE_PATTERNS[1:]):
        if not _has_path(plan, primary_nodes[src]["id"], primary_nodes[dst]["id"]):
            _fail(f"no transition path from {src!r} to {dst!r}; primary chain is broken")

    exception_nodes: dict[str, dict] = {}
    for name, pattern in EXCEPTION_PATTERNS.items():
        stage = _find_stage(all_stages, pattern)
        if not stage:
            _fail(
                f"missing exception lane {name!r}; stages present: "
                f"{[_label(s) for s in all_stages]}"
            )
        exception_nodes[name] = stage

    tasks = list(iter_tasks(plan))
    if len(tasks) < 18:
        _fail(f"task volume too low for aged invoice case: got {len(tasks)}, expected >=18")

    types_seen = {task.get("type") for task in tasks}
    missing_types = {
        "api-workflow",
        "agent",
        "action",
        "rpa",
        "wait-for-timer",
        "case-management",
    } - types_seen
    if missing_types:
        _fail(
            f"missing required task type(s) {sorted(missing_types)}; "
            f"types seen: {sorted(t for t in types_seen if t)}"
        )
    if not ({"execute-connector-activity", "wait-for-connector"} & types_seen):
        _fail(
            "missing connector task type; expected execute-connector-activity "
            "or wait-for-connector"
        )

    triage_text = _stage_condition_text(primary_nodes["Triage"]) + _text(_stage_tasks(primary_nodes["Triage"]))
    if "rootcause" not in _norm(triage_text):
        _fail("Triage stage must classify rootCause")
    if "priorityscore" not in _norm(triage_text):
        _fail("Triage stage must calculate priorityScore / SLA priority")

    payment_risk = primary_nodes["Payment Risk"]
    payment_risk_text = _text(payment_risk)
    if "paymentrisk" not in _norm(payment_risk_text):
        _fail("Payment Risk stage must carry payment-risk evidence/output")
    if not any(task.get("type") == "agent" for task in _stage_tasks(payment_risk)):
        _fail("Payment Risk stage must include an agent task")

    approval_text = _stage_condition_text(primary_nodes["Approval"])
    if "paymentrisk" not in _norm(approval_text) and "approved" not in approval_text:
        _fail("Approval stage must be gated by the Payment Risk decision/result")

    case_mgmt_tasks = [task for task in tasks if task.get("type") == "case-management"]
    if not any("payment" in _text(task) and "tracking" in _text(task) for task in case_mgmt_tasks):
        _fail("case-management task must reference the Payment Tracking child case")

    case_exits = get_case_exit_conditions(plan)
    if len(case_exits) < 2:
        _fail(f"expected >=2 case-exit conditions; got {len(case_exits)}")
    exit_stage_ids = _case_exit_stage_ids(case_exits)
    if primary_nodes["Closure"]["id"] not in exit_stage_ids and not any(
        (first_rule_of_condition(c) or {}).get("rule") == "required-stages-completed"
        for c in case_exits
    ):
        _fail("case exits must close on Closure or required-stages-completed")

    plan_text = _text(plan)
    required_terms = [
        "mock erp",
        "outlook",
        "servicenow",
        "slack",
        "sap",
        "supplier",
        "rootcause",
        "priorityscore",
        "paymenttracking",
    ]
    missing_terms = [term for term in required_terms if _norm(term) not in _norm(plan_text)]
    if missing_terms:
        _fail("caseplan lost expected aged-invoice terms: " + ", ".join(missing_terms))

    print(
        "OK: AgedInvoicePayment caseplan preserves the PDD-derived primary chain, "
        "exception lanes, task-type mix, triage root-cause/priority scoring, "
        "Payment Risk gate, Payment Tracking child case, and integration footprint"
    )


if __name__ == "__main__":
    main()
