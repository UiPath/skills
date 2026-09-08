#!/usr/bin/env python3
"""Grade one thing: whether the built caseplan names an action catalog.

Exits 0 only when the caseplan resolved enough real action tasks to be worth
judging AND none of them carries `data.actionCatalogName`. The resolved-task
floor is the point of the second condition: an action task whose app did not
resolve collapses to `"data": {}`, so a caseplan full of placeholders would
report "no catalog named" while proving nothing at all.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CASEPLAN = Path("SupplierOnboarding/SupplierOnboarding/caseplan.json")
MIN_RESOLVED_ACTION_TASKS = 12


def action_tasks(node: object, found: list) -> None:
    if isinstance(node, dict):
        if node.get("type") == "action" and isinstance(node.get("data"), dict) and node.get("id"):
            found.append(node)
        for value in node.values():
            action_tasks(value, found)
    elif isinstance(node, list):
        for item in node:
            action_tasks(item, found)


def main() -> int:
    if not CASEPLAN.exists():
        print(f"FAIL: {CASEPLAN} does not exist")
        return 1

    try:
        plan = json.loads(CASEPLAN.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"FAIL: {CASEPLAN} is not valid JSON: {exc}")
        return 1

    tasks: list = []
    action_tasks(plan, tasks)
    resolved = [t for t in tasks if t["data"]]
    named = [
        (t.get("id"), t.get("displayName"), t["data"]["actionCatalogName"])
        for t in tasks
        if isinstance(t["data"].get("actionCatalogName"), str)
        and t["data"]["actionCatalogName"] != ""
    ]

    print(f"action tasks: {len(tasks)}")
    print(f"resolved (non-empty data): {len(resolved)}")
    print(f"naming an action catalog: {len(named)}")
    for task_id, title, value in named:
        print(f"  {task_id} {title!r} -> {value!r}")

    if len(resolved) < MIN_RESOLVED_ACTION_TASKS:
        print(
            f"FAIL: only {len(resolved)} resolved action tasks, floor is "
            f"{MIN_RESOLVED_ACTION_TASKS}. The registry did not resolve, so the "
            "catalog result below proves nothing. Treat this replicate as void, "
            "not as a pass."
        )
        return 1

    if named:
        print(f"FAIL: {len(named)} action task(s) name an action catalog")
        return 1

    print("PASS: no action task names an action catalog")
    return 0


if __name__ == "__main__":
    sys.exit(main())
