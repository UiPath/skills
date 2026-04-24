#!/usr/bin/env python3
"""SlackChannelDescription: a Slack connector node executes; output contains
the Bellevue office address fragments."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_outputs_contain,
    run_debug,
)

ADDRESS_FRAGMENTS = [
    "700 Bellevue Way NE",
    "Suite 2000",
    "Bellevue",
    "WA 98004",
]


def main():
    # Require a Slack connector node in the flow — prevents the agent passing
    # by hardcoding the address in a Script node.
    assert_flow_has_node_type(["uipath.connector"])
    payload = run_debug(timeout=240)
    assert_outputs_contain(payload, ADDRESS_FRAGMENTS, require_all=True)
    print("OK: Connector node present; output contains Bellevue office address")


if __name__ == "__main__":
    main()
