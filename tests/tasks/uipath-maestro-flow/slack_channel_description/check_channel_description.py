#!/usr/bin/env python3
"""SlackChannelDescription: a Slack connector node executes; output contains
the Bellevue office address fragments."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_node_types,
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
    payload = run_debug(timeout=120)
    # Require a Slack connector node — prevents the agent passing by
    # hardcoding the address in a Script node.
    assert_node_types(payload, ["slack"])
    assert_outputs_contain(payload, ADDRESS_FRAGMENTS, require_all=True)
    print("OK: Slack connector ran; output contains Bellevue office address")


if __name__ == "__main__":
    main()
