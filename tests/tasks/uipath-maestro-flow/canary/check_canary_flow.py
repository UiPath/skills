#!/usr/bin/env python3
"""Canary: fan-out/merge flow with one leg per fragile plugin type.

Hardcoded inputs in the flow file:
  - coded agent        inputString = "car"    → count = 1
  - lowcode agent      inputString = "berry"  → count = 2
  - RPA workflow       problemId  = 42        → title = "Coded Triangle Numbers"
  - API workflow       name       = "tomasz"  → age in [40, 60]
  - Slack get-channel  id         = CLYMR02GK → topic/purpose contains "700 Bellevue Way"

The point of this test is infra attribution: if finalStatus != "Completed"
the orchestrator / tenant / network is suspect; individual output checks
only fire if the flow as a whole completed, so a failure here means an
infra regression rather than a skill regression.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_output_int_in_range,
    assert_output_value,
    assert_outputs_contain,
    run_debug,
)


REQUIRED_NODE_TYPES = [
    "uipath.core.agent",           # both coded and lowcode agents share this prefix
    "uipath.core.rpa-workflow",
    "uipath.core.api-workflow",
    "uipath.connector.uipath-salesforce-slack",
]


def main():
    assert_flow_has_node_type(REQUIRED_NODE_TYPES)
    # RPA on Project Euler can take 5+ min on a cold robot; five legs in
    # parallel amplify tail latency. Match the RPA-only task's ceiling plus
    # slack for fan-out overhead.
    payload = run_debug(timeout=780)

    # Per-leg spot checks. Kept loose enough to survive harmless drift
    # (e.g. name-to-age model update) but strict enough to catch a leg
    # silently returning an empty payload.
    assert_output_value(payload, 1)                   # "car" has 1 'r' → coded agent
    assert_output_value(payload, 2)                   # "berry" has 2 'r's → lowcode agent
    assert_output_int_in_range(payload, 40, 60)       # tomasz age → API workflow
    assert_outputs_contain(payload, "coded triangle numbers")  # Project Euler 42 title → RPA
    assert_outputs_contain(payload, "700 Bellevue Way")  # Slack channel topic/purpose contains the office address

    print("OK: 5 plugin legs completed (agent, lowcode-agent, rpa, api-workflow, slack)")


if __name__ == "__main__":
    main()
