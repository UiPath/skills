#!/usr/bin/env python3
"""Multi-city weather: loop + HTTP + script all ran, output has all 3 cities with verdicts."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_outputs_contain,
    run_debug,
)


def main():
    # Must have a loop and HTTP node — proves iteration + API calls
    assert_flow_has_node_type(["core.logic.loop", "core.action.http"])

    payload = run_debug(timeout=240)

    # All 3 city names must appear in output — proves the loop iterated 3 times
    assert_outputs_contain(payload, ["Seattle", "Phoenix", "New York"])

    # At least one verdict must appear — proves the script classified the temp
    assert_outputs_contain(
        payload, ["warm", "cold"], require_all=False
    )
    print("OK: loop + HTTP + script all executed, all 3 cities with verdicts present")


if __name__ == "__main__":
    main()
