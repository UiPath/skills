#!/usr/bin/env python3
"""Structural grader for the Athena CM event-case plan generated from sdd.md."""

from __future__ import annotations

import os
import sys
from typing import Iterable


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import (  # noqa: E402
    assert_tasks_nested,
    find_node_by_label,
    find_stages,
    find_triggers,
    get_case_exit_conditions,
    get_variables,
    read_caseplan,
)


CASEPLAN_PATH = os.path.join("AthenaCMEventCase", "AthenaCMEventCase", "caseplan.json")
TASK_FLAGS = {
    "StageATask1": (True, False),
    "StageATask2": (True, True),
    "StageBTask1": (False, False),
    "StageBTask2": (True, False),
    "StageCTask1": (False, True),
    "StageCTask2": (False, True),
    "StageCTask3": (True, True),
}


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def stage_label(stage: dict) -> str:
    return (stage.get("data") or {}).get("label") or stage.get("id") or "<unnamed>"


def binding_value(plan: dict, reference: object) -> str | None:
    """Resolve a binding default, following nested binding aliases when present."""
    value = reference
    visited: set[str] = set()
    bindings = {binding.get("id"): binding for binding in plan.get("bindings") or []}
    while isinstance(value, str) and value.startswith("=bindings."):
        binding_id = value.removeprefix("=bindings.").split(".", 1)[0]
        if binding_id in visited:
            return None
        visited.add(binding_id)
        binding = bindings.get(binding_id)
        if not binding:
            return None
        value = binding.get("default") or binding.get("resourceKey")
    return value if isinstance(value, str) else None


def task_names(plan: dict, task: dict) -> set[str]:
    data = task.get("data") or {}
    names = {
        task.get("displayName"),
        task.get("label"),
        data.get("displayName"),
        data.get("label"),
        binding_value(plan, data.get("name")),
    }
    return {name for name in names if isinstance(name, str)}


def stage_task(plan: dict, stage: dict, task_name: str) -> dict:
    for lane in (stage.get("data") or {}).get("tasks") or []:
        for task in lane or []:
            if task_name in task_names(plan, task):
                return task
    found = [
        sorted(task_names(plan, task))
        for lane in (stage.get("data") or {}).get("tasks") or []
        for task in lane or []
    ]
    fail(f"missing task {task_name!r} in {stage_label(stage)!r}; found {found}")


def iter_rules(conditions: Iterable[dict]) -> Iterable[dict]:
    for condition in conditions:
        for group in condition.get("rules") or []:
            for rule in group or []:
                if isinstance(rule, dict):
                    yield rule


def has_rule(conditions: Iterable[dict], rule_name: str, **expected: object) -> bool:
    return any(
        rule.get("rule") == rule_name
        and all(rule.get(field) == value for field, value in expected.items())
        for rule in iter_rules(conditions)
    )


def has_named_variable(plan: dict, name: str) -> bool:
    variables = get_variables(plan)
    return any(
        variable.get("name") == name
        for category in ("inputs", "inputOutputs")
        for variable in variables.get(category) or []
    )


def assert_task_flags(task: dict, task_name: str) -> None:
    required, run_once = TASK_FLAGS[task_name]
    if task.get("type") != "process":
        fail(f"{task_name} must be a process task; got {task.get('type')!r}")
    actual = (task.get("isRequired"), task.get("shouldRunOnlyOnce"))
    if actual != (required, run_once):
        fail(
            f"{task_name} must have isRequired={required} and "
            f"shouldRunOnlyOnce={run_once}; got {actual}"
        )


def assert_case_manager(plan: dict) -> None:
    manager = (plan.get("metadata") or {}).get("caseManagerData") or {}
    if manager.get("enabled") is not True:
        fail("metadata.caseManagerData must be enabled")
    manager_tasks = [
        task
        for lane in ((manager.get("data") or {}).get("tasks") or [])
        for task in lane or []
    ]
    if len(manager_tasks) != 1:
        fail(f"Case Manager must have exactly one process task; got {len(manager_tasks)}")
    manager_task = manager_tasks[0]
    if manager_task.get("type") != "process":
        fail(f"Case Manager task must have type='process'; got {manager_task.get('type')!r}")
    if "CaseManagerProc" not in task_names(plan, manager_task):
        fail("Case Manager process must resolve to 'CaseManagerProc'")
    data = manager_task.get("data") or {}
    input_names = {item.get("name") for item in data.get("inputs") or []}
    expected_inputs = {"caseCurrentExecutionState", "caseRulesDecisions", "eventPayload"}
    if not expected_inputs <= input_names:
        fail(f"Case Manager inputs missing {sorted(expected_inputs - input_names)}")
    output_names = {item.get("name") for item in data.get("outputs") or []}
    if "caseManagerDecisions" not in output_names:
        fail("Case Manager output must include 'caseManagerDecisions'")


def main() -> None:
    if not os.path.isfile(CASEPLAN_PATH):
        fail(f"expected generated caseplan at {CASEPLAN_PATH}")
    plan = read_caseplan(CASEPLAN_PATH)
    assert_tasks_nested(plan)

    triggers = find_triggers(plan)
    event_triggers = [
        trigger
        for trigger in triggers
        if ((trigger.get("data") or {}).get("uipath") or {}).get("serviceType")
        == "Intsvc.EventTrigger"
    ]
    if len(event_triggers) != 1 or len(triggers) != 1:
        fail(f"expected exactly one Intsvc.EventTrigger; got {len(triggers)} trigger(s)")

    metadata = plan.get("metadata") or {}
    if metadata.get("caseIdentifierType") != "external":
        fail("case identifier type must be external")
    if not has_named_variable(plan, "InstanceExternalId"):
        fail("missing root input 'InstanceExternalId'")
    if not has_named_variable(plan, "eventPayload"):
        fail("missing root input 'eventPayload'")
    if not str(metadata.get("caseIdentifier") or "").lower().endswith("instanceexternalid"):
        fail("external case identifier must reference InstanceExternalId")

    stages = find_stages(plan, include_exception=False)
    if len(stages) != 3:
        fail(f"expected exactly 3 primary stages; got {len(stages)}")
    stage_a = find_node_by_label(plan, "StageA")
    stage_b = find_node_by_label(plan, "StageB")
    stage_c = find_node_by_label(plan, "StageC")

    tasks = {
        "StageATask1": stage_task(plan, stage_a, "StageATask1"),
        "StageATask2": stage_task(plan, stage_a, "StageATask2"),
        "StageBTask1": stage_task(plan, stage_b, "StageBTask1"),
        "StageBTask2": stage_task(plan, stage_b, "StageBTask2"),
        "StageCTask1": stage_task(plan, stage_c, "StageCTask1"),
        "StageCTask2": stage_task(plan, stage_c, "StageCTask2"),
        "StageCTask3": stage_task(plan, stage_c, "StageCTask3"),
    }
    for task_name, task in tasks.items():
        assert_task_flags(task, task_name)

    if not has_rule(
        tasks["StageATask2"].get("entryConditions") or [],
        "selected-tasks-completed",
        selectedTasksIds=[tasks["StageATask1"].get("id")],
    ):
        fail("StageATask2 must start after StageATask1 completes")
    if not has_rule(
        (stage_b.get("data") or {}).get("exitConditions") or [],
        "required-tasks-completed",
    ) or not any(
        condition.get("marksStageComplete") is True
        for condition in (stage_b.get("data") or {}).get("exitConditions") or []
    ):
        fail("StageB must complete on required-tasks-completed")
    if not has_rule(
        (stage_c.get("data") or {}).get("entryConditions") or [],
        "selected-stage-completed",
        selectedStageId=stage_b.get("id"),
    ):
        fail("StageC must start after StageB completes")
    if not has_rule(
        tasks["StageCTask1"].get("entryConditions") or [],
        "current-stage-entered",
    ):
        fail("StageCTask1 must start on current-stage-entered")
    if not has_rule(
        (stage_c.get("data") or {}).get("exitConditions") or [],
        "required-tasks-completed",
    ) or not any(
        condition.get("marksStageComplete") is True
        for condition in (stage_c.get("data") or {}).get("exitConditions") or []
    ):
        fail("StageC must complete on required-tasks-completed")
    if not any(
        has_rule([condition], "required-stages-completed")
        and condition.get("marksCaseComplete") is True
        for condition in get_case_exit_conditions(plan)
    ):
        fail("case must complete on required-stages-completed")

    assert_case_manager(plan)
    print("OK: Athena CM caseplan preserves the staged SDD topology and Case Manager contract")


if __name__ == "__main__":
    main()
