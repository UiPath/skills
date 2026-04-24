#!/usr/bin/env python3
"""Decision: verify a Decision node routes temperature to 'warm' or 'cool'."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_outputs_contain,
    find_project_dir,
    read_flow_input_vars,
    run_debug,
)


def main():
    assert_flow_has_node_type(["core.logic.decision"])

    project_dir = find_project_dir()
    in_vars = read_flow_input_vars(project_dir)
    if not in_vars:
        sys.exit("FAIL: No input variable found for temperature")

    # Temperature 90 (> 75) -> "warm"
    payload = run_debug(inputs={in_vars[0]: 90})
    assert_outputs_contain(payload, "warm")

    # Temperature 50 (<= 75) -> "cool"
    payload = run_debug(inputs={in_vars[0]: 50})
    assert_outputs_contain(payload, "cool")

    print("OK: Decision node present; warm/cool branches verified")


if __name__ == "__main__":
    main()
