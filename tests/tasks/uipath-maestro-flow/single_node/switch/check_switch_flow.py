#!/usr/bin/env python3
"""Switch: inject quarter=2 and assert a Switch node produces 'Summer'."""

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
    assert_flow_has_node_type(["core.logic.switch"])

    project_dir = find_project_dir()
    in_vars = read_flow_input_vars(project_dir)

    inputs = {in_vars[0]: 2} if in_vars else None
    payload = run_debug(inputs=inputs)

    # Quarter 2 -> "Summer"
    assert_outputs_contain(payload, "summer")

    print("OK: Switch node present; quarter 2 returns 'Summer'")


if __name__ == "__main__":
    main()
