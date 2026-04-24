#!/usr/bin/env python3
"""FeetInches: one debug run per direction, asserting the exact converted value.

Usage: check_feet_inches_flow.py {f2i|i2f|y2f}
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_output_value,
    run_debug,
)

CASES = {
    # case: (value, direction, expected_result)
    "f2i": (23, "f2i", 276),
    "i2f": (276, "i2f", 23),
    "y2f": (15, "y2f", 45),
}


def main():
    case = sys.argv[1] if len(sys.argv) > 1 else ""
    if case not in CASES:
        sys.exit(f"FAIL: Unknown case {case!r}; expected one of {list(CASES)}")

    # Require a Switch node — blocks agents that hardcode both formulas in a
    # single Script without branching on direction.
    assert_flow_has_node_type(["core.logic.switch"])

    value, direction, expected = CASES[case]
    inputs = {"value": value, "direction": direction}
    print(f"[{case}] Injecting inputs: {inputs} (expect {expected})")
    payload = run_debug(inputs=inputs, timeout=240)
    assert_output_value(payload, expected)
    print(f"OK: [{case}] {inputs} -> {expected}")


if __name__ == "__main__":
    main()
