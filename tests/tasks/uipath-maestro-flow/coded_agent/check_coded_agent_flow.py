#!/usr/bin/env python3
"""CountLettersCoded: a coded-agent node executes; output holds the count (3)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_output_value,
    run_debug,
)


def main():
    assert_flow_has_node_type(["uipath.core.agent"])
    payload = run_debug(timeout=240)
    # 3 r's in 'counterrevolutionary'.
    assert_output_value(payload, 3)
    print("OK: Coded-agent node present; output contains 3")


if __name__ == "__main__":
    main()
