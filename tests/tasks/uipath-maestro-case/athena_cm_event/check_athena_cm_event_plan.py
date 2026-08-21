#!/usr/bin/env python3
"""Assert that Phase 1 does not reinterpret Athena's authored task-entry rules."""

from __future__ import annotations

import glob
import re
import sys


EXPECTED_RULES = {
    "StageATask1": "current-stage-entered",
    "StageATask2": "selected-tasks-completed",
    "StageBTask1": "current-stage-entered",
    "StageBTask2": "current-stage-entered",
    "StageCTask1": "current-stage-entered",
    "StageCTask2": "current-stage-entered",
    "StageCTask3": "selected-tasks-completed",
}
SELECTED_PREDECESSORS = {
    "StageATask2": "StageATask1",
    "StageCTask3": "StageCTask2",
}


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def read_plan() -> str:
    matches = sorted(
        path
        for path in glob.glob("**/tasks/tasks.md", recursive=True)
        if "/.venv/" not in path
    )
    if len(matches) != 1:
        fail(f"expected one tasks/tasks.md, found {matches}")
    return open(matches[0], encoding="utf-8").read()


def task_section(plan: str, task_name: str) -> str:
    match = re.search(
        rf'(?ims)^##\s+T\d+:[^\n]*"{re.escape(task_name)}"[^\n]*\n'
        rf".*?(?=^##\s+T\d+:|\Z)",
        plan,
    )
    if not match:
        fail(f"tasks.md has no quoted T-entry for {task_name!r}")
    return match.group(0)


def field(section: str, name: str, task_name: str) -> str:
    match = re.search(
        rf"(?im)^(?:-\s*)?(?:\*\*)?{re.escape(name)}:(?:\*\*)?\s*"
        rf"`?([a-z][a-z0-9-]*)(?:\([^\n)]*\))?`?\s*$",
        section,
    )
    if not match:
        fail(f"{task_name} is missing {name} in its own task T-entry")
    return match.group(1).lower()


def main() -> None:
    plan = read_plan()
    for task_name, expected_rule in EXPECTED_RULES.items():
        section = task_section(plan, task_name)
        actual_rule = field(section, "entry-rule", task_name)
        mode = field(section, "activation-mode", task_name)
        if actual_rule != expected_rule:
            fail(
                f"{task_name} authored entry-rule is {expected_rule}, but tasks.md changes it "
                f"to {actual_rule} ({mode})"
            )
        if expected_rule == "current-stage-entered" and mode != "parallel":
            fail(f"{task_name} must preserve parallel/current-stage-entered, got {mode}/{actual_rule}")
        if expected_rule == "selected-tasks-completed" and mode not in {
            "conditional-gate",
            "fan-in",
        }:
            fail(
                f"{task_name} must preserve its explicit selected-task gate, got "
                f"{mode}/{actual_rule}"
            )

    for task_name, predecessor in SELECTED_PREDECESSORS.items():
        section = task_section(plan, task_name)
        if predecessor not in section:
            fail(f"{task_name} selected-task gate does not name predecessor {predecessor}")

    print("OK: Athena tasks.md preserves every authored task-entry rule")


if __name__ == "__main__":
    main()
