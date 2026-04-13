#!/usr/bin/env python3
"""CountLettersCoded: a coded-agent node executes; output holds the count (3)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_node_types,
    assert_output_value,
    run_debug,
)


def main():
    payload = run_debug(timeout=240)
    # Coded-agent invocation node has extensionType "agent".
    assert_node_types(payload, ["agent"])
    # 3 r's in 'counterrevolutionary'.
    assert_output_value(payload, 3)
    print("OK: Agent node ran; output contains 3")


if __name__ == "__main__":
    main()
