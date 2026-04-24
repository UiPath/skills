#!/usr/bin/env python3
"""DiceRoller: a Script node runs and produces an integer in [1, 6]."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_output_int_in_range,
    run_debug,
)


def main():
    assert_flow_has_node_type(["core.action.script"])
    payload = run_debug(timeout=240)
    roll = assert_output_int_in_range(payload, 1, 6)
    print(f"OK: Script node present; dice value = {roll}")


if __name__ == "__main__":
    main()
