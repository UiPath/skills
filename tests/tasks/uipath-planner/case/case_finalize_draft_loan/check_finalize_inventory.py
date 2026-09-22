#!/usr/bin/env python3
"""Ensure finalization preserves the draft's ordered stage/task inventory."""

from __future__ import annotations

import re
import sys
from pathlib import Path


STAGE_HEADING = re.compile(
    r"(?im)^###\s+(?:Stage\s+\d+|Secondary\s+Stage):\s*(.+?)\s*$"
)
TASK_HEADING = re.compile(r"(?im)^#####\s+Task\s+[^:\n]+:\s*(.+?)\s*$")


def clean_name(value: str) -> str:
    return re.sub(r"\s+\(`[^`]+`\)\s*$", "", value).strip()


def inventory(text: str, pattern: re.Pattern[str]) -> list[str]:
    return [clean_name(match.group(1)) for match in pattern.finditer(text)]


def stage_task_inventory(text: str) -> list[tuple[str, str]]:
    events = [
        *((match.start(), "stage", clean_name(match.group(1))) for match in STAGE_HEADING.finditer(text)),
        *((match.start(), "task", clean_name(match.group(1))) for match in TASK_HEADING.finditer(text)),
    ]
    current_stage = None
    result = []
    for _, kind, name in sorted(events):
        if kind == "stage":
            current_stage = name
        elif current_stage is None:
            sys.exit(f"FAIL: task {name!r} appears before any stage heading")
        else:
            result.append((current_stage, name))
    return result


def require_same_order(kind: str, expected: list[object], actual: list[object]) -> None:
    if expected == actual:
        return
    mismatch = next(
        (
            index
            for index, pair in enumerate(zip(expected, actual))
            if pair[0] != pair[1]
        ),
        min(len(expected), len(actual)),
    )
    expected_item = expected[mismatch] if mismatch < len(expected) else "<end>"
    actual_item = actual[mismatch] if mismatch < len(actual) else "<end>"
    sys.exit(
        f"FAIL: finalized {kind} inventory differs at position {mismatch + 1}: "
        f"expected {expected_item!r}, got {actual_item!r} "
        f"(draft={len(expected)}, final={len(actual)})"
    )


def main() -> None:
    draft = Path("sdd.draft.md").read_text(encoding="utf-8")
    final = Path("sdd.md").read_text(encoding="utf-8")
    draft_stages = inventory(draft, STAGE_HEADING)
    draft_stage_tasks = stage_task_inventory(draft)
    if not draft_stages or not draft_stage_tasks:
        sys.exit("FAIL: draft contains no stage/task inventory")
    require_same_order("stage", draft_stages, inventory(final, STAGE_HEADING))
    require_same_order("stage/task", draft_stage_tasks, stage_task_inventory(final))
    print(
        f"OK: finalized SDD preserves {len(draft_stages)} ordered stages and "
        f"{len(draft_stage_tasks)} ordered stage/task assignments"
    )


if __name__ == "__main__":
    main()
