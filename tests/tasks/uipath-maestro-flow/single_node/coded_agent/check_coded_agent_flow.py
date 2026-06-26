#!/usr/bin/env python3
"""ApproverCountAgent: a coded-agent node executes; output holds the count (3).

The prompt explicitly asks for a coded AGENT on a free-text task. The skill must
honor that request: scaffold an Agent project (ProjectType: "Agent" — LangGraph /
LlamaIndex / OpenAI Agents) producing a uipath.core.agent.<key> node, NOT downgrade
it to a coded Function (ProjectType: "Function", uipath.core.function.<key>) that
regexes the wording or hardcodes the answer because the task looks deterministic.
The node-type assert below fails on a Function — a correct count from the wrong
node kind does not satisfy an explicit agent request.
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
    assert_flow_has_node_type(["uipath.core.agent"])
    payload = run_debug(timeout=240)
    # Dana, Priya, Sam signed off → 3 approvers (Marco and Lena did not).
    assert_output_value(payload, 3)
    print("OK: Coded-agent node present; output contains 3")


if __name__ == "__main__":
    main()
