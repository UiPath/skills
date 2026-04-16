#!/usr/bin/env python3
"""GoogleDriveQuotes: a Google Drive connector node executes; output contains
the sentinel string from the quote.txt doc in the hardcoded folder."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_outputs_contain,
    run_debug,
)

SENTINEL = "Just go with the flow."


def main():
    # Require a connector node in the flow — prevents the agent passing by
    # hardcoding the doc contents in a Script node.
    assert_flow_has_node_type(["uipath.connector"])

    payload = run_debug(timeout=240)

    assert_outputs_contain(payload, SENTINEL)
    print(f"OK: Connector node present; output contains {SENTINEL!r}")


if __name__ == "__main__":
    main()
