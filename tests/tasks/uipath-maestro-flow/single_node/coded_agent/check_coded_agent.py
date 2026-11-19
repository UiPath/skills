#!/usr/bin/env python3
"""ApproverCountAgent: debug the flow on a sentence the prompt never shows and
assert what the run did and returned.

The sentence is known only to this checker, so neither the agent nor a regex
can be fitted to it: Dana, Priya and Sam signed off, Marco asked for changes
and Lena recused herself, so 3 people approved.

The run must complete the flow's agent node (a `uipath.core.agent.<key>` node,
the node a coded Agent project gets; a coded Function would be
`uipath.core.function.<key>`) and return `approvedCount` = 3, read by the name
the prompt gives. The prompt does not name the input, so the sentence is fed to
the declared input that best means it (`flow_io_roles.map_inputs`).
"""
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from _shared import flow_io_roles as io  # noqa: E402
from _shared.flow_check import (  # noqa: E402
    _fail,
    _fail_with_capture,
    _load_flow,
    assert_flow_has_node_type,
    assert_output_nonempty,
    completed_node_ids_of_type,
    run_debug,
)

AGENT_TYPE = "uipath.core.agent."
SENTENCE = (
    "The proposal went to Dana, Marco, Priya, Lena and Sam for review. "
    "Dana, Priya and Sam each signed off, Marco asked for changes, "
    "and Lena recused herself."
)
EXPECTED = 3
ROLES = {"text": {"value": SENTENCE, "keywords": [
    "sentence", "outcome", "review", "description", "summary", "message", "text", "input"]}}


def check(payload):
    ran = completed_node_ids_of_type(payload, AGENT_TYPE)
    if not ran:
        _fail_with_capture("the agent node did not complete in the debug run")
    print(f"OK: the agent node completed ({sorted(ran)})")
    got = assert_output_nonempty(payload, "approvedCount")
    try:
        ok = float(str(got).strip()) == EXPECTED
    except ValueError:
        ok = False
    if not ok:
        _fail(f"output 'approvedCount': expected {EXPECTED}, got {got!r}")
    print(f"OK: approvedCount={got!r}")


def main():
    assert_flow_has_node_type([AGENT_TYPE])
    flow = _load_flow("**/project.uiproj")
    inputs, _attachments, unmapped = io.map_inputs(flow, ROLES, object_fallback=None, file_path=None)
    if problem := io.unmapped_error(flow, unmapped, inputs):
        _fail(problem)
    print(f"debug inputs: {inputs}")
    check(run_debug(inputs=inputs, timeout=300))


if __name__ == "__main__":
    main()
