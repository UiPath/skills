#!/usr/bin/env python3
"""Check for the Test Manager Maestro-Flow connector task.

SKELETON: mirrors the _shared/flow_check pattern used by the billing connector
flows. Before un-skipping the task, set CONNECTOR_NODE to the real node type
(confirm via `uip maestro flow registry search testmanager --output json`).

The check (a) anti-hardcode gate: the produced flow must contain the real Test
Manager connector node (not a Script faking it), then (b) debugs the flow and
asserts the created test case name round-trips back through the outputs.
"""
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_outputs_contain,
    find_project_dir,
    read_flow_input_vars,
    run_debug,
)

# TODO(node-type): confirm the real Test Manager create node type via
#   `uip maestro flow registry search testmanager --output json`
# First-party connectors follow uipath.connector.<connectorKey>.<operation>;
# the connectorKey is uipath-uipath-testmanager. Substring match is enough.
CONNECTOR_NODE = "uipath-uipath-testmanager"
TC_NAME = "Connector Eval - Maestro Flow TC"


def main():
    # (a) A real Test Manager connector node must be present.
    assert_flow_has_node_type([CONNECTOR_NODE])
    # (b) Debug the flow; the created test case name must echo back in outputs.
    in_vars = read_flow_input_vars(find_project_dir())
    inputs = {in_vars[0]: TC_NAME} if in_vars else {"testCaseName": TC_NAME}
    payload = run_debug(inputs=inputs, timeout=300)
    assert_outputs_contain(payload, TC_NAME)
    print(f"OK: Test Case created via {CONNECTOR_NODE} and echoed: {TC_NAME}")


if __name__ == "__main__":
    main()
