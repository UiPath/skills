#!/usr/bin/env python3
"""ExpenseReimbursementRunnable — structural audit of the generated caseplan.

Grades that the generated caseplan.json encodes the adapted (fully-automated)
employee expense reimbursement process, not just a structurally valid case:

  - 5 primary stages exist (Submission -> Manager Approval -> Finance Approval
    -> Payment -> Approved) chained as a condition-driven happy path
  - Rejected and Withdrawn terminal lanes exist and do not route back into the
    happy path
  - the case starts from a Manual trigger (so case debug can start it headlessly)
  - the AUTOMATED task-type mix is present (api-workflow, agent, process, rpa,
    wait-for-timer, case-management) and the human/connector types the runnable
    variant deliberately drops (action, execute-connector-activity,
    wait-for-connector) are ABSENT
  - a case-management (Payment Tracking) child task exists
  - case-exit conditions cover happy-path completion + the two terminal lanes

Mechanical only; runtime behaviour is graded by check_expense_runnable_debug.py.
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import (  # noqa: E402
    find_stages,
    find_transitions,
    find_triggers,
    first_rule_of_condition,
    get_case_exit_conditions,
    iter_tasks,
    read_caseplan,
)

EXPECTED_CASEPLAN = os.path.join(
    "ExpenseReimbursementRunnable", "ExpenseReimbursementRunnable", "caseplan.json"
)
EXPECTED_BINDINGS_V2 = os.path.join(
    "ExpenseReimbursementRunnable", "ExpenseReimbursementRunnable", "bindings_v2.json"
)
PRIMARY_STAGES = ["Submission", "Manager Approval", "Finance Approval", "Payment", "Approved"]
TERMINAL_LANES = ["Rejected", "Withdrawn"]
REQUIRED_TASK_TYPES = {
    "api-workflow", "agent", "process", "rpa", "wait-for-timer", "case-management",
}
# The automated runnable variant deliberately omits these (no HITL / no live connectors).
FORBIDDEN_TASK_TYPES = {"action", "execute-connector-activity", "wait-for-connector"}
REQUIRED_EXTERNAL_BINDINGS = {
    "Shared/uipath-maestro-case/NameToAgeFixed2.API Workflow": "API Workflow",
    "Shared/uipath-maestro-flow/CountLetters CodedAgent.CountLetters": "CountLetters",
    "Shared/uipath-agents/ProcurementProcess.ProcurementProcess": "ProcurementProcess",
    "Shared/uipath-maestro-flow/ProjectEuler RPA.RPA Workflow": "RPA Workflow",
    "Shared/uipath-maestro-case/CaseTest.Maestro Case": "Maestro Case",
}


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _label(node: dict) -> str:
    return (node.get("data") or {}).get("label") or ""


def _find_stage(stages: list[dict], target: str) -> dict | None:
    t = _norm(target)
    return next((s for s in stages if t in _norm(_label(s))), None)


def _has_path(plan: dict, src: str, dst: str, max_hops: int = 8) -> bool:
    if src == dst:
        return True
    frontier, seen = {src}, {src}
    for _ in range(max_hops):
        nxt = set()
        for nid in frontier:
            for tr in find_transitions(plan, source=nid):
                tgt = tr.get("target")
                if tgt == dst:
                    return True
                if tgt and tgt not in seen:
                    seen.add(tgt)
                    nxt.add(tgt)
        if not nxt:
            return False
        frontier = nxt
    return False


def _incoming_from(plan: dict, target_id: str, sources: set[str]) -> bool:
    return any(tr.get("source") in sources for tr in find_transitions(plan, target=target_id))


def _assert_bindings_v2_metadata(bindings: dict) -> None:
    """Reject metadata that the eval CLI's resource refresh cannot consume."""
    resources = bindings.get("resources")
    if not isinstance(resources, list):
        _fail("bindings_v2.json must contain a resources array")
    for index, resource in enumerate(resources):
        if not isinstance(resource, dict):
            _fail(f"bindings_v2.json resources[{index}] must be an object")
        metadata = resource.get("metadata") or {}
        if not isinstance(metadata, dict):
            _fail(f"bindings_v2.json resource {resource.get('key', index)!r} metadata must be an object")
        unsupported = sorted(set(metadata) - {"subType"})
        if unsupported:
            _fail(
                "bindings_v2.json resource "
                f"{resource.get('key', index)!r} has unsupported metadata key(s) "
                f"{unsupported}; only subType is supported by uip solution resources refresh"
            )


def _assert_required_external_bindings(bindings: dict) -> None:
    """Ensure aliases from the SDD are not used as deployed resource names."""
    resources = bindings.get("resources")
    if not isinstance(resources, list):
        _fail("bindings_v2.json must contain a resources array")
    names_by_key = {
        resource.get("key"): ((resource.get("value") or {}).get("name") or {}).get(
            "defaultValue"
        )
        for resource in resources
        if isinstance(resource, dict)
    }
    for key, expected_name in REQUIRED_EXTERNAL_BINDINGS.items():
        actual_name = names_by_key.get(key)
        if actual_name != expected_name:
            _fail(
                f"bindings_v2.json must bind {key!r} as deployed name "
                f"{expected_name!r}; got {actual_name!r}"
            )


def main():
    plan = read_caseplan(EXPECTED_CASEPLAN if os.path.exists(EXPECTED_CASEPLAN) else None)
    if not os.path.exists(EXPECTED_BINDINGS_V2):
        _fail(f"missing required {EXPECTED_BINDINGS_V2}")
    with open(EXPECTED_BINDINGS_V2, encoding="utf-8") as f:
        bindings = json.load(f)
    _assert_bindings_v2_metadata(bindings)
    _assert_required_external_bindings(bindings)

    # --- trigger: Manual, so `uip maestro case debug` can start the case headlessly
    triggers = find_triggers(plan)
    if len(triggers) != 1:
        _fail(f"expected exactly 1 trigger; got {len(triggers)}")
    stype = ((triggers[0].get("data") or {}).get("uipath") or {}).get("serviceType")
    if stype not in (None, "", "None"):
        _fail(f"runnable variant must start from a Manual trigger (serviceType None), not {stype}")

    # --- stages present
    stages = find_stages(plan, include_exception=True)
    labels = [_label(s) for s in stages]
    primary = {}
    for name in PRIMARY_STAGES:
        node = _find_stage(stages, name)
        if not node:
            _fail(f"missing primary stage {name!r}; stages present: {labels}")
        primary[name] = node
    terminal = {}
    for name in TERMINAL_LANES:
        node = _find_stage(stages, name)
        if not node:
            _fail(f"missing terminal lane {name!r}; stages present: {labels}")
        terminal[name] = node

    # --- happy-path chain
    for a, b in zip(PRIMARY_STAGES, PRIMARY_STAGES[1:]):
        if not _has_path(plan, primary[a]["id"], primary[b]["id"]):
            _fail(f"no transition path {a!r} -> {b!r}; happy path is broken")

    # --- terminals reachable + no leak back into the primary chain
    mgr, fin, pay = primary["Manager Approval"]["id"], primary["Finance Approval"]["id"], primary["Payment"]["id"]
    if not _incoming_from(plan, terminal["Rejected"]["id"], {mgr, fin, pay}):
        _fail("Rejected lane not reachable from Manager Approval / Finance Approval / Payment")
    if not _incoming_from(plan, terminal["Withdrawn"]["id"], {primary["Submission"]["id"], mgr, fin}):
        _fail("Withdrawn lane not reachable from Submission / Manager Approval / Finance Approval")
    primary_ids = {n["id"] for n in primary.values()}
    for name, node in {**terminal, "Approved": primary["Approved"]}.items():
        leaks = [tr.get("target") for tr in find_transitions(plan, source=node["id"])
                 if tr.get("target") in primary_ids and tr.get("target") != node["id"]]
        if leaks:
            _fail(f"terminal stage {name!r} routes back into the primary chain: {leaks}")

    # --- task-type mix: required present, forbidden absent
    tasks = list(iter_tasks(plan))
    types_seen = {t.get("type") for t in tasks}
    missing = sorted(REQUIRED_TASK_TYPES - types_seen)
    if missing:
        _fail(f"missing required automated task type(s) {missing}; seen: {sorted(t for t in types_seen if t)}")
    present_forbidden = sorted(FORBIDDEN_TASK_TYPES & types_seen)
    if present_forbidden:
        _fail(f"runnable variant must not contain HITL/connector task type(s) {present_forbidden} "
              "(they block headless debug)")

    # --- child case (Payment Tracking)
    child_tasks = [t for t in tasks if t.get("type") == "case-management"]
    if not child_tasks:
        _fail("Payment stage must contain a case-management child task (Payment Tracking)")

    # --- case-exit: happy completion + both terminal lanes
    case_exits = get_case_exit_conditions(plan)
    terminal_ids = {n["id"] for n in terminal.values()}
    happy = False
    terminal_seen: set[str] = set()
    for ce in case_exits:
        rule = first_rule_of_condition(ce) or {}
        rname = rule.get("rule")
        if rname == "required-stages-completed" and ce.get("marksCaseComplete") is True:
            happy = True
        if rname in ("selected-stage-completed", "selected-stage-exited") and rule.get("selectedStageId") in terminal_ids:
            terminal_seen.add(rule.get("selectedStageId"))
    if not happy:
        _fail("missing happy-path case-exit 'required-stages-completed' with marksCaseComplete=true")
    missing_term = [name for name, node in terminal.items() if node["id"] not in terminal_seen]
    if missing_term:
        _fail("case-exit conditions do not reference terminal lane(s): " + ", ".join(missing_term))

    print(
        f"OK: ExpenseReimbursementRunnable caseplan sound — 5-stage happy path + "
        f"Rejected/Withdrawn terminals, manual trigger, "
        f"{len(tasks)} tasks across automated types {sorted(REQUIRED_TASK_TYPES & types_seen)}, "
        f"no HITL/connector types, Payment Tracking child case, happy + terminal case-exits"
    )


if __name__ == "__main__":
    main()
