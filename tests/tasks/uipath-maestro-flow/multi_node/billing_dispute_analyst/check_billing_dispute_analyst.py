#!/usr/bin/env python3
"""Inline-agent analyst flow (context-grounded).

Tests a Maestro Flow whose single work node is an inline low-code agent
(`uipath.agent.autonomous`) grounded on a semantic index via its `context`
handle. Three layers:
  1. Structural: the flow contains BOTH an inline autonomous agent node AND a
     `uipath.agent.resource.context.index.*` node — the agent's context handle
     must be wired to a real index (anti-hardcode).
  2. Behavior: `flow debug` completes.
  3. Output: the agent returns a real SOP-grounded determination — one that
     engaged the dispute facts, not a generic refusal. We assert the output
     references at least one grounded fact / verdict token (contracted rate,
     billed rate, or a recognized verdict) rather than pinning the exact
     determination text: the agent under test authors its own determination
     vocabulary, so a literal-string match would be brittle and unfair.
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
    assert_outputs_contain,
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
    # Beat a bare non-empty check (a soft refusal like "please provide the invoice
    # number to proceed" is itself a non-empty string and would pass): require the
    # output to engage the grounded dispute facts. OR over the contracted/billed
    # rates and a few verdict/domain tokens rather than pinning the exact
    # determination — the agent under test authors its own determination
    # vocabulary, so a literal match would be unfair. A generic refusal that never
    # reasoned over the dispute contains none of these.
    assert_outputs_contain(
        payload,
        ["290", "300", "credit", "valid", "contracted", "discrepancy", "overcharge"],
        require_all=False,
    )
    print("OK: grounded inline agent returned a real SOP-grounded determination")


if __name__ == "__main__":
    main()
