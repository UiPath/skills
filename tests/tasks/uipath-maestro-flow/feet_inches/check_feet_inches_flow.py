#!/usr/bin/env python3
"""FeetInches: switch routes (value, direction) to the right conversion.

Runs debug twice to exercise both switch cases:
  - (23, "f2i") -> 276    (feet -> inches: value * 12)
  - (276, "i2f") -> 23    (inches -> feet: value / 12)
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_output_value,
    find_project_dir,
    run_debug,
)

CASES = [
    ({"f2i_value": 23, "direction_value": "f2i"}, 276),
    ({"f2i_value": 276, "direction_value": "i2f"}, 23),
]


def find_input_var_names(project_dir: str) -> tuple[str, str]:
    """Return (number_input_id, string_input_id) from the first .flow file.

    The agent picks the variable names; we identify them by declared type so
    the test isn't coupled to a specific naming choice.
    """
    flows = glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True)
    if not flows:
        sys.exit(f"FAIL: No .flow file found under {project_dir}")
    with open(flows[0]) as f:
        flow = json.load(f)
    globals_list = (flow.get("variables") or {}).get("globals") or []
    number_ids = [
        v["id"]
        for v in globals_list
        if v.get("direction") in ("in", "inout") and v.get("type") == "number"
    ]
    string_ids = [
        v["id"]
        for v in globals_list
        if v.get("direction") in ("in", "inout") and v.get("type") == "string"
    ]
    if not number_ids or not string_ids:
        sys.exit(
            f"FAIL: Expected one number and one string input variable; "
            f"found number={number_ids}, string={string_ids}"
        )
    return number_ids[0], string_ids[0]


def main():
    # Switch node is required — prevents the agent from hardcoding the
    # conversion in a single script without branching on direction.
    assert_flow_has_node_type(["core.logic.switch"])

    project_dir = find_project_dir()
    number_id, string_id = find_input_var_names(project_dir)
    print(f"Input variables: number={number_id!r}, direction={string_id!r}")

    for marker, expected in CASES:
        inputs = {number_id: marker["f2i_value"], string_id: marker["direction_value"]}
        print(f"\nInjecting inputs: {inputs} (expect {expected})")
        payload = run_debug(inputs=inputs, timeout=240)
        assert_output_value(payload, expected)
        print(f"OK: ({inputs}) -> {expected}")

    print("\nOK: Switch routed both directions correctly")


if __name__ == "__main__":
    main()
