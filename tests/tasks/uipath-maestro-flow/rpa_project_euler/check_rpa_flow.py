#!/usr/bin/env python3
"""ProjectEulerTitle: an RPA-workflow node executes; output holds the title."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_outputs_contain,
    run_debug,
)


def main():
    assert_flow_has_node_type(["uipath.core.rpa-workflow"])
    # RPA workflows are slow: spin up robot, launch Chrome, scrape. 4 min
    # is routinely not enough on this tenant.
    payload = run_debug(timeout=540)
    assert_outputs_contain(payload, "prime square remainders")
    print("OK: RPA node present; output contains 'prime square remainders'")


if __name__ == "__main__":
    main()
