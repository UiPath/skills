#!/usr/bin/env python3
"""LoopMultiply: a Loop node iterates over [13, 15, 17]; output is 3315."""

import os
import sys

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-maestro-flow")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, _shared_root)
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_output_value,
    run_debug,
)

EXPECTED = 13 * 15 * 17  # 3315


def main():
    assert_flow_has_node_type(["core.logic.loop"])
    payload = run_debug(timeout=240)
    assert_output_value(payload, EXPECTED)
    print(f"OK: Loop node present; output contains {EXPECTED}")


if __name__ == "__main__":
    main()
