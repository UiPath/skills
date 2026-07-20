#!/usr/bin/env python3
"""ApproverCountAgent: a coded-agent node analyzes an unseen sentence; output is 3.

The prompt explicitly asks for a coded AGENT on a free-text task and deliberately
does NOT disclose the sentence — the flow declares a string input variable, and
this checker injects the sentence at debug time via ``--inputs``. The agent must
identify each person mentioned, classify their stance (approved / requested
changes / recused), and return the approval count, so a deterministic Function
that regexes known wording or hardcodes the answer is not a viable design.

The skill must honor the agent request: scaffold an Agent project (ProjectType:
"Agent" — LangGraph / LlamaIndex / OpenAI Agents) producing a
uipath.core.agent.<key> node, NOT downgrade it to a coded Function (ProjectType:
"Function", uipath.core.function.<key>). The node-type assert below fails on a
Function — a correct count from the wrong node kind does not satisfy an explicit
agent request.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_output_value,
    find_project_dir,
    read_flow_input_vars,
    run_debug,
)

# Known only to this checker — never shown to the agent under test.
SENTENCE = (
    "The proposal went to Dana, Marco, Priya, Lena and Sam for review. "
    "Dana, Priya and Sam each signed off, Marco asked for changes, "
    "and Lena recused herself."
)
EXPECTED = 3  # Dana, Priya, Sam signed off; Marco and Lena did not.


def main():
    assert_flow_has_node_type(["uipath.core.agent"])

    project_dir = find_project_dir()
    in_vars = read_flow_input_vars(project_dir)
    if not in_vars:
        sys.exit(
            "FAIL: Flow declares no input variables; "
            "expected a string input for the sentence"
        )
    var = in_vars[0]
    if len(in_vars) > 1:
        var = next(
            (v for v in in_vars if re.search(r"sentence|text|summary|input", v, re.I)),
            in_vars[0],
        )

    print(f"Injecting sentence into input variable {var!r}")
    payload = run_debug(inputs={var: SENTENCE}, timeout=300)

    assert_output_value(payload, EXPECTED)
    print(f"OK: Coded-agent node present; output contains {EXPECTED}")


if __name__ == "__main__":
    main()
