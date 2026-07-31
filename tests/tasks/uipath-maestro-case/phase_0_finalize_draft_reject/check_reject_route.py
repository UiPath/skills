#!/usr/bin/env python3
"""Grades deterministic rejection routing in a finalized sdd.md.

The staged draft authors the Application Rejected lane as `user-selected-stage`
while its Requirements say rejection follows automatically from the Reviewer
Decision. `user-selected-stage` is the picker rule, not a deterministic route
(sdd-generation-rules § Logical integrity 5, § Finalization 12a), so
finalization must re-key the lane on the decision fact and add the origin's
gated diverting exit plus a mutually-exclusive completion gate.

Grades authored condition tables only. The skill *requires* Design Rationale
that names the anti-pattern it avoided, so rationale prose is never read.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _shared.entry_rule_check import (  # noqa: E402
    column,
    entry_rows,
    exit_rows,
    fail,
    find_stage,
    guard,
    is_empty,
    read_sdd,
    rule_type,
    stage_blocks,
    when,
)

LANE = "Application Rejected"
ORIGIN = "Eligibility Review"
DECISION_VAR = "reviewdecision"
DECISION_VALUE = "reject"

DECISION_KEYED = {"selected-stage-completed", "selected-stage-exited"}


def names_decision(cell: str) -> bool:
    """True when the cell gates on the reject value of the decision variable."""
    flat = re.sub(r"[^a-z0-9]", "", cell.lower())
    return DECISION_VAR in flat and DECISION_VALUE in flat


def marks_complete(row: dict[str, str]) -> str:
    return column(row, "marks stage complete", "marks complete").strip().lower()


def main() -> None:
    blocks = stage_blocks(read_sdd())
    lane = find_stage(blocks, LANE)
    origin = find_stage(blocks, ORIGIN)

    lane_entries = entry_rows(lane)
    if not lane_entries:
        fail(f"{LANE!r} has no Stage Entry Conditions table")

    picker = [row for row in lane_entries if rule_type(row) == "user-selected-stage"]
    if picker:
        fail(
            f"{LANE!r} is entered by user-selected-stage, but rejection is deterministic from the "
            "Reviewer Decision — a picker rule cannot carry a decision route "
            "(sdd-generation-rules § Logical integrity 5)"
        )

    keyed = [
        row
        for row in lane_entries
        if rule_type(row) in DECISION_KEYED
        and ORIGIN.lower() in when(row).lower()
        and names_decision(guard(row))
    ]
    if not keyed:
        authored = [(when(row), guard(row)) for row in lane_entries]
        fail(
            f"{LANE!r} has no entry rule keyed on the decision: expected "
            f'selected-stage-completed/exited("{ORIGIN}") with an IF on reviewDecision == "Reject"; '
            f"authored rows were {authored}"
        )

    for row in keyed:
        if not column(row, "interrupting").lower().startswith("y"):
            fail(f"{LANE!r} decision-keyed entry row is not Interrupting: Yes")

    origin_exits = exit_rows(origin)
    if not origin_exits:
        fail(f"{ORIGIN!r} has no Stage Exit Conditions table")

    diverting = [
        row
        for row in origin_exits
        if marks_complete(row).startswith("n") and names_decision(guard(row))
    ]
    if not diverting:
        authored = [(when(row), guard(row), marks_complete(row)) for row in origin_exits]
        fail(
            f"{ORIGIN!r} has no gated diverting exit for the reject route (Marks Stage Complete: No "
            'with an IF on reviewDecision == "Reject"). Without it the decision path dual-fires or '
            f"deadlocks; authored exits were {authored}"
        )

    completion = [row for row in origin_exits if marks_complete(row).startswith("y")]
    if not completion:
        fail(f"{ORIGIN!r} has no completion exit (Marks Stage Complete: Yes)")
    ungated = [row for row in completion if is_empty(guard(row)) or DECISION_VAR not in re.sub(r"[^a-z0-9]", "", guard(row).lower())]
    if ungated:
        fail(
            f"{ORIGIN!r} completion exit is not gated on reviewDecision, so it is not mutually "
            f"exclusive with the diverting exit and both fire: {[guard(row) for row in ungated]}"
        )

    print(f"OK: {LANE} is decision-keyed and {ORIGIN} diverts and completes mutually exclusively")


if __name__ == "__main__":
    main()
