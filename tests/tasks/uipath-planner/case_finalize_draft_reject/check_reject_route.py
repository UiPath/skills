#!/usr/bin/env python3
"""Grades deterministic rejection routing in a finalized sdd.md.

The staged draft authors the Application Rejected lane as `user-selected-stage`
while its Requirements say rejection follows automatically from the Reviewer
Decision. `user-selected-stage` is the picker rule, not a deterministic route
(references/case/review.md — logical-integrity check 5, entry-producer check), so
finalization must re-key the lane on the decision fact and add the origin's
gated diverting exit plus a mutually-exclusive completion gate.

Grades authored condition tables only. The skill *requires* Design Rationale
that names the anti-pattern it avoided, so rationale prose is never read.
"""

from __future__ import annotations

import argparse
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


def references_decision(cell: str) -> bool:
    return DECISION_VAR in re.sub(r"[^a-z0-9]", "", cell.lower())


def positive_reject(cell: str) -> bool:
    """True only for the affirmative reject guard.

    The negated form `!== "Reject"` names both tokens too, so a token test alone accepts
    the exact inverse of the route it is supposed to require.
    """
    flat = re.sub(r"[^a-z0-9]", "", cell.lower())
    return DECISION_VAR in flat and DECISION_VALUE in flat and "!=" not in cell


def marks_complete(row: dict[str, str]) -> str:
    return column(row, "marks stage complete", "marks complete").strip().lower()


def main() -> None:
    # `lane` grades this PR's delta: the route is keyed on the decision fact, not the picker.
    # `origin` grades rule 5's older diverting-exit clause, which predates #2393 — the task
    # runs it advisory so a pre-existing gap cannot read as a regression in this PR.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=("lane", "origin", "all"), default="all")
    scope = parser.parse_args().scope

    blocks = stage_blocks(read_sdd())
    lane = find_stage(blocks, LANE)
    origin = find_stage(blocks, ORIGIN)

    if scope in {"lane", "all"}:
        lane_entries = entry_rows(lane)
        if not lane_entries:
            fail(f"{LANE!r} has no Stage Entry Conditions table")

        picker = [row for row in lane_entries if rule_type(row) == "user-selected-stage"]
        if picker:
            fail(
                f"{LANE!r} is entered by user-selected-stage, but rejection is deterministic from "
                "the Reviewer Decision — a picker rule cannot carry a decision route "
                "(references/case/review.md — logical-integrity check 5)"
            )

        keyed = [
            row
            for row in lane_entries
            if rule_type(row) in DECISION_KEYED
            and ORIGIN.lower() in when(row).lower()
            and positive_reject(guard(row))
        ]
        if not keyed:
            authored = [(when(row), guard(row)) for row in lane_entries]
            fail(
                f"{LANE!r} has no entry rule keyed on the decision: expected "
                f'selected-stage-completed/exited("{ORIGIN}") with an IF on reviewDecision == '
                f'"Reject"; authored rows were {authored}'
            )

        for row in keyed:
            if not column(row, "interrupting").lower().startswith("y"):
                fail(f"{LANE!r} decision-keyed entry row is not Interrupting: Yes")

        if scope == "lane":
            print(f"OK: {LANE} is entered from the decision fact, not the stage picker")
            return

    origin_exits = exit_rows(origin)
    if not origin_exits:
        fail(f"{ORIGIN!r} has no Stage Exit Conditions table")

    diverting = [
        row
        for row in origin_exits
        if marks_complete(row).startswith("n") and positive_reject(guard(row))
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
    # Mutually exclusive means the completion gate is the *complement*: it must reference the
    # decision and must not repeat the affirmative reject guard the diverting exit carries.
    ungated = [
        row
        for row in completion
        if is_empty(guard(row))
        or not references_decision(guard(row))
        or positive_reject(guard(row))
    ]
    if ungated:
        fail(
            f"{ORIGIN!r} completion exit is not the complement of the diverting exit, so both fire "
            f"on a Reject: {[guard(row) or '—' for row in ungated]}"
        )

    print(f"OK: {LANE} is decision-keyed and {ORIGIN} diverts and completes mutually exclusively")


if __name__ == "__main__":
    main()
