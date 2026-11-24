#!/usr/bin/env python3
"""Grades batch-ai composed with ai-decision-human-review: inside one loop body,
an agent decides, a confidence gate auto-applies, a person reviews the rest, both
routes reach one apply step, and a failure or rejection moves on to the next item
instead of ending the run."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _shared.flow_graph import CASE_PREFIX, CONTINUE_PORT, CONTROL, DECISION, LOOP, SWITCH, fail, load_graph  # noqa: E402

ERROR_PORT = "error"
SCRIPT = "core.action.script"


def moves_on(g, edge, loop: str) -> bool:
    return (edge["targetNodeId"] == loop and edge.get("targetPort") == CONTINUE_PORT) or g.continues(edge["targetNodeId"], loop)


# Runs a check script and the gate on a mocked agent output, in a bare vm
# context (for determinism, not a security boundary), 2 s per run.
ROUTE_JS = r"""
const vm = require("vm");
const context = vm.createContext(Object.assign(Object.create(null), { JOB: require("fs").readFileSync(0, "utf8") }));
const run = code => vm.runInContext(code, context, { timeout: 2000 });
run(`
  const console = { log() {}, info() {}, warn() {}, error() {}, debug() {} };
  const { agent, step, script, gate, fallback, fields, scores } = JSON.parse(JOB);
  // Any other value the script reads: a harmless object that reads as "".
  const anything = new Proxy({}, { get: (_, key) => key === Symbol.toPrimitive ? () => "" : anything });
  const call = (code, $vars) => new Function("$vars", "vars", "$metadata", "return (function () {" + code + "\\n})();")($vars, $vars, anything);
  globalThis.route = confidence => {
    const output = new Proxy({ ...fields, ...Object.fromEntries(scores.map(name => [name, confidence])) }, {
      get: (t, key) => key in t ? t[key] : typeof key !== "string" ? undefined : /confid/i.test(key) ? confidence : "approve",
    });
    const $vars = new Proxy({ [agent]: { output } }, { get: (t, key) => key in t ? t[key] : anything });
    $vars[step] = { output: call(script, $vars) };
    const taken = gate.find(([, expression]) => call("return (" + expression + ");", $vars));
    return taken ? taken[0] : fallback;
  };
`);
process.stdout.write(JSON.stringify([run("route(0.3)"), run("route(0.95)")]));
"""


def routes_on_confidence(g, script: str, agent: str, gate: str) -> bool:
    """Running ``script`` on the agent's output, a low confidence (0.3) takes a
    below-the-bar port of ``gate`` and a high one (0.95) does not. A script that
    throws, never returns or needs anything outside ``$vars`` fails. Fields the
    agent declares get typed placeholders; any other field reads as "approve"."""
    schema = (g.nodes[agent].get("outputs") or {}).get("output", {}).get("schema") or {}
    placeholder = {"number": 0.5, "integer": 1, "boolean": True, "array": [], "object": {}}
    fields = {
        name: (spec.get("enum") or ["approve"])[0] if spec.get("type") == "string" else placeholder.get(spec.get("type"))
        for name, spec in (schema.get("properties") or {}).items()
    }
    inputs = g.nodes[gate].get("inputs") or {}
    if g.type_of(gate) == DECISION:
        ports, fallback = [("true", inputs.get("expression", ""))], "false"
    else:
        ports, fallback = [(f"{CASE_PREFIX}{c.get('id')}", c.get("expression", "")) for c in inputs.get("cases") or []], "default"
    job = {
        "agent": agent.rsplit("/", 1)[-1], "step": script.rsplit("/", 1)[-1],
        "script": str((g.nodes[script].get("inputs") or {}).get("script", "")),
        "gate": [(port, re.sub(r"^=(js:)?", "", str(e).strip())) for port, e in ports],
        "fallback": fallback, "fields": fields,
        "scores": [k for k in fields if re.search("confid", k, re.I)] or ["confidence"],
    }
    try:
        done = subprocess.run(["node", "-e", ROUTE_JS], input=json.dumps(job), capture_output=True, text=True, timeout=15)
    except FileNotFoundError:
        fail("node is needed to run the check script between the agent and the gate")
    except subprocess.TimeoutExpired:
        return False
    if done.returncode != 0:
        return False
    low, high = json.loads(done.stdout)
    below = g.low_ports(gate, script)
    return low in below and high not in below


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
        # agent (any number of steps, no human task on the way from the agent
        # to the gate) that, when run, sends a low-confidence item to review
        # and a high-confidence one past it.
        gated = [
            (a, n) for a in agents for n in g.ids(DECISION, SWITCH) if n in body
            for s in [a] + [
                s for s in g.reachable(a, blocked=people)
                if s in body and g.type_of(s) == SCRIPT and g.reaches(s, n, blocked=people)
            ]
            if g.thresholds(n, s) and g.routes_low(n, people, s) and (s == a or routes_on_confidence(g, s, a, n))
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
