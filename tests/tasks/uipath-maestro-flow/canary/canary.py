#!/usr/bin/env python3
"""Canary: standalone infra-health check for the Maestro Flow debug path.

Fans out to one node per fragile plugin (coded agent, lowcode agent, RPA,
API workflow, Slack), merges with a parallel gateway, and asserts all legs
complete. No coder_eval, no agent — just ``uip flow debug``.

Usage:
    python3 canary.py

Exit code 0 on healthy infra, non-zero (with ``FAIL:`` prefix on stderr)
otherwise.

Hardcoded inputs in ``Canary/Canary.flow``:
  - coded agent        inputString = "car"    → count = 1
  - lowcode agent      inputString = "berry"  → count = 2
  - RPA workflow       problemId  = 42        → title = "Coded Triangle Numbers"
  - API workflow       name       = "tomasz"  → age in [40, 60]
  - Slack get-channel  id         = CLYMR02GK → topic/purpose contains "700 Bellevue Way"
"""

import os
import sys

# Reuse the shared flow-debug helpers. _shared/ lives one directory up:
# tests/tasks/uipath-maestro-flow/_shared/flow_check.py
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_output_int_in_range,
    assert_output_value,
    assert_outputs_contain,
    run_debug,
)

REQUIRED_NODE_TYPES = [
    "uipath.core.agent",
    "uipath.core.rpa-workflow",
    "uipath.core.api-workflow",
    "uipath.connector.uipath-salesforce-slack",
]


def main():
    # run_debug globs project.uiproj from cwd; anchor to this file so the
    # script works from any invocation cwd.
    os.chdir(_HERE)

    assert_flow_has_node_type(REQUIRED_NODE_TYPES)
    # RPA on Project Euler can take 5+ min on a cold robot; five legs in
    # parallel amplify tail latency.
    payload = run_debug(timeout=780)

    assert_output_value(payload, 1)                            # coded agent
    assert_output_value(payload, 2)                            # lowcode agent
    assert_output_int_in_range(payload, 40, 60)                # API workflow
    assert_outputs_contain(payload, "coded triangle numbers")  # RPA
    assert_outputs_contain(payload, "700 Bellevue Way")        # Slack

    print("OK: 5 plugin legs completed (agent, lowcode-agent, rpa, api-workflow, slack)")


if __name__ == "__main__":
    main()
