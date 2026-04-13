#!/usr/bin/env python3
"""BellevueWeather: HTTP node executes and output contains one branch message."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_node_types,
    assert_outputs_contain,
    run_debug,
)


def main():
    payload = run_debug(timeout=90)
    # Require an HTTP node actually fired — prevents agent from hardcoding the
    # branch message without calling the weather API.
    assert_node_types(payload, ["http"])
    # Either branch is acceptable; only one should win.
    assert_outputs_contain(
        payload, ["nice day", "bring a jacket"], require_all=False
    )
    print("OK: HTTP node ran; output contains a weather branch message")


if __name__ == "__main__":
    main()
