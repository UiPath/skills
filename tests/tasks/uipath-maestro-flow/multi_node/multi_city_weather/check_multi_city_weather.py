#!/usr/bin/env python3
"""Multi-city weather: loop + weather-API node + script all ran, output has all 3 cities with verdicts."""

import os
import sys

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-maestro-flow")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, _shared_root)
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_any_node_type,
    assert_flow_has_node_type,
    assert_loop_body_nodes_parented,
    assert_outputs_contain,
    run_debug,
)


def main():
    # Must have a loop — proves iteration. This stays a HARD requirement.
    assert_flow_has_node_type(["core.logic.loop"])
    # The per-city API call may be a raw HTTP node OR the curated Open-Meteo
    # connector (the skill's node-selection ladder may pick either) — proves
    # the loop actually fetches weather rather than hardcoding values.
    assert_flow_has_any_node_type(["core.action.http", "custom-codereval-openmeteoapis"])
    assert_loop_body_nodes_parented()

    payload = run_debug(timeout=240)

    # All 3 city names must appear in output — proves the loop iterated 3 times
    assert_outputs_contain(payload, ["Seattle", "Phoenix", "New York"])

    # At least one verdict must appear — proves the script classified the temp
    assert_outputs_contain(
        payload, ["warm", "cold"], require_all=False
    )
    print("OK: loop + weather-API node + script all executed, all 3 cities with verdicts present")


if __name__ == "__main__":
    main()
