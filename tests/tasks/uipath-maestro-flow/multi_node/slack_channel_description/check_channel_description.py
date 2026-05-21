#!/usr/bin/env python3
"""SlackChannelDescription: a Slack connector node executes; output contains
the Bellevue office address fragments."""

import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from _shared.flow_check import (  # noqa: E402
    assert_flow_uses_connector_target,
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
    # Require a real Slack-backed connector call. Current flows may represent
    # this either as a native uipath.connector node or as HTTP v2 with
    # bodyParameters.targetConnector = uipath-salesforce-slack.
    assert_flow_uses_connector_target("uipath-salesforce-slack")
    payload = run_debug(timeout=240)
    assert_outputs_contain(payload, ADDRESS_FRAGMENTS, require_all=True)
    print("OK: Slack connector target present; output contains Bellevue office address")


if __name__ == "__main__":
    main()
