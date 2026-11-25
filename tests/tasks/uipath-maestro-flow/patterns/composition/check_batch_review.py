#!/usr/bin/env python3
"""Grades batch-ai composed with ai-decision-human-review: inside one loop body,
an agent decides, a confidence gate auto-applies, a person reviews the rest, both
routes reach one apply step, and a failure or rejection moves on to the next item
instead of ending the run."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _shared.flow_graph import CONTINUE_PORT, CONTROL, DECISION, LOOP, SWITCH, fail, load_graph  # noqa: E402

ERROR_PORT = "error"
SCRIPT = "core.action.script"


def moves_on(g, edge, loop: str) -> bool:
    return (edge["targetNodeId"] == loop and edge.get("targetPort") == CONTINUE_PORT) or g.continues(edge["targetNodeId"], loop)


def top_level(items: str) -> list[str]:
    """``items`` split on the commas outside any brackets."""
    parts, depth, start = [], 0, 0
    for i, ch in enumerate(items):
        depth += (ch in "([{") - (ch in ")]}")
        if ch == "," and depth == 0:
            parts, start = parts + [items[start:i]], i + 1
    return [p.strip() for p in parts + [items[start:]] if p.strip()]


def passes_confidence(script: str, agent: str) -> bool:
    """``script`` may check the agent's output, then ends in its only ``return``:
    the output itself, a spread of it no later key overrides, or an object whose
    ``confidence`` is the agent's own (``const`` names, nothing assigns one)."""
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", script, flags=re.S)
    code = re.sub(r"\[\s*['\"]confidence['\"]\s*\]", ".confidence", code)
    out = f"$vars.{agent.rsplit('/', 1)[-1]}.output"
    bound = lambda value: re.findall(rf"\bconst\s+(\w+)\s*=\s*{re.escape(value)}\s*;", code)
    outputs = {out, *bound(out)}
    scores = {o + ".confidence" for o in outputs} | set(bound(out + ".confidence")) | {
        "confidence" for names, source in re.findall(r"\bconst\s*\{([^}]*)\}\s*=\s*([\w$.]+)\s*;", code)
        if source in outputs and "confidence" in top_level(names)
    }
    end = re.search(r"\breturn\s+(.*?)\s*;?\s*$", code, re.S)
    if not end or len(re.findall(r"\breturn\b", code)) != 1 or re.search(r"\.confidence\s*([-+*/]?=(?!=)|\+\+|--)", code):
        return False
    value, decides = end.group(1), False
    if value in outputs:
        return True
    for prop in top_level(value[1:-1]) if value.startswith("{") and value.endswith("}") else []:
        if prop.startswith("..."):
            decides = prop[3:].strip() in outputs
        elif re.match(r"['\"]?confidence['\"]?\s*(:|$)", prop):
            decides = prop.split(":", 1)[-1].strip() in scores
    return decides


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
        # The gate reads the agent's output, or a script downstream of the
        # agent (no human task on the way to the gate) that passes the
        # agent's confidence on unchanged.
        gated = [
            (a, n) for a in agents for n in g.ids(DECISION, SWITCH) if n in body
            for s in [a] + [
                s for s in g.reachable(a, blocked=people)
                if s in body and g.type_of(s) == SCRIPT and g.reaches(s, n, blocked=people)
                and passes_confidence(str((g.nodes[s].get("inputs") or {}).get("script", "")), a)
            ]
            if g.thresholds(n, s) and g.routes_low(n, people, s)
        ]
        if not (gated and people):
            continue

        agent = gated[0][0]
        gates = [n for a, n in gated if a == agent]
        errors = g.edges_from(agent, ERROR_PORT)
        if not errors or not all(moves_on(g, e, loop) for e in errors):
            fail(f"{agent}'s failure is unwired, leaves the loop, or ends the run: one failed item stops the batch")

        # One apply step both routes reach. A route may record something first,
        # but at least one route must reach it with nothing but routing between,
        # or each route has an apply step of its own.
        shared = [
            n for n in body - set(people) - set(gates) - {agent}
            if not g.type_of(n).startswith(CONTROL)
            and any(g.reaches(gate, n, blocked=people) for gate in gates)
            and any(g.reaches(p, n) for p in people)
            and (any(only_control_between(g, gate, n, people) for gate in gates)
                 or any(only_control_between(g, p, n, ()) for p in people))
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
