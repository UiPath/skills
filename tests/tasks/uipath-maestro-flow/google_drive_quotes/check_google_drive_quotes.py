#!/usr/bin/env python3
"""GoogleDriveQuotes: a Google Drive connector node executes; the folder URL
is injected as input; output contains the sentinel string from the Quotes doc."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_outputs_contain,
    find_project_dir,
    read_flow_input_vars,
    run_debug,
)

FOLDER_URL = (
    "https://drive.google.com/drive/u/0/folders/17l9eNEERL4GD7bGF6BkajAOKXcq_OnYr"
)
SENTINEL = "Just go with the flow."


def main():
    # Require a connector node in the flow — prevents the agent passing by
    # hardcoding the doc contents in a Script node.
    assert_flow_has_node_type(["uipath.connector"])

    project_dir = find_project_dir()
    in_vars = read_flow_input_vars(project_dir)
    if not in_vars:
        sys.exit("FAIL: No input variable found for folder URL")

    inputs = {in_vars[0]: FOLDER_URL}
    print(f"Injecting inputs: {inputs}")
    payload = run_debug(inputs=inputs, timeout=240)

    assert_outputs_contain(payload, SENTINEL)
    print(f"OK: Connector node present; output contains {SENTINEL!r}")


if __name__ == "__main__":
    main()
