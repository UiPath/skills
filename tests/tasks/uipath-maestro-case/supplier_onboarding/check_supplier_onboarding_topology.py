#!/usr/bin/env python3
"""SupplierOnboarding: stage graph, routing guards, case exits, variables.

Grades the §1/§2 contract of the staged SDD that is independent of task
internals: seven stages (five primary + two secondary), the authored stage
entry / exit rules with their guard expressions, the three case exit rules,
the manual case trigger, and the case variables.

Task-level fidelity is graded by check_supplier_onboarding_tasks.py, SLA
wiring by check_supplier_onboarding_sla.py, resource resolution by
check_supplier_onboarding_bindings.py.
"""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))

from _shared.case_check import assert_tasks_nested  # noqa: E402
import supplier_onboarding_expected as E  # noqa: E402
from supplier_onboarding_plan import (  # noqa: E402
    condition_expressions,
    fail,
    find_stages,
    find_task,
    find_triggers,
    get_case_exit_conditions,
    get_variables,
    has_expression,
    iter_rules,
    load_plan,
    rule_names,
    stage_label,
    stage_of,
    stage_transitions,
)


def stage_ids(plan: dict) -> dict[str, str]:
    return {label: stage_of(plan, label).get("id") for label in E.ALL_STAGES}


def entry_conditions(stage: dict) -> list[dict]:
    return (stage.get("data") or {}).get("entryConditions") or []


def exit_conditions(stage: dict) -> list[dict]:
    return (stage.get("data") or {}).get("exitConditions") or []


def check_stage_set(plan: dict) -> None:
    every = find_stages(plan, include_exception=True)
    primary_ids = {id(stage) for stage in find_stages(plan, include_exception=False)}

    for label in E.PRIMARY_STAGES:
        if id(stage_of(plan, label)) not in primary_ids:
            fail(f"stage {label!r} must be a primary stage, not a secondary one")
    for label in E.SECONDARY_STAGES:
        if id(stage_of(plan, label)) in primary_ids:
            fail(
                f"stage {label!r} is an exception lane — author it as a secondary stage "
                "(data.stageType = \"secondary\")"
            )

    expected = len(E.ALL_STAGES)
    if len(every) != expected:
        fail(
            f"expected exactly {expected} stages ({len(E.PRIMARY_STAGES)} primary + "
            f"{len(E.SECONDARY_STAGES)} secondary), got {len(every)}: "
            f"{[stage_label(s) for s in every]}"
        )


def check_trigger(plan: dict) -> None:
    triggers = find_triggers(plan)
    if len(triggers) != 1:
        fail(f"expected exactly 1 case trigger (T02 Manual), got {len(triggers)}")
    inputs = (triggers[0].get("data") or {}).get("inputs") or {}
    service_type = inputs.get("serviceType")
    if service_type not in (None, "None"):
        fail(
            "the SDD's only trigger is Manual, so the trigger node must carry "
            f'data.inputs.serviceType "None"; got {service_type!r}'
        )


def check_transitions(plan: dict) -> None:
    ids = stage_ids(plan)
    actual = {(t["source"], t["target"]) for t in stage_transitions(plan)}
    missing = [
        f"{src} -> {dst}"
        for src, dst in E.EXPECTED_TRANSITIONS
        if (ids[src], ids[dst]) not in actual
    ]
    if missing:
        by_id = {v: k for k, v in ids.items()}
        readable = sorted(
            f"{by_id.get(s, s)} -> {by_id.get(t, t)}" for s, t in actual
        )
        fail(
            f"missing condition-derived stage hop(s): {missing}. "
            f"Hops found: {readable}"
        )


def check_entry_conditions(plan: dict) -> None:
    ids = stage_ids(plan)

    checking = entry_conditions(stage_of(plan, E.CHECKING))
    names = rule_names(checking)
    if "case-entered" not in names:
        fail(f"{E.CHECKING} must be entered on case-entered; rules found: {sorted(names)}")
    if "selected-stage-exited" not in names:
        fail(
            f"{E.CHECKING} must re-enter on selected-stage-exited(\"{E.BUYER}\") for the "
            f"send-back lane; rules found: {sorted(names)}"
        )
    if not has_expression(checking, E.SEND_BACK):
        fail(
            f"{E.CHECKING} send-back re-entry must be guarded by "
            f"'=js:{E.SEND_BACK}'; expressions found: {sorted(condition_expressions(checking))}"
        )

    for stage_name, source in (
        (E.BUYER, E.CHECKING),
        (E.COMPLIANCE, E.BUYER),
        (E.SETUP, E.COMPLIANCE),
        (E.ONBOARDED, E.SETUP),
    ):
        conditions = entry_conditions(stage_of(plan, stage_name))
        if not any(
            rule.get("rule") == "selected-stage-completed"
            and rule.get("selectedStageId") == ids[source]
            for rule in iter_rules(conditions)
        ):
            fail(
                f"{stage_name} must be entered on "
                f'selected-stage-completed("{source}"); rules found: '
                f"{sorted(rule_names(conditions))}"
            )

    rejected = entry_conditions(stage_of(plan, E.REJECTED))
    expected_sources = {ids[E.BUYER], ids[E.COMPLIANCE], ids[E.SETUP]}
    actual_sources = {
        rule.get("selectedStageId")
        for rule in iter_rules(rejected)
        if rule.get("rule") == "selected-stage-exited"
    }
    if not expected_sources <= actual_sources:
        fail(
            f"{E.REJECTED} must be entered on selected-stage-exited from "
            f"{E.BUYER}, {E.COMPLIANCE} and {E.SETUP} (3 authored origins); "
            f"rules found: {sorted(rule_names(rejected))}"
        )
    for guard in (E.BUYER_DECLINE, E.COMPLIANCE_REJECT, E.BANK_NOT_VERIFIED):
        if not has_expression(rejected, guard):
            fail(
                f"{E.REJECTED} entry is missing the guard '=js:{guard}'; "
                f"expressions found: {sorted(condition_expressions(rejected))}"
            )
    not_interrupting = [
        condition.get("displayName") or condition.get("id")
        for condition in rejected
        if condition.get("isInterrupting") is not True
    ]
    if not_interrupting:
        fail(
            f"every {E.REJECTED} entry condition is authored Interrupting=Yes; "
            f"these are not: {not_interrupting}"
        )

    withdrawn = entry_conditions(stage_of(plan, E.WITHDRAWN))
    if rule_names(withdrawn) != {"wait-for-connector"}:
        fail(
            f"{E.WITHDRAWN} is entered by the supplier-withdrawal connector event: "
            "its only entry rule must be wait-for-connector; rules found: "
            f"{sorted(rule_names(withdrawn))}"
        )
    if not any(condition.get("isInterrupting") is True for condition in withdrawn):
        fail(f"the {E.WITHDRAWN} connector entry must be Interrupting=Yes")


def completing_condition(conditions: list[dict], rule: str) -> dict | None:
    for condition in conditions:
        if condition.get("marksStageComplete") is True and rule in rule_names([condition]):
            return condition
    return None


def routing_conditions(conditions: list[dict], rule: str) -> list[dict]:
    return [
        condition
        for condition in conditions
        if condition.get("marksStageComplete") is not True
        and rule in rule_names([condition])
    ]


def check_exit_conditions(plan: dict) -> None:
    for label in E.ALL_STAGES:
        conditions = exit_conditions(stage_of(plan, label))
        if completing_condition(conditions, "required-tasks-completed") is None:
            fail(
                f"{label} must complete on a required-tasks-completed exit with "
                f"marksStageComplete=true; conditions found: "
                f"{[(c.get('displayName'), sorted(rule_names([c])), c.get('marksStageComplete')) for c in conditions]}"
            )

    buyer = exit_conditions(stage_of(plan, E.BUYER))
    completing = completing_condition(buyer, "required-tasks-completed")
    if not has_expression([completing], E.BUYER_APPROVE):
        fail(
            f"{E.BUYER}'s completing exit must be guarded by '=js:{E.BUYER_APPROVE}'; "
            f"expressions found: {sorted(condition_expressions([completing]))}"
        )
    decision = find_task(plan, stage_of(plan, E.BUYER), "Buyer Decision")
    if decision is None:
        fail(f"{E.BUYER} has no 'Buyer Decision' task to route its exits on")
    for guard in (E.BUYER_DECLINE, E.SEND_BACK):
        matches = [
            condition
            for condition in routing_conditions(buyer, "selected-tasks-completed")
            if has_expression([condition], guard)
        ]
        if not matches:
            fail(
                f"{E.BUYER} must carry a non-completing "
                f"selected-tasks-completed(\"Buyer Decision\") exit guarded by "
                f"'=js:{guard}'"
            )
        if not any(
            decision.get("id") in (rule.get("selectedTasksIds") or [])
            for rule in iter_rules(matches)
        ):
            fail(
                f"{E.BUYER}'s '=js:{guard}' exit must select the Buyer Decision task "
                f"(id {decision.get('id')!r})"
            )

    compliance = exit_conditions(stage_of(plan, E.COMPLIANCE))
    if not has_expression(
        [completing_condition(compliance, "required-tasks-completed")], E.SEND_TO_SETUP
    ):
        fail(
            f"{E.COMPLIANCE}'s completing exit must be guarded by "
            f"'=js:{E.SEND_TO_SETUP}'"
        )
    decision = find_task(plan, stage_of(plan, E.COMPLIANCE), "Compliance Decision")
    if decision is None:
        fail(f"{E.COMPLIANCE} has no 'Compliance Decision' task to route its exits on")
    reject_exits = [
        condition
        for condition in routing_conditions(compliance, "selected-tasks-completed")
        if has_expression([condition], E.COMPLIANCE_REJECT)
    ]
    if not reject_exits:
        fail(
            f"{E.COMPLIANCE} must carry a non-completing "
            "selected-tasks-completed(\"Compliance Decision\") exit guarded by "
            f"'=js:{E.COMPLIANCE_REJECT}'"
        )
    if not any(
        decision.get("id") in (rule.get("selectedTasksIds") or [])
        for rule in iter_rules(reject_exits)
    ):
        fail(
            f"{E.COMPLIANCE}'s reject exit must select the Compliance Decision task "
            f"(id {decision.get('id')!r})"
        )

    setup = exit_conditions(stage_of(plan, E.SETUP))
    erp = find_task(plan, stage_of(plan, E.SETUP), "Create Supplier Record in ERP")
    if erp is None:
        fail(f"{E.SETUP} has no 'Create Supplier Record in ERP' task")
    bank_exits = [
        condition
        for condition in routing_conditions(setup, "selected-tasks-completed")
        if has_expression([condition], E.BANK_NOT_VERIFIED)
    ]
    if not bank_exits:
        fail(
            f"{E.SETUP} must carry a non-completing "
            "selected-tasks-completed(\"Create Supplier Record in ERP\") exit guarded "
            f"by '=js:{E.BANK_NOT_VERIFIED}'"
        )
    if not any(
        erp.get("id") in (rule.get("selectedTasksIds") or [])
        for rule in iter_rules(bank_exits)
    ):
        fail(
            f"{E.SETUP}'s bank-verification-failed exit must select the "
            f"Create Supplier Record in ERP task (id {erp.get('id')!r})"
        )


def check_case_exits(plan: dict) -> None:
    ids = stage_ids(plan)
    conditions = get_case_exit_conditions(plan)
    completing = [
        condition
        for condition in conditions
        if condition.get("marksCaseComplete") is True
        and "required-stages-completed" in rule_names([condition])
    ]
    if not completing:
        fail(
            "case must complete on required-stages-completed with "
            "marksCaseComplete=true; case exit rules found: "
            f"{[(c.get('displayName'), sorted(rule_names([c])), c.get('marksCaseComplete')) for c in conditions]}"
        )
    for label in (E.REJECTED, E.WITHDRAWN):
        matches = [
            condition
            for condition in conditions
            if any(
                rule.get("rule") == "selected-stage-completed"
                and rule.get("selectedStageId") == ids[label]
                for rule in iter_rules([condition])
            )
        ]
        if not matches:
            fail(
                f'case must exit on selected-stage-completed("{label}"); '
                "no case exit rule selects that stage"
            )
        marking = [c for c in matches if c.get("marksCaseComplete") is True]
        if marking:
            fail(
                f'the "{label}" case exit is authored Marks Case Complete=No, but '
                f"{[c.get('displayName') or c.get('id') for c in marking]} sets it true"
            )


def check_variables(plan: dict) -> None:
    variables = get_variables(plan)
    inputs = {
        str(v.get("name")): v for v in variables.get("inputs") or [] if v.get("name")
    }
    missing = [name for name in E.IN_VARIABLES if name not in inputs]
    if missing:
        fail(
            f"case In-arguments missing from variables.inputs: {missing}; "
            f"present: {sorted(inputs)}"
        )
    wrong_type = [
        f"{name} (type={inputs[name].get('type')!r})"
        for name in E.FILE_VARIABLES
        if str(inputs[name].get("type") or "").lower() not in {"file", "octet-stream"}
    ]
    if wrong_type:
        fail(f"document In-arguments must carry type 'file': {wrong_type}")

    declared = {
        str(v.get("name"))
        for category in ("inputs", "outputs", "inputOutputs")
        for v in variables.get(category) or []
        if v.get("name")
    }
    missing_gates = [name for name in E.GATE_VARIABLES if name not in declared]
    if missing_gates:
        fail(
            f"case variables that gate routing are not declared: {missing_gates}; "
            f"declared: {sorted(declared)}"
        )


def main() -> None:
    plan = load_plan()
    assert_tasks_nested(plan)
    check_stage_set(plan)
    check_trigger(plan)
    check_transitions(plan)
    check_entry_conditions(plan)
    check_exit_conditions(plan)
    check_case_exits(plan)
    check_variables(plan)
    print(
        "OK: 5 primary + 2 secondary stages, manual trigger, all 8 authored stage "
        "hops, send-back / decline / reject / bank-failure guards, 3 case exit "
        "rules and the case variables match the staged SDD"
    )


if __name__ == "__main__":
    main()
