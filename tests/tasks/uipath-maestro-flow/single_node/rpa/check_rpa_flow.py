#!/usr/bin/env python3
"""HelpDeskTicketTitle: an RPA-workflow node executes; output holds the title."""

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
    assert_outputs_contain,
    run_debug,
)


def main():
    assert_flow_has_node_type(["uipath.core.rpa-workflow"])
    # The workflow itself is a fixed in-process lookup, but the run still has
    # to provision and start a robot, so keep a generous budget.
    payload = run_debug(timeout=540)
    assert_outputs_contain(payload, "password reset loop")
    print("OK: RPA node present; output contains 'password reset loop'")


if __name__ == "__main__":
    main()
