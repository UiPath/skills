#!/usr/bin/env python3
"""Add-output check: end nodes must include 'Bellevue, WA' in their output."""

import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_outputs_contain,
    run_debug,
)


def main():
    assert_flow_has_node_type(["core.action.http"])
    payload = run_debug(timeout=240)
    # Must still have a branch message
    assert_outputs_contain(payload, ["nice day", "bring a jacket"], require_all=False)
    # Must have the new location field
    assert_outputs_contain(payload, ["Bellevue, WA"])
    print("OK: output contains branch message and 'Bellevue, WA' location")


if __name__ == "__main__":
    main()
