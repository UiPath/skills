"""Shared helpers for uipath-maestro-case single-node e2e checks.

Locates the generated `caseplan.json`, runs ``uip maestro case validate``,
and asserts that a task of the expected ``type`` exists somewhere in the
case definition. ``case-management`` tasks are allowed to land as skeletons
(empty ``data``) when the referenced sub-case isn't published on the tenant
— the test only cares that the task ``type`` was written correctly.
"""

from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
from typing import Any


def find_caseplan(pattern: str = "**/caseplan.json") -> str:
    matches = sorted(
        p for p in glob.glob(pattern, recursive=True) if "/.venv/" not in p
    )
    if not matches:
        _fail(f"No caseplan.json found matching {pattern}")
    if len(matches) > 1:
        joined = "\n  - ".join(matches)
        _fail(f"Multiple caseplan.json files match {pattern!r}:\n  - {joined}")
    return matches[0]


def read_caseplan(path: str | None = None) -> dict:
    p = path or find_caseplan()
    with open(p) as f:
        return json.load(f)


def iter_tasks(plan: dict):
    """Yield every task dict from every Stage / ExceptionStage node."""
    for node in plan.get("nodes") or []:
        node_type = node.get("type") or ""
        if not node_type.endswith("Stage") and "Stage" not in node_type:
            continue
        lanes = ((node.get("data") or {}).get("tasks")) or []
        for lane in lanes:
            for task in lane or []:
                yield task


def find_tasks_of_type(plan: dict, task_type: str) -> list[dict]:
    return [t for t in iter_tasks(plan) if t.get("type") == task_type]


def assert_validate_passes(caseplan_path: str, *, timeout: int = 60) -> None:
    cmd = ["uip", "maestro", "case", "validate", caseplan_path, "--output", "json"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        _fail(
            f"uip maestro case validate exit {r.returncode}\n"
            f"stdout: {r.stdout}\nstderr: {r.stderr}"
        )


def assert_task_type_present(task_type: str, *, caseplan_path: str | None = None) -> dict:
    plan = read_caseplan(caseplan_path)
    matches = find_tasks_of_type(plan, task_type)
    if not matches:
        types_seen = sorted({t.get("type", "?") for t in iter_tasks(plan)})
        _fail(
            f"No task with type={task_type!r} found in caseplan. "
            f"Task types seen: {types_seen}"
        )
    return matches[0]


def task_is_skeleton(task: dict) -> bool:
    data = task.get("data") or {}
    if not data:
        return True
    context = data.get("context") or {}
    return not context.get("taskTypeId")


def _stringify(v: Any) -> str:
    return json.dumps(v, default=str)


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")
