#!/usr/bin/env python3
"""Inline-agent analyst flow (context-grounded).

Tests a Maestro Flow whose single work node is an inline low-code agent
(`uipath.agent.autonomous`) grounded on a semantic index via its `context`
handle. Three layers:
  1. Structural: the flow contains BOTH an inline autonomous agent node AND a
     `uipath.agent.resource.context.index.*` node — the agent's context handle
     must be wired to a real index (anti-hardcode).
  2. Behavior: `flow debug` completes.
  3. Output: the agent returns a non-empty `determination`. We do NOT assert
     grounding: the dispute facts (290/300/contracted) are in the prompt, so a
     keyword match proves restatement, not that the SOP index was consulted.
     Grading the named output keeps the pass honest.
"""
import os
import sys

# Walk up to the skill's tests root (the dir holding the _shared package).
_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_output_nonempty,
    get_last_debug_raw,
    run_debug,
)

INPUTS = {
    "disputeDescription": "Charged 14 units at $300 but the contracted unit price is $290.",
    "invoiceNumber": "MCS-2026-04872",
}


def main():
    assert_flow_has_node_type(["uipath.agent.autonomous"])
    assert_flow_has_node_type(["uipath.agent.resource.context.index"])
    print("OK: flow wires an inline autonomous agent to a context.index node")

    payload = run_debug(inputs=INPUTS, timeout=540)
    # Persist the full debug trace in the writable task sandbox so the execution
    # (element runs, agent outputs, traceId) can be inspected after the run. The
    # task definition directory is mounted read-only in CI.
    raw = get_last_debug_raw()
    if raw:
        trace_path = os.path.abspath("last_debug_trace.json")
        with open(trace_path, "w") as fh:
            fh.write(raw)
        print(f"trace: wrote debug payload to {trace_path}")
    # Assert the flow produced a non-empty `determination` output. We do NOT
    # assert grounding here: the dispute facts (290/300/contracted) are present
    # in the prompt, so any keyword match is satisfiable by restatement and
    # would not prove the SOP index was actually consulted. Grading the named
    # output keeps this honest — the agent ran and emitted its determination.
    assert_output_nonempty(payload, "determination")
    print("OK: flow completed and the agent returned a non-empty determination")


if __name__ == "__main__":
    main()
