#!/usr/bin/env python3
"""Grades batch-ai composed with ai-decision-human-review: inside one loop body,
an agent decides, a confidence gate auto-applies, a person reviews the rest, both
routes reach one apply step, and a failure or rejection moves on to the next item
instead of ending the run."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _shared.flow_graph import CONTINUE_PORT, CONTROL, DECISION, LOOP, SWITCH, fail, load_graph  # noqa: E402

ERROR_PORT = "error"


def moves_on(g, edge, loop: str) -> bool:
    return (edge["targetNodeId"] == loop and edge.get("targetPort") == CONTINUE_PORT) or g.continues(edge["targetNodeId"], loop)


def only_control_between(g, source: str, target: str, blocked) -> bool:
    """Every step between ``source`` and ``target`` is routing, so no route has an
    apply step of its own before they meet."""
    between = {n for n in g.reachable(source, blocked) if g.reaches(n, target, blocked)} - {target}
    return all(g.type_of(n).startswith(CONTROL) for n in between)


def main() -> None:
    g = load_graph()

    for loop in g.ids(LOOP):
        body = {n for n in g.nodes if g.inside(n, loop)}
        agents = [a for a in g.agents() if a in body]
        people = [p for p in g.hitl() if p in body]
        gated = [
            (a, n) for a in agents for n in g.ids(DECISION, SWITCH)
            if n in body and g.thresholds(n, a) and g.routes_low(n, people, a)
        ]
        if not (gated and people):
            continue

        agent = gated[0][0]
        gates = [n for a, n in gated if a == agent]
        errors = g.edges_from(agent, ERROR_PORT)
        if not errors or not all(moves_on(g, e, loop) for e in errors):
            fail(f"{agent}'s failure is unwired, leaves the loop, or ends the run: one failed item stops the batch")

        shared = [
            n for n in body - set(people) - set(gates) - {agent}
            if not g.type_of(n).startswith(CONTROL)
            and any(g.reaches(gate, n, blocked=people) and only_control_between(g, gate, n, people) for gate in gates)
            and any(g.reaches(p, n) and only_control_between(g, p, n, ()) for p in people)
        ]
        if not shared:
            fail("no single step in the loop body is reached by both the confident route and the reviewer's approval")

        for p in people:
            outcomes = [e for e in g.edges_from(p) if e["sourcePort"] != ERROR_PORT]
            if not outcomes or not all(moves_on(g, e, loop) for e in outcomes):
                fail(f"a review outcome of {p} leaves the loop or ends the run instead of moving on to the next item")
            skips = [
                e for e in outcomes
                if (e["targetNodeId"] == loop and e.get("targetPort") == CONTINUE_PORT)
                or (e["targetNodeId"] not in shared and not set(shared) & g.reachable(e["targetNodeId"]))
            ]
            if not skips:
                fail(f"every review outcome of {p} reaches {shared[0]}: a rejected item is still applied")

        print(f"PASS: loop {loop} decides with {agent}, reviews with {people[0]}, applies at {shared[0]}")
        return

    fail("no loop body holds an agent, a confidence gate and a human task together")


if __name__ == "__main__":
    main()
