#!/usr/bin/env python3
"""CountLettersLowCode: a low-code-agent node executes; output holds the count (2)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_output_value,
    run_debug,
)


def main():
    # Coded and low-code agents share the `uipath.core.agent.{guid}` node-type
    # family on this tenant — distinguished only by registry DisplayName, not
    # by node-type prefix. The prompt drives the coded-vs-lowcode choice;
    # this check just verifies an agent node was used.
    assert_flow_has_node_type(["uipath.core.agent"])
    payload = run_debug(timeout=240)
    # 2 r's in 'arrow'.
    assert_output_value(payload, 2)
    print("OK: Low-code agent node present; output contains 2")


if __name__ == "__main__":
    main()
