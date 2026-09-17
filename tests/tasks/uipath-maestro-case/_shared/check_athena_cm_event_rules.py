#!/usr/bin/env python3
"""Assert the build does not reinterpret Athena's authored task-entry rules.

The SDD states an explicit entry rule for all seven tasks. The build must carry
each one into `caseplan.json` unchanged — normalizing an authored
`selected-tasks-completed` gate into `runs-sequentially` (or vice versa) is the
regression this grades. `check_athena_cm_event_case.py` grades topology, flags,
identity, and the trigger; this file grades rule preservation for every task.
"""

from __future__ import annotations

import os
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_athena_cm_event_case import (  # noqa: E402
    CASEPLAN_PATH,
    stage_task,
)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import find_node_by_label, read_caseplan  # noqa: E402


# task name -> (authored entry rule, predecessor named by the rule's selector)
EXPECTED_RULES = {
    "StageATask1": ("current-stage-entered", None),
    "StageATask2": ("selected-tasks-completed", "StageATask1"),
    "StageBTask1": ("current-stage-entered", None),
    "StageBTask2": ("current-stage-entered", None),
    "StageCTask1": ("current-stage-entered", None),
    "StageCTask2": ("current-stage-entered", None),
    "StageCTask3": ("selected-tasks-completed", "StageCTask2"),
}
TASK_STAGES = {
    "StageATask1": "StageA",
    "StageATask2": "StageA",
    "StageBTask1": "StageB",
    "StageBTask2": "StageB",
    "StageCTask1": "StageC",
    "StageCTask2": "StageC",
    "StageCTask3": "StageC",
}


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def entry_rules(task: dict) -> list[dict]:
    rules = []
    for condition in task.get("entryConditions") or []:
        for group in condition.get("rules") or []:
            for rule in group or []:
                if isinstance(rule, dict):
                    rules.append(rule)
    return rules


def main() -> None:
    if not os.path.isfile(CASEPLAN_PATH):
        fail(f"expected generated caseplan at {CASEPLAN_PATH}")
    plan = read_caseplan(CASEPLAN_PATH)

    stages = {label: find_node_by_label(plan, label) for label in ("StageA", "StageB", "StageC")}
    tasks = {
        name: stage_task(plan, stages[TASK_STAGES[name]], name) for name in EXPECTED_RULES
    }

    for name, (expected_rule, predecessor) in EXPECTED_RULES.items():
        rules = entry_rules(tasks[name])
        if not rules:
            fail(
                f"{name} has no entry rule in caseplan.json — `validate` only warns about this, "
                f"but a task with no entry rule never starts and `case debug` hangs"
            )
        names = [rule.get("rule") for rule in rules]
        if expected_rule not in names:
            fail(
                f"{name} authored entry-rule is {expected_rule}, but the caseplan emits "
                f"{names} — an authored rule must survive the build unchanged"
            )
        if predecessor is None:
            continue
        expected_id = tasks[predecessor].get("id")
        gate = next(rule for rule in rules if rule.get("rule") == expected_rule)
        selected = gate.get("selectedTasksIds") or []
        if selected != [expected_id]:
            fail(
                f"{name} selected-task gate must name {predecessor} ({expected_id!r}); "
                f"got {selected!r}"
            )

    print("OK: Athena caseplan preserves every authored task-entry rule")


if __name__ == "__main__":
    main()
