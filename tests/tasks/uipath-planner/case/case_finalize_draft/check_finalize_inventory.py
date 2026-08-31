#!/usr/bin/env python3
"""Ensure CandidateInterview finalization retains the complete design contract."""

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


def task_block(text: str, name: str) -> str:
    match = re.search(
        rf"(?ims)^#####\s+Task\s+[^:\n]+:\s*{re.escape(name)}(?:\s+\([^\n]*\))?\s*$"
        rf"(?P<body>.*?)(?=^#####\s+Task\s+|^###\s+|\Z)",
        text,
    )
    if not match:
        sys.exit(f"FAIL: finalized SDD has no task detail block for {name!r}")
    return match.group(0)


def main() -> None:
    draft = Path("sdd.draft.md").read_text(encoding="utf-8")
    final = Path("sdd.md").read_text(encoding="utf-8")
    expected = stage_task_inventory(draft)
    actual = stage_task_inventory(final)
    if not expected:
        sys.exit("FAIL: draft contains no stage/task inventory")
    if expected != actual:
        sys.exit(
            "FAIL: finalized stage/task inventory differs from draft "
            f"(draft={len(expected)}, final={len(actual)})"
        )

    decision = task_block(final, "Technical Screen Decision")
    required = ("roleDepartment", "roleLevel", "onsiteRecommended", "=js:")
    missing = [value for value in required if value not in decision]
    if missing:
        sys.exit(
            "FAIL: Technical Screen Decision lost the Engineering L4+ policy "
            f"contract: missing {', '.join(missing)}"
        )

    print(
        "OK: finalized SDD preserves "
        f"{len(expected)} stage/task assignments and the Engineering L4+ policy"
    )


if __name__ == "__main__":
    main()
