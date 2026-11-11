#!/usr/bin/env python3
"""Grades voice-agents handoff: a triage voice agent, a route on what that agent
returned, specialists on the same call, and one end-call they converge on."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _shared.flow_graph import DECISION, SWITCH, fail, load_graph  # noqa: E402

TRIGGER = "core.trigger.voice"
VOICE_AGENT = "uipath.agent.voice"
END_CALL = "uipath.conversational.voice.end-call"
SPECIALISTS = 2
_AGENT_CALL = re.compile(r"^\$vars\.([A-Za-z0-9_]+)\.output\.uipath__voice_call_context$")


def call_of(g, node_id: str, depth: int = 0) -> str:
    """The call a voice step joins, following an agent's own call-context output
    back to the call that agent joined."""
    expr = str((g.nodes[node_id].get("inputs") or {}).get("callContext", {}).get("expression", ""))
    match = _AGENT_CALL.match(expr)
    if match and match.group(1) in g.nodes and depth < len(g.nodes):
        return call_of(g, match.group(1), depth + 1)
    return expr


def main() -> None:
    g = load_graph()

    if not g.ids(TRIGGER):
        fail("no incoming-call trigger")

    voice = g.ids(VOICE_AGENT)
    agents = g.agents()
    # The router reads the triage agent: its session reason directly, or through
    # one agent that classifies the transcript.
    routes = [
        (t, r) for r in g.ids(DECISION, SWITCH) for t in voice
        if g.reaches(t, r) and (g.reads(r, t) or any(g.reads(r, a) and g.reads(a, t) for a in agents))
    ]
    if not routes:
        fail("no decision or switch routes on what a voice agent returned")
    triage, router = routes[0]

    specialists = [a for a in voice if a != triage and g.reaches(router, a)]
    if len(specialists) < SPECIALISTS:
        fail(f"{router} hands the call to {len(specialists)} voice agent(s), need at least {SPECIALISTS}")

    calls = {call_of(g, a) for a in [triage, *specialists]}
    if len(calls) != 1 or not next(iter(calls)):
        fail(f"the voice agents do not share one call: {sorted(calls)}")

    if not any(all(g.reaches(s, e) for s in specialists) for e in g.ids(END_CALL)):
        fail("the specialists do not converge on an end-call")

    print(f"PASS: {triage} routes via {router} to {len(specialists)} specialists on one call")


if __name__ == "__main__":
    main()
