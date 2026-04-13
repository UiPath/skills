#!/usr/bin/env python3
"""DiceRoller: a Script node runs and produces an integer in [1, 6]."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_node_types,
    assert_output_int_in_range,
    run_debug,
)


def main():
    payload = run_debug(timeout=90)
    # A Script node is required to produce the random value.
    assert_node_types(payload, ["script"])
    roll = assert_output_int_in_range(payload, 1, 6)
    print(f"OK: Script node ran; dice value = {roll}")


if __name__ == "__main__":
    main()
