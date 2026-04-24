#!/usr/bin/env python3
"""Calculator: inject inputs (17, 23) and assert a Script node produces 391."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_output_value,
    find_project_dir,
    read_flow_input_vars,
    run_debug,
)

INPUT_A = 17
INPUT_B = 23
EXPECTED = INPUT_A * INPUT_B  # 391


def main():
    # A Script node must be present — prevents hardcoding 391 as a literal.
    assert_flow_has_node_type(["core.action.script"])

    project_dir = find_project_dir()
    in_vars = read_flow_input_vars(project_dir)
    if len(in_vars) < 2:
        sys.exit(f"FAIL: Expected 2+ input variables, found {len(in_vars)}")

    inputs = {in_vars[0]: INPUT_A, in_vars[1]: INPUT_B}
    print(f"Injecting inputs: {inputs}")
    payload = run_debug(inputs=inputs, timeout=240)

    assert_output_value(payload, EXPECTED)
    print(f"OK: Script node present; output contains {EXPECTED}")


if __name__ == "__main__":
    main()
