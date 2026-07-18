#!/usr/bin/env python3
"""InlineAgentSum: an inline-agent node executes; output holds the sum (42).

Distinct from coded_agent / lowcode_agent: those exercise the published-agent
node family (``uipath.core.agent.{key}``), whose source identity comes from
the tenant registry. This test exercises the inline form
(``uipath.agent.autonomous``), whose ``inputs.source`` resolves to a local
UUID subdirectory inside the flow project — proving inputs.source hydration
end-to-end.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_output_value,
    run_debug,
)


def main():
    assert_flow_has_node_type(["uipath.agent.autonomous"])
    payload = run_debug(timeout=240)
    # 17 + 25 = 42. Default inline-agent outputSchema is content:string,
    # so match via case-insensitive substring on the agent's text response.
    assert_output_value(payload, "42")
    print("OK: Inline-agent node present; output contains 42")


if __name__ == "__main__":
    main()
