#!/usr/bin/env python3
"""ApproverCountAgent: a coded-agent node executes; output holds the count (3).

The reviewers' stances are stated in free text ("signed off", "asked for
changes", "recused herself") with no tally and no number-word for the answer,
so a deterministic coded function (regex / word-to-number parsing) cannot reach
the count. Solving it requires an LLM-bearing Agent framework — LangGraph /
LlamaIndex / OpenAI Agents — which scaffolds ProjectType: "Agent" and produces a
uipath.core.agent.<key> node. The Coded Function framework (uipath package)
would produce uipath.core.function.<key>, failing the node-type assert below.
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
