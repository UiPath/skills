#!/usr/bin/env python3
"""DevCon BillingDisputeResolution — Dispute Analyst (context-grounded inline agent).

The agent builds + validates a Maestro Flow whose single work node is an inline
low-code agent (`uipath.agent.autonomous`, scaffolded with
`uip agent init --inline-in-flow`) grounded on the existing "Billing Dispute SOP
Index" via its `context` handle. This check runs `uip maestro flow debug` itself
and asserts the flow completes with a non-empty determination.

Three layers:
  1. Structural (passes today): the flow must contain BOTH an inline autonomous
     agent node AND a `uipath.agent.resource.context.index.*` node — the agent's
     `context` handle must be wired to a real semantic index. Anti-hardcode: a
     script cannot stand in for SOP-grounded analysis.
  2. Execution (RED until the inline-agent runtime lands — MST-9381): `flow
     debug` must reach finalStatus Completed.
  3. Output: the agent must produce a non-empty determination.

NOTE (2026-06): greenfield inline-agent `flow debug` faults at the agent node
with `170007 ... the job's associated process could not be found`. The CLI half
of the provisioning fix (cli#1914) is shipped and verified in the binary, but
the Orchestrator/runtime half is not yet available on the test tenant, so no
greenfield inline agent can execute under debug. This check is structured to
pass unchanged once that lands — intentionally RED until then, the same
validate-passes / debug-faults split the billing connector tasks use.
"""
import os
import sys

# Walk up to the skill's tests root (the dir holding the _shared package).
_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    collect_outputs,
    run_debug,
)

INPUTS = {
    "disputeDescription": "Charged 14 units at $300 but the contracted unit price is $290.",
    "invoiceNumber": "MCS-2026-04872",
}


def main():
    # Anti-hardcode: an inline low-code agent grounded on a real semantic index.
    assert_flow_has_node_type(["uipath.agent.autonomous"])
    assert_flow_has_node_type(["uipath.agent.resource.context.index"])
    print("OK: flow wires an inline autonomous agent to a context.index node")

    payload = run_debug(inputs=INPUTS, timeout=300)
    # The SOP-grounded agent must return a non-empty analysis.
    nonempty = [v for v in collect_outputs(payload) if isinstance(v, str) and v.strip()]
    if not nonempty:
        sys.exit("FAIL: agent produced no non-empty determination/rationale output")
    print("OK: grounded inline agent returned a non-empty determination")


if __name__ == "__main__":
    main()
