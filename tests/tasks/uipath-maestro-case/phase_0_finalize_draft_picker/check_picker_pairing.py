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

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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

    # The pairing: an upstream PRIMARY stage must expose this lane via a wait-for-user exit.
    # A secondary or exception lane exposing another lane is not an upstream producer.
    exposing = []
    for label, block in blocks.items():
        if label.lower() == LANE.lower() or stage_kind(block) != "primary":
            continue
        for row in exit_rows(block):
            if "wait-for-user" in column(row, "exit type").lower():
                exposing.append(label)
    if not exposing:
        fail(
            f"{LANE!r} is entered by user-selected-stage but no upstream stage carries a "
            "wait-for-user exit, so nothing exposes the lane to the picker and it is unreachable "
            "(sdd-generation-rules § Logical integrity 5, § Finalization 12a)"
        )

    print(f"OK: {LANE} user-selected-stage entry is paired with a wait-for-user exit on {exposing}")


if __name__ == "__main__":
    main()
