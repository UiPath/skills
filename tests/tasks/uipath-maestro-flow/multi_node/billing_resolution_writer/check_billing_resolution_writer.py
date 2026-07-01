#!/usr/bin/env python3
"""Inline-agent writer flow.

Tests a Maestro Flow whose single work node is an inline low-code agent
(`uipath.agent.autonomous`). Two layers:
  1. Structural: the flow contains an inline autonomous agent node (anti-hardcode
     — a Script node cannot stand in for the agent).
  2. Behavior: `flow debug` completes and the drafted email — landed in the
     mapped `emailBody` output — cites the invoice and the approved credit.

The behavior grade scopes to the `emailBody` output global, NOT the whole debug
payload. Matching the whole payload is a false pass: the trigger echoes the
`invoiceNumber` input back into the outputs, so the invoice string is "present"
even when the agent refuses to draft OR the End node never maps the agent's
result into `emailBody`. Scoping to `emailBody` catches both.
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
    assert_named_output_contains,
    assert_output_nonempty,
    run_debug,
)

INVOICE = "MCS-2026-04872"
INPUTS = {"customerName": "Northwind Traders", "invoiceNumber": INVOICE, "creditAmount": 1610}


def main():
    assert_flow_has_node_type(["uipath.agent.autonomous"])
    print("OK: flow contains an inline uipath.agent.autonomous node")

    payload = run_debug(inputs=INPUTS, timeout=540)
    # Subject must be mapped + non-empty.
    assert_output_nonempty(payload, "emailSubject")
    # Body must be mapped, cite the invoice, and state the approved credit.
    assert_named_output_contains(payload, "emailBody", INVOICE)
    assert_named_output_contains(payload, "emailBody", ["1610", "1,610"], require_all=False)
    print(f"OK: emailBody drafted, cites invoice {INVOICE} and the approved credit")


if __name__ == "__main__":
    main()
