#!/usr/bin/env python3
"""Grades the `user-selected-stage` <-> `wait-for-user` pairing in a finalized sdd.md.

The staged draft describes a lane a Compliance Officer launches by hand from the
stage picker — the one trigger for which `user-selected-stage` IS the right rule
— but authors it with no upstream `wait-for-user` exit, so nothing exposes the
lane to the picker and the lane is unreachable. Finalization (sdd-generation
rules § Logical integrity 5, § Finalization 12a) must supply the missing half of
the pair.

Grades authored condition tables only, never Design Rationale prose.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-planner")
    if os.environ.get("SKILLS_REPO_PATH")
    else str(Path(__file__).resolve().parents[2])
)
sys.path.insert(0, _shared_root)

from _shared.entry_rule_check import (  # noqa: E402
    column,
    entry_rows,
    exit_rows,
    fail,
    find_stage,
    read_sdd,
    rule_type,
    stage_blocks,
    stage_kind,
)

LANE = "Compliance Hold"
PRIMARY_STAGES = ("Document Collection", "Vendor Approval")


def main() -> None:
    blocks = stage_blocks(read_sdd())
    lane = find_stage(blocks, LANE)

    lane_entries = entry_rows(lane)
    if not lane_entries:
        fail(f"{LANE!r} has no Stage Entry Conditions table")

    picker_rows = [row for row in lane_entries if rule_type(row) == "user-selected-stage"]
    if not picker_rows:
        found = sorted({rule_type(row) for row in lane_entries})
        fail(
            f"{LANE!r} is launched from the stage picker by a person, so its entry rule must be "
            f"user-selected-stage; authored rules were {found}"
        )

    for row in picker_rows:
        interrupting = column(row, "interrupting").lower()
        if not interrupting.startswith("y"):
            fail(f"{LANE!r} user-selected-stage entry row is not Interrupting: Yes (got {interrupting!r})")

    # The requirement says the person may pull *any active case* into the lane,
    # so every named primary stage must expose the picker with the canonical
    # completing exit. Exposure from one phase cannot cover another active phase.
    exposing = []
    for label in PRIMARY_STAGES:
        block = find_stage(blocks, label)
        if stage_kind(block) != "primary":
            fail(f"{label!r} must remain a primary stage")
        completion_rows = [
            row
            for row in exit_rows(block)
            if rule_type(row) == "required-tasks-completed"
        ]
        if len(completion_rows) != 1:
            fail(
                f"{label!r} must have exactly one required-tasks-completed completion exit; "
                "replace the existing row instead of adding a duplicate"
            )
        row = completion_rows[0]
        if (
            "wait-for-user" not in column(row, "exit type").lower()
            or not column(row, "marks stage complete").lower().startswith("y")
        ):
            fail(
                f"{label!r} must expose {LANE!r} with a required-tasks-completed / "
                "wait-for-user / Marks Stage Complete: Yes exit"
            )
        exposing.append(label)

    print(f"OK: {LANE} user-selected-stage entry is exposed from every primary stage: {exposing}")


if __name__ == "__main__":
    main()
