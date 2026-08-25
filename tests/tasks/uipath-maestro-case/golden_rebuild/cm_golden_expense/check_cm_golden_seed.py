#!/usr/bin/env python3
"""CM-Golden rebuild: exact Task 1.1 literal-seed fidelity check."""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from _shared.case_check import find_stages, read_caseplan  # noqa: E402


EXPECTED_CASEPLAN = os.path.join("CMGoldenExpense", "CMGoldenExpense", "caseplan.json")
FIXTURE_SDD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "sdd.md")


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")


def _read_plan() -> dict:
    if len(sys.argv) > 1:
        return read_caseplan(sys.argv[1])
    if os.path.exists(EXPECTED_CASEPLAN):
        return read_caseplan(EXPECTED_CASEPLAN)
    return read_caseplan()


def _expected_seed() -> dict:
    try:
        with open(FIXTURE_SDD, encoding="utf-8") as stream:
            sdd = stream.read()
    except OSError as exc:
        _fail(f"cannot read fixture SDD {FIXTURE_SDD}: {exc}")
    block = re.search(
        r"##### Task 1\.1: Analyze Expense Request(.*?)(?=\n---)",
        sdd,
        re.DOTALL,
    )
    row = None if block is None else re.search(
        r"^\|\s*expenseRequest\s*\|\s*object\s*\|\s*`(\{.*\})`",
        block.group(1),
        re.MULTILINE,
    )
    if row is None:
        _fail("fixture parse error: Task 1.1 expenseRequest literal not found")
    try:
        return json.loads(row.group(1))
    except ValueError as exc:
        _fail(f"fixture parse error: Task 1.1 expenseRequest is invalid JSON: {exc}")


def _stage_tasks(stage: dict) -> list[dict]:
    tasks: list[dict] = []
    for lane in ((stage.get("data") or {}).get("tasks") or []):
        if isinstance(lane, dict):
            tasks.append(lane)
        elif isinstance(lane, list):
            tasks.extend(task for task in lane if isinstance(task, dict))
    return tasks


def main():
    plan = _read_plan()
    matches = [
        task
        for stage in find_stages(plan, include_exception=True)
        for task in _stage_tasks(stage)
        if task.get("displayName") == "Analyze Expense Request"
    ]
    if len(matches) != 1:
        _fail(f"expected one Analyze Expense Request task; got {len(matches)}")
    inputs = {
        item.get("name"): item
        for item in ((matches[0].get("data") or {}).get("inputs") or [])
        if isinstance(item, dict)
    }
    if "expenseRequest" not in inputs:
        _fail("Analyze Expense Request is missing expenseRequest input")
    seed = inputs["expenseRequest"].get("value")
    if isinstance(seed, dict):
        actual_seed = seed
    elif isinstance(seed, str):
        try:
            actual_seed = json.loads(seed)
        except ValueError as exc:
            _fail(f"expenseRequest is not a JSON object: {exc}")
    else:
        _fail(
            "expenseRequest must be an object or a JSON-encoded object; "
            f"got {type(seed).__name__}"
        )
    if not isinstance(actual_seed, dict):
        _fail(f"expenseRequest must decode to an object; got {type(actual_seed).__name__}")
    if actual_seed != _expected_seed():
        _fail("Task 1.1 expenseRequest literal does not match fixtures/sdd.md")
    print("OK: Task 1.1 preserves the exact SDD expenseRequest object literal")


if __name__ == "__main__":
    main()
