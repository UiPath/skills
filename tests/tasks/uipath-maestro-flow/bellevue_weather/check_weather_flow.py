#!/usr/bin/env python3
"""BellevueWeather: HTTP node executes and output contains one branch message."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_outputs_contain,
    run_debug,
)


def main():
    # Require an HTTP node in the flow — blocks agents that hardcode a
    # branch message in a Script node without calling the weather API.
    assert_flow_has_node_type(["core.action.http"])
    payload = run_debug(timeout=240)
    assert_outputs_contain(
        payload, ["nice day", "bring a jacket"], require_all=False
    )
    print("OK: HTTP node present; output contains a weather branch message")


if __name__ == "__main__":
    main()
