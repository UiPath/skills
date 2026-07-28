#!/usr/bin/env python3
"""Check the procurement SLA design and plan regression contract."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def read_required(path: Path) -> str:
    if not path.is_file():
        fail(f"missing {path}")
    return path.read_text(encoding="utf-8")


def has_near(text: str, left: str, right: str, distance: int = 500) -> bool:
    return re.search(
        rf"{re.escape(left)}.{{0,{distance}}}{re.escape(right)}",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    ) is not None


def task_section(plan: str, task_name: str) -> str:
    match = re.search(
        rf"(?ims)^##\s+T\d+:.*?\"{re.escape(task_name)}\".*?(?=^##\s+T\d+:|\Z)",
        plan,
    )
    if not match:
        fail(f"missing tasks.md T-entry for {task_name!r}")
    return match.group(0)


def task_lane(section: str, task_name: str) -> int:
    match = re.search(r"(?im)^-\s*lane:\s*(\d+)\s*$", section)
    if not match:
        fail(f"missing lane for sequential task {task_name!r}")
    return int(match.group(1))


def main() -> None:
    sdd = read_required(Path("sdd.md"))
    plan = read_required(Path("tasks/tasks.md"))
    combined = f"{sdd}\n{plan}"

    if combined.lower().count("sla-status-change") < 2:
        fail("phase/case breach work is not modeled with SLA stage-entry rules")

    for stage in ("SLA Escalation", "Case SLA Review", "Withdrawn"):
        if not has_near(sdd, stage, "Interrupting", 300):
            fail(f"{stage!r} is not documented as an interrupting secondary stage")

    if not has_near(sdd, "Withdrawn", "wait-for-connector", 900):
        fail("Withdrawn is not entered by the global supplier-portal event")

    sequential_tasks = ("Verify Supplier Identity", "Set Supplier Record", "Invite Supplier")
    lanes: list[int] = []
    for task in sequential_tasks:
        if not has_near(combined, task, "runs-sequentially", 700):
            fail(f"{task!r} does not preserve the explicit sequential mode")
        section = task_section(plan, task)
        if not has_near(section, "activation-mode", "sequential", 120):
            fail(f"{task!r} does not expose activation-mode: sequential")
        if not has_near(section, "entry-rule", "runs-sequentially", 120):
            fail(f"{task!r} does not expose entry-rule: runs-sequentially")
        lanes.append(task_lane(section, task))
    expected_lanes = list(range(lanes[0], lanes[0] + len(lanes))) if lanes else []
    if lanes != expected_lanes:
        fail(
            "Supplier Setup strict sequential tasks must use consecutive "
            f"single-task lane/task-set indices; got {lanes!r}, "
            f"expected {expected_lanes!r}"
        )

    if sdd.lower().count("rationale") < 4:
        fail("SDD does not preserve enough design rationale")
    if plan.lower().count("rationale") < 4:
        fail("tasks.md does not carry the SDD rationale into planning")

    print("OK: global interrupts, sequential activation, and rationale are preserved")


if __name__ == "__main__":
    main()
