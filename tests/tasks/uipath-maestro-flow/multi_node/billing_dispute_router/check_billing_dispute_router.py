#!/usr/bin/env python3
"""BillingDisputeRouter: the agent builds + validates only; this check runs
`uip maestro flow debug` itself for three amounts and asserts the switch routes
each to the correct outcome.

Routing rule under test (switch on `disputedAmount`):
  > 5000  -> "manager_review"
  <= 500  -> "auto_resolve"
  else    -> "standard_review"

A Switch node is required (anti-hardcode): the three cases already force real
branching (a single hardcoded output fails two of three), and the node-type
guard additionally rejects an if/else or script that sidesteps the Switch the
task targets.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_output_value,
    run_debug,
)

# (disputedAmount, disputeType, expected routingDecision)
CASES = [
    (11000, "duplicate_charge", "manager_review"),
    (300, "incorrect_amount", "auto_resolve"),
    (2500, "incorrect_rate", "standard_review"),
]


def main():
    # The routing must go through a Switch node, not an if/else chain or script.
    assert_flow_has_node_type(["core.logic.switch"])

    for amount, dispute_type, expected in CASES:
        inputs = {"disputedAmount": amount, "disputeType": dispute_type}
        print(f"[amount={amount}] debug inputs: {inputs} (expect {expected!r})")
        payload = run_debug(inputs=inputs, timeout=180)
        assert_output_value(payload, expected)
        print(f"OK: amount={amount} -> {expected!r}")

    print(f"OK: all {len(CASES)} amounts routed to the correct branch")


if __name__ == "__main__":
    main()
