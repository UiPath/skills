#!/usr/bin/env python3
"""Assert that the staged Athena CM SDD keeps its evaluation-critical contract."""

from __future__ import annotations

import glob
import re
import sys


REQUIREMENTS = {
    "InstanceExternalId": r"\bInstanceExternalId\b",
    "event payload": r"\beventPayload\b",
    "Stage A": r"Stage\s*A",
    "Stage B": r"Stage\s*B",
    "Stage C": r"Stage\s*C",
    "StageATask1": r"\bStageATask1\b",
    "StageATask2": r"\bStageATask2\b",
    "StageBTask1": r"\bStageBTask1\b",
    "StageBTask2": r"\bStageBTask2\b",
    "StageCTask1": r"\bStageCTask1\b",
    "StageCTask2": r"\bStageCTask2\b",
    "StageCTask3": r"\bStageCTask3\b",
    "CaseManagerProc": r"\bCaseManagerProc\b",
    "case manager execution state": r"\bcaseCurrentExecutionState\b",
    "case manager rules decisions": r"\bcaseRulesDecisions\b",
    "case manager output": r"\bcaseManagerDecisions\b",
    "A2 dependency": r"\bselected-tasks-completed\b",
    "Stage C dependency": r"\bselected-stage-completed\b",
    "Stage C task entry": r"\bcurrent-stage-entered\b",
    "case completion": r"\brequired-stages-completed\b",
}

TASK_FLAGS = {
    "StageATask1": ("Yes", "No"),
    "StageATask2": ("Yes", "Yes"),
    "StageBTask1": ("No", "No"),
    "StageBTask2": ("Yes", "No"),
    "StageCTask1": ("No", "Yes"),
    "StageCTask2": ("No", "Yes"),
    "StageCTask3": ("Yes", "Yes"),
}


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def find_sdd() -> str:
    matches = sorted(
        path for path in glob.glob("**/sdd.md", recursive=True) if "/.venv/" not in path
    )
    if not matches:
        fail("no staged sdd.md found")
    if len(matches) > 1:
        fail(f"expected one staged sdd.md, found {matches}")
    return matches[0]


def require(text: str, description: str, pattern: str) -> None:
    if not re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL):
        fail(f"SDD is missing {description}")


def main() -> None:
    path = find_sdd()
    text = open(path, encoding="utf-8").read()

    for description, pattern in REQUIREMENTS.items():
        require(text, description, pattern)

    for task_name, (required, run_once) in TASK_FLAGS.items():
        valid_row = False
        for line in text.splitlines():
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if task_name not in cells:
                continue
            task_index = cells.index(task_name)
            remaining = cells[task_index + 1 :]
            if any(
                required == left and run_once == right
                for left, right in zip(remaining, remaining[1:])
            ):
                valid_row = True
                break
        if not valid_row:
            fail(
                f"SDD is missing {task_name} required/run-only-once settings "
                f"({required}/{run_once})"
            )

    event_positions = []
    for event in ("event1", "event2", "event3", "event4", "event5"):
        match = re.search(rf"\b{event}\b", text, flags=re.IGNORECASE)
        if not match:
            fail(f"router decision table is missing {event}")
        event_positions.append(match.start())
    if event_positions != sorted(event_positions):
        fail("router decision table must list event1 through event5 in order")

    print("OK: Athena CM SDD fixture contract preserved")


if __name__ == "__main__":
    main()
