#!/usr/bin/env python3
"""Grades the triage near miss: an agent classifies and the flow routes by
category, with no person anywhere, because the request names none."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _shared.flow_graph import CASE_PREFIX, DECISION, END, SWITCH, fail, load_graph  # noqa: E402

CATEGORIES = 3


def main() -> None:
    g = load_graph()

    people = g.hitl()
    if people:
        fail(f"a human task the request never asked for: {sorted(people)}")

    agents = g.agents()
    if not agents:
        fail("no agent classifies the email")

    routers = [n for n in g.ids(DECISION, SWITCH) if any(g.reads(n, a) for a in agents)]
    if not routers:
        fail("nothing routes on the agent's classification")

    ends = {
        n for r in routers for e in g.edges_from(r)
        if e["sourcePort"].startswith(CASE_PREFIX) or e["sourcePort"] in ("true", "false")
        for n in g.reachable(e["targetNodeId"]) | {e["targetNodeId"]} if g.type_of(n) == END
    }
    if len(ends) < CATEGORIES:
        fail(f"{len(ends)} End node(s) reached from the routing, need one per category ({CATEGORIES})")

    print(f"PASS: {agents[0]} classifies, {routers[0]} routes to {len(ends)} ends, no human task")


if __name__ == "__main__":
    main()
