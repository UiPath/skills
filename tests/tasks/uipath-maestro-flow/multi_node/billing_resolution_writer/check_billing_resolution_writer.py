#!/usr/bin/env python3
"""Inline-agent writer flow.

Tests a Maestro Flow whose single work node is an inline low-code agent
(`uipath.agent.autonomous`). Two layers:
  1. Structural: the flow contains an inline autonomous agent node (anti-hardcode
     — a Script node cannot stand in for the agent).
  2. Behavior: `flow debug` completes and the drafted email cites the invoice.
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

INVOICE = "MCS-2026-04872"
INPUTS = {"customerName": "Northwind Traders", "invoiceNumber": INVOICE, "creditAmount": 1610}


def main():
    assert_flow_has_node_type(["uipath.agent.autonomous"])
    print("OK: flow contains an inline uipath.agent.autonomous node")

    payload = run_debug(inputs=INPUTS, timeout=540)
    assert_outputs_contain(payload, INVOICE)
    print(f"OK: inline agent drafted a resolution email citing {INVOICE}")


if __name__ == "__main__":
    main()
