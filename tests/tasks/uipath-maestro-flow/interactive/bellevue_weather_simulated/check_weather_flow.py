#!/usr/bin/env python3
"""BellevueWeather (simulated): a weather-API node executes and output contains one branch message.

Name-agnostic runtime checker for the simulated variant. Identical assertions to
the retired non-simulated original (multi_node/bellevue_weather/check_weather_flow.py):
it locates the Flow project via `_shared.flow_check` (globs `**/project.uiproj`,
not a fixed name), runs `uip maestro flow debug`, and asserts a real weather-API
node ran and a verdict landed in the OUTPUT — not merely that both strings appear
in the .flow JSON (which a hardcoded flow would pass)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_any_node_type,
    assert_outputs_contain,
    run_debug,
)


def main():
    assert_flow_has_any_node_type(["core.action.http", "custom-codereval-openmeteoapis"])
    payload = run_debug(timeout=240)
    assert_outputs_contain(payload, ["nice day", "bring a jacket"], require_all=False)
    print("OK: weather-API node present; output contains a weather branch message")


if __name__ == "__main__":
    main()
