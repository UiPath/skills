#!/usr/bin/env python3
"""SupplierOnboarding: the 39-task matrix, entry rules and conditional gates.

For every stage the staged SDD pins the task list, each task's type, its
Required / Run-Only-Once envelope and its authored entry rule. This grader
holds the build to that matrix, then checks the two §2 Stage 3 sign-off gates
and the Stage 4 bank-verification gate resolve to the sibling tasks they name.

Recipient objects are graded for the four tasks whose recipient the SDD pins
to a case-variable expression: `validate` never inspects `data.recipient`, and
a bare string there crashes the Studio Web canvas silently
(plugins/tasks/action/impl-json.md).
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
    has_expression,
    iter_rules,
    load_plan,
    rule_names,
    stage_of,
    tasks_of,
)

ENTRY_RULE = {
    "stage-entered": "current-stage-entered",
    "sequential": "runs-sequentially",
    "sla-stage": "sla-status-change",
    "sla-root": "sla-status-change",
    "gate": "selected-tasks-completed",
}


def resolve_tasks(plan: dict) -> dict[tuple[str, str], dict]:
    """``{(stage label, task name): task}`` for every expected task."""
    resolved: dict[tuple[str, str], dict] = {}
    for stage_name, expected in E.TASKS.items():
        stage = stage_of(plan, stage_name)
        actual = tasks_of(stage)
        if len(actual) != len(expected):
            names = [
                task.get("displayName") or (task.get("data") or {}).get("label") or task.get("id")
                for task in actual
            ]
            fail(
                f"{stage_name} must carry {len(expected)} tasks, got {len(actual)}: {names}"
            )
        seen_ids: set[str] = set()
        for spec in expected:
            task = find_task(plan, stage, spec["name"])
            if task is None:
                names = [
                    task.get("displayName") or (task.get("data") or {}).get("label")
                    for task in actual
                ]
                fail(f"{stage_name} is missing task {spec['name']!r}; tasks found: {names}")
            task_id = task.get("id")
            if task_id in seen_ids:
                fail(
                    f"{stage_name}: task {spec['name']!r} resolved to the same task id "
                    f"{task_id!r} as an earlier expected task — display names must be unique"
                )
            seen_ids.add(task_id)
            resolved[(stage_name, spec["name"])] = task
    return resolved


def check_matrix(plan: dict, resolved: dict[tuple[str, str], dict]) -> None:
    for stage_name, expected in E.TASKS.items():
        for spec in expected:
            task = resolved[(stage_name, spec["name"])]
            where = f"{stage_name} / {spec['name']}"
            if task.get("type") != spec["type"]:
                fail(f"{where}: type must be {spec['type']!r}, got {task.get('type')!r}")
            if bool(task.get("isRequired")) is not spec["required"]:
                fail(
                    f"{where}: isRequired must be {spec['required']}, got "
                    f"{task.get('isRequired')!r}"
                )
            if bool(task.get("shouldRunOnlyOnce")) is not spec["run_once"]:
                fail(
                    f"{where}: shouldRunOnlyOnce must be {spec['run_once']}, got "
                    f"{task.get('shouldRunOnlyOnce')!r}"
                )
            conditions = task.get("entryConditions") or []
            if not conditions:
                fail(
                    f"{where}: entryConditions is empty — a task with no entry rule is "
                    "never triggered and `validate` does not catch it"
                )
            names = rule_names(conditions)
            if spec["entry"] == "adhoc":
                if names != {"adhoc"}:
                    fail(
                        f"{where}: an ad-hoc (worker-launched) task carries an "
                        f"adhoc-only entry rule; rules found: {sorted(names)}"
                    )
            else:
                wanted = ENTRY_RULE[spec["entry"]]
                if wanted not in names:
                    fail(
                        f"{where}: authored entry rule is {wanted}, but the task carries "
                        f"{sorted(names)}"
                    )


def check_type_totals(plan: dict) -> None:
    totals: dict[str, int] = {}
    for stage in find_stages(plan, include_exception=True):
        for task in tasks_of(stage):
            totals[task.get("type")] = totals.get(task.get("type"), 0) + 1
    wrong = {
        task_type: (totals.get(task_type, 0), expected)
        for task_type, expected in E.TYPE_TOTALS.items()
        if totals.get(task_type, 0) != expected
    }
    if wrong:
        fail(
            "task-type mix does not match the SDD (got, expected): "
            f"{wrong}; all types present: {totals}"
        )


def selected_ids(conditions: list[dict]) -> set[str]:
    out: set[str] = set()
    for rule in iter_rules(conditions):
        if rule.get("rule") == "selected-tasks-completed":
            out.update(rule.get("selectedTasksIds") or [])
    return out


def check_sign_off_gate(plan: dict, resolved: dict[tuple[str, str], dict]) -> None:
    task = resolved[(E.COMPLIANCE, "Procurement Director Sign-off")]
    tier = resolved[(E.COMPLIANCE, "Determine Supplier Sign-off Tier")]
    conditions = task.get("entryConditions") or []
    if tier.get("id") not in selected_ids(conditions):
        fail(
            "Procurement Director Sign-off must gate on "
            'selected-tasks-completed("Determine Supplier Sign-off Tier") '
            f"(id {tier.get('id')!r}); selected ids: {sorted(selected_ids(conditions))}"
        )
    if not has_expression(conditions, E.SIGN_OFF_REQUIRED):
        fail(
            "Procurement Director Sign-off must be gated by "
            f"'=js:{E.SIGN_OFF_REQUIRED}'; expressions found: "
            f"{sorted(condition_expressions(conditions))}"
        )


def check_compliance_gate(plan: dict, resolved: dict[tuple[str, str], dict]) -> None:
    task = resolved[(E.COMPLIANCE, "Compliance Decision")]
    conditions = task.get("entryConditions") or []
    ids = {
        name: resolved[(E.COMPLIANCE, name)].get("id")
        for name in E.COMPLIANCE_GATE["selected_with"]
    }
    for guard, selectors in (
        (E.SIGN_OFF_NOT_REQUIRED, E.COMPLIANCE_GATE["selected_without"]),
        (E.SIGN_OFF_REQUIRED, E.COMPLIANCE_GATE["selected_with"]),
    ):
        matches = [
            condition for condition in conditions if has_expression([condition], guard)
        ]
        if not matches:
            fail(
                "Compliance Decision must carry both authored gates: no condition "
                f"guarded by '=js:{guard}'. Expressions found: "
                f"{sorted(condition_expressions(conditions))}"
            )
        expected_ids = {ids[name] for name in selectors}
        if not any(expected_ids <= selected_ids([condition]) for condition in matches):
            fail(
                f"Compliance Decision's '=js:{guard}' gate must select "
                f"{selectors}; selected ids on that gate: "
                f"{sorted(selected_ids(matches))} (expected {sorted(expected_ids)})"
            )


def check_portal_gate(plan: dict, resolved: dict[tuple[str, str], dict]) -> None:
    task = resolved[(E.SETUP, "Verify Supplier Portal Access")]
    conditions = task.get("entryConditions") or []
    if not has_expression(conditions, E.BANK_VERIFIED):
        fail(
            "Verify Supplier Portal Access runs only once the ERP record verified the "
            f"bank details: its entry rule must be guarded by '=js:{E.BANK_VERIFIED}'; "
            f"expressions found: {sorted(condition_expressions(conditions))}"
        )


def check_recipients(plan: dict, resolved: dict[tuple[str, str], dict]) -> None:
    by_name = {name: task for (_stage, name), task in resolved.items()}
    for name, expected_value in E.EXPRESSION_RECIPIENTS.items():
        task = by_name[name]
        recipient = (task.get("data") or {}).get("recipient")
        if not isinstance(recipient, dict):
            fail(
                f"{name}: data.recipient must be the object {{Type, Value}}, got "
                f"{type(recipient).__name__} ({recipient!r})"
            )
        value = recipient.get("Value", recipient.get("value"))
        if value != expected_value:
            fail(
                f"{name}: data.recipient Value must be {expected_value!r}, got {value!r}"
            )
        rtype = recipient.get("Type", recipient.get("type"))
        if rtype not in (2, 3):
            fail(
                f"{name}: an expression recipient is Type 3 (or 2 for a bare email "
                f"address), got {rtype!r}"
            )


def main() -> None:
    plan = load_plan()
    assert_tasks_nested(plan)
    resolved = resolve_tasks(plan)
    check_matrix(plan, resolved)
    check_type_totals(plan)
    check_sign_off_gate(plan, resolved)
    check_compliance_gate(plan, resolved)
    check_portal_gate(plan, resolved)
    check_recipients(plan, resolved)
    print(
        f"OK: all {E.TASK_TOTAL} tasks match the SDD matrix (type, required, "
        "run-once, entry rule), the sign-off / compliance / portal gates resolve to "
        "their sibling tasks, and expression recipients are objects"
    )


if __name__ == "__main__":
    main()
