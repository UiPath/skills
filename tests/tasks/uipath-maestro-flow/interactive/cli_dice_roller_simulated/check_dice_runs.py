#!/usr/bin/env python3
"""DiceRoller (simulated): a Script node runs and produces an integer in [1, 6].

Name-agnostic runtime checker for the simulated variant. Identical assertions to
the retired non-simulated original (multi_node/dice_roller/check_dice_runs.py):
locates the Flow project via `_shared.flow_check`, runs `uip maestro flow debug`,
and asserts the output is an integer in [1, 6] — not merely that the script text
contains "random" (which a flow that never executes would still pass)."""

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
    assert_output_int_in_range,
    run_debug,
)


def main():
    assert_flow_has_node_type(["core.action.script"])
    payload = run_debug(timeout=600)
    roll = assert_output_int_in_range(payload, 1, 6)
    print(f"OK: Script node present; dice value = {roll}")


if __name__ == "__main__":
    main()
