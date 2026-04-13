#!/usr/bin/env python3
"""ProjectEulerTitle: an RPA-workflow node executes; output holds the title."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_node_types,
    assert_outputs_contain,
    run_debug,
)


def main():
    payload = run_debug(timeout=240)
    # RPA workflow invocation node has extensionType "process".
    assert_node_types(payload, ["process"])
    assert_outputs_contain(payload, "prime square remainders")
    print("OK: RPA node ran; output contains 'prime square remainders'")


if __name__ == "__main__":
    main()
