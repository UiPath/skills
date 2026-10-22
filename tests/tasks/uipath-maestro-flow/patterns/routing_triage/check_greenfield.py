#!/usr/bin/env python3
"""Grades routing-triage: a confidence floor whose human fallback reaches the same
category handlers as the confident route, not a second set of its own."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _shared.flow_graph import CASE_PREFIX, DECISION, END, SWITCH, fail, load_graph  # noqa: E402

MIN_CATEGORIES = 3


def main() -> None:
    g = load_graph()

    people = g.hitl()
    if not people:
        fail("no human task: low-confidence items have no fallback")

    # The floor: a gate that compares the classifier's output against a bound and
    # leads to the person. A category switch whose default reaches the person is
    # not a floor.
    floors = [
        (agent, gate) for agent in g.agents() for gate in g.ids(DECISION, SWITCH)
        if g.thresholds(gate, agent) and g.reaches(agent, gate) and g.routes_low(gate, people, agent)
    ]
    if not floors:
        fail("no decision compares the classifier's confidence and sends only the low side to the person")
    classifier, floor = floors[0]

    # Shared handling: the categories the confident route ends in, without passing
    # the person, are the same Ends the person's choice reaches. A duplicated
    # dispatch path gives the person Ends of its own and this set comes back empty.
    confident = g.reachable(floor, blocked=people)
    from_person = g.reachable(people)
    # A category End is one a switch case leads to; an "unrouted" End off the
    # default is a stop condition, not a category.
    category_ends = {
        n for sw in g.ids(SWITCH) for e in g.edges_from(sw) if e["sourcePort"].startswith(CASE_PREFIX)
        for n in g.reachable(e["targetNodeId"]) | {e["targetNodeId"]} if g.type_of(n) == END
    }
    shared_ends = {n for n in confident & from_person & category_ends}
    if len(shared_ends) < MIN_CATEGORIES:
        fail(
            f"the confident route and the human fallback share {len(shared_ends)} End node(s), "
            f"need one per category ({MIN_CATEGORIES}): routing was duplicated rather than shared"
        )

    print(f"PASS: {classifier} gated by {floor}, fallback {people}, {len(shared_ends)} shared category ends")


if __name__ == "__main__":
    main()
