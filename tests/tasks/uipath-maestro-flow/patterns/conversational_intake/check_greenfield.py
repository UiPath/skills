#!/usr/bin/env python3
"""Grades conversational-intake: a turn loop through wait-for-message and a
conversational agent, an exit from it, and a report back in the same
conversation after the exit. The loop is a back-edge (as the canvas draws it)
or a do-while container."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _shared.flow_graph import DECISION, DO_WHILE, SWITCH, fail, load_graph  # noqa: E402

TRIGGER = "core.trigger.conversation"
WAIT = "uipath.conversational.wait-for-message"
CHAT_AGENT = "uipath.agent.conversational"
SEND = "uipath.conversational.send-message"


def turn_loops(g):
    """(loop nodes, exit edges) for every turn loop in the flow."""
    for wait in g.ids(WAIT):
        if g.on_cycle(wait):
            nodes = {n for n in g.reachable(wait) if g.reaches(n, wait)} | {wait}
            exits = [
                e for gate in nodes if g.type_of(gate) in (DECISION, SWITCH)
                for e in g.edges_from(gate) if e["targetNodeId"] not in nodes
            ]
            yield nodes, exits
        for container in g.ids(DO_WHILE):
            if g.inside(wait, container):
                nodes = {n for n in g.nodes if g.inside(n, container)}
                yield nodes, [e for e in g.edges_from(container) if not g.inside(e["targetNodeId"], container)]


def main() -> None:
    g = load_graph()

    if not g.ids(TRIGGER):
        fail("no conversation trigger: the flow is not started by a chat")

    loops = [(nodes, exits) for nodes, exits in turn_loops(g) if any(g.type_of(n) == CHAT_AGENT for n in nodes)]
    if not loops:
        fail("no turn loop through wait-for-message and a conversational agent: the flow answers once")

    for nodes, exits in loops:
        if not exits:
            continue
        starts = {e["targetNodeId"] for e in exits}
        after = g.reachable(starts, blocked=nodes) | starts
        if any(g.type_of(n) == SEND for n in after):
            print(f"PASS: turn loop of {len(nodes)} nodes, {len(exits)} exit(s), report sent after the exit")
            return
        fail("nothing after the loop exit sends a message back to the conversation")

    fail("nothing leaves the turn loop: every conversation suspends forever")


if __name__ == "__main__":
    main()
