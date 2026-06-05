#!/usr/bin/env python3
"""Inline-agent analyst flow (context-grounded).

Tests a Maestro Flow whose single work node is an inline low-code agent
(`uipath.agent.autonomous`) grounded on a semantic index via its `context`
handle. Three layers:
  1. Structural: the flow contains BOTH an inline autonomous agent node AND a
     `uipath.agent.resource.context.index.*` node — the agent's context handle
     must be wired to a real index (anti-hardcode).
  2. Behavior: `flow debug` completes.
  3. Output: the agent returns a non-empty determination.
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
    collect_outputs,
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
    nonempty = [v for v in collect_outputs(payload) if isinstance(v, str) and v.strip()]
    if not nonempty:
        sys.exit("FAIL: agent produced no non-empty determination/rationale output")
    print("OK: grounded inline agent returned a non-empty determination")


if __name__ == "__main__":
    main()
