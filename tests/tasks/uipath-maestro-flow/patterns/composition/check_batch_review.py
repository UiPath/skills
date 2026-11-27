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
            parts.append(items[start:i])
            start = i + 1
    parts.append(items[start:])
    return [p.strip() for p in parts if p.strip()]


WRITE = r"(?:[-+*/%&|^]|\*\*|<<|>>>?|&&|\|\||\?\?)?=(?![=>])"
# The bar of the task's "less than 80% sure goes to review": c < 0.8 or c >= 0.8
# (0.8 or 80), either operand order.
BAR = r"(?<![\w.])(?:0?\.80*|80(?:\.0*)?)(?![\w.])"


def changes(code: str, name: str) -> bool:
    """``code`` writes to ``name`` other than its ``const`` binding, or hands it to
    ``Object.assign``/``defineProperty``/``Reflect.set``."""
    rest = re.sub(rf"\bconst\s+{re.escape(name)}\s*=", "", code)
    return re.search(
        rf"(?<![\w$.]){re.escape(name)}\s*{WRITE}"
        rf"|\b(?:Object\.(?:assign|defineProperty|defineProperties)|Reflect\.set)\(\s*{re.escape(name)}(?![\w$])",
        rest,
    ) is not None


def at_80(g, gate: str, step: str) -> bool:
    """``gate`` compares ``step``'s confidence with 80%: below it is low, 80% is not."""
    score = rf"\$?{g.subject_pattern(step, gate).pattern}(?:\.output)?\.confidence"
    return re.search(rf"{score}\s*(?:<|>=)\s*{BAR}|{BAR}\s*(?:>|<=)\s*{score}", g.text(gate)) is not None


def passes_confidence(script: str, agent: str) -> bool:
    """``script`` may check the agent's output, then ends in its only ``return``:
    the output itself, a spread of it no later key overrides, or an object whose
    ``confidence`` is the agent's own (``const`` names, nothing writes to one)."""
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", script, flags=re.S)
    code = re.sub(r"\[\s*['\"]confidence['\"]\s*\]", ".confidence", code)
    out = f"$vars.{agent.rsplit('/', 1)[-1]}.output"

    def bound(value: str) -> list[str]:
        return re.findall(rf"\bconst\s+(\w+)\s*=\s*{re.escape(value)}\s*;", code)

    outputs = {out, *bound(out)}
    scores = {o + ".confidence" for o in outputs} | set(bound(out + ".confidence")) | {
        "confidence" for names, source in re.findall(r"\bconst\s*\{([^}]*)\}\s*=\s*([\w$.]+)\s*;", code)
        if source in outputs and "confidence" in top_level(names)
    }
    end = re.search(r"\breturn\s+(.*)", code.rstrip().removesuffix(";"), re.S)
    one_return = len(re.findall(r"\breturn\b", code)) == 1
    assigns = re.search(rf"\.confidence\s*({WRITE}|\+\+|--)|(\+\+|--|\bdelete)\s*[\w$.]+\.confidence\b", code)
    if not end or not one_return or assigns or any(changes(code, o) for o in outputs):
        return False
    value, decides = end.group(1).rstrip(), False
    if value in outputs:
        return True
    for prop in top_level(value[1:-1]) if value.startswith("{") and value.endswith("}") else []:
        if prop.startswith("..."):
            decides = prop[3:].strip() in outputs
        elif re.match(r"\.?['\"]?confidence['\"]?\s*(:|$)", prop):
            decides = prop.split(":", 1)[-1].strip() in scores
        elif prop.startswith(("[", ".")):  # a computed key may override the confidence
            decides = False
    return decides


def only_control_between(g, source: str, target: str, blocked) -> bool:
    """Every step between ``source`` and ``target`` is routing, so no route has an
    apply step of its own before they meet."""
    between = {n for n in g.reachable(source, blocked) if g.reaches(n, target, blocked)} - {target}
    return all(g.type_of(n).startswith(CONTROL) for n in between)


def script_of(g, node_id: str) -> str:
    return str((g.nodes[node_id].get("inputs") or {}).get("script", ""))


def main() -> None:
    g = load_graph()
    reason = "no loop body holds an agent, a confidence gate and a human task together"

    for loop in g.ids(LOOP):
        body = {n for n in g.nodes if g.inside(n, loop)}
        agents = [a for a in g.agents() if a in body]
        people = [p for p in g.hitl() if p in body]
        # The gate reads the agent's output, or a script downstream of the
        # agent (no human task on the way to the gate) that passes the
        # agent's confidence on unchanged to a gate at 80%.
        gated = [
            (a, n) for a in agents for n in g.ids(DECISION, SWITCH) if n in body
            for s in [a] + [
                s for s in g.reachable(a, blocked=people)
                if s in body and g.type_of(s) == SCRIPT and g.reaches(s, n, blocked=people)
                and passes_confidence(script_of(g, s), a) and at_80(g, n, s)
            ]
            if g.thresholds(n, s) and g.routes_low(n, people, s)
        ]
        rejected = [
            f"{n} reads {s}, which does not return {a}'s confidence unchanged" if not passes_confidence(script_of(g, s), a)
            else f"{n} reads {s}'s confidence but does not send below 80% to review and 80% on"
            for a in agents for n in g.ids(DECISION, SWITCH) if n in body
            for s in g.reachable(a, blocked=people)
            if s in body and g.type_of(s) == SCRIPT and g.thresholds(n, s)
            and not (passes_confidence(script_of(g, s), a) and at_80(g, n, s))
        ]
        if people and rejected and not gated:
            reason = rejected[0]
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

    fail(reason)


if __name__ == "__main__":
    main()
