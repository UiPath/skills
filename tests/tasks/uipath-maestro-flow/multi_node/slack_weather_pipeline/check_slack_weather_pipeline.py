#!/usr/bin/env python3
"""Slack weather pipeline: Slack connector + HTTP + decision all ran, output has verdict."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_api_node_targeting,
    assert_flow_uses_connector_target,
    assert_outputs_contain,
    run_debug,
)


def main():
    # Must have a real Slack-backed connector call and a weather-API node —
    # proves the pipeline isn't shortcutting by hardcoding the city or skipping
    # the Slack read. The Slack call may be represented as an HTTP v2 proxy node.
    # The weather call may be a raw HTTP node OR the curated Open-Meteo
    # connector (the skill's node-selection ladder may pick either) — but it
    # must actually TARGET open-meteo: a bare core.action.http hint would be
    # satisfied by the Slack HTTP proxy node above, letting a flow with no
    # weather node at all pass the structural gate.
    assert_flow_uses_connector_target("uipath-salesforce-slack")
    assert_flow_has_api_node_targeting(["open-meteo", "openmeteoapis"])

    payload = run_debug(timeout=240)

    # Verdict proves the full chain executed: Slack → Script → HTTP → Decision → End
    assert_outputs_contain(
        payload, ["warm office today", "cold office today"], require_all=False
    )
    print("OK: Slack connector target + weather-API node + decision all executed, verdict present")


if __name__ == "__main__":
    main()
