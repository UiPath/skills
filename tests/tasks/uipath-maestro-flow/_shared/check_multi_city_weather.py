#!/usr/bin/env python3
"""Multi-city weather: loop + weather-API node + script all ran, and the flow's
declared output holds all 3 cities with verdicts.

The result is graded on the flow's ``out`` variable, not on the whole debug
payload. The payload carries every step's outputs and every global, so the
city names are in it whether or not the flow returned anything: each
iteration's script output is ``{city, temperature, verdict}``, and the
``cities`` list the loop walks is an ``inout`` global, which
``assert_outputs_contain`` does not treat as an input echo. On the platform's
V2 engine a loop body's ``{ updates }`` to an outer variable is dropped
(UiPath/builder-sdk#1941), so the returned array can be empty while the
whole-payload match still passes.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_any_node_type,
    assert_flow_has_node_type,
    assert_loop_body_nodes_parented,
    assert_named_output_contains,
    find_flow_file,
    run_debug,
)

CITIES = ["Seattle", "Phoenix", "New York"]
VERDICTS = ["warm", "cold"]


def read_flow_out_vars(flow_path: str) -> list[str]:
    """The ids of the flow's declared ``out`` globals."""
    with open(flow_path) as f:
        flow = json.load(f)
    variables = flow.get("variables") or flow.get("workflow", {}).get("variables") or {}
    return [v["id"] for v in (variables.get("globals") or []) if v.get("direction") == "out" and v.get("id")]


def assert_result_output(payload: dict, out_vars: list[str]) -> str:
    """Require one declared output to hold every city and at least one verdict.

    Returns the name of the output that does. With several outputs the first
    that passes wins; when none does, the last one's failure is reported.
    """
    if not out_vars:
        sys.exit("FAIL: No output variable (direction:'out') found in the flow — nothing returns the results.")
    for i, name in enumerate(out_vars):
        try:
            assert_named_output_contains(payload, name, CITIES)
            assert_named_output_contains(payload, name, VERDICTS, require_all=False)
            return name
        except SystemExit:
            if i == len(out_vars) - 1:
                raise
    raise AssertionError("unreachable")


def main():
    # Must have a loop — proves iteration. This stays a HARD requirement.
    assert_flow_has_node_type(["core.logic.loop"])
    # The per-city API call may be a raw HTTP node OR the curated Open-Meteo
    # connector (the skill's node-selection ladder may pick either) — proves
    # the loop actually fetches weather rather than hardcoding values.
    assert_flow_has_any_node_type(["core.action.http", "custom-codereval-openmeteoapis"])
    assert_loop_body_nodes_parented()

    out_vars = read_flow_out_vars(find_flow_file())
    payload = run_debug(timeout=240)

    # All 3 cities and a verdict must be in what the flow RETURNS — proves the
    # loop iterated 3 times, the script classified each city, and the results
    # reached the output.
    name = assert_result_output(payload, out_vars)
    print(f"OK: loop + weather-API node + script all executed; output {name!r} has all 3 cities with verdicts")


if __name__ == "__main__":
    main()
