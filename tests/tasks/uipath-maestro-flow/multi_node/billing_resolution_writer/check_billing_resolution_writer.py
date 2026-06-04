#!/usr/bin/env python3
"""DevCon BillingDisputeResolution — Resolution Writer (inline low-code agent).

The agent builds + validates a Maestro Flow whose single work node is an inline
low-code agent (`uipath.agent.autonomous`, scaffolded with
`uip agent init --inline-in-flow`) that drafts a customer-facing resolution
email. This check runs `uip maestro flow debug` itself and asserts the flow
completes and the drafted email cites the disputed invoice number.

Two layers:
  1. Structural (passes today): the flow must contain an inline autonomous agent
     node. Anti-hardcode — you cannot satisfy the email oracle with a script.
  2. Execution (RED until the inline-agent runtime lands — MST-9381): `flow
     debug` must reach finalStatus Completed and the agent output must echo the
     invoice number it was grounded on.

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

# Walk up to the skill's tests root (the dir holding the _shared package) so
# this resolves regardless of how deeply the task is nested under tests/tasks/.
_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_outputs_contain,
    run_debug,
)

INVOICE = "MCS-2026-04872"
INPUTS = {
    "customerName": "Northwind Traders",
    "invoiceNumber": INVOICE,
    "creditAmount": 1610,
}


def main():
    # Anti-hardcode: the work must be done by an inline low-code agent, not a
    # script that fakes the email text.
    assert_flow_has_node_type(["uipath.agent.autonomous"])
    print("OK: flow contains an inline uipath.agent.autonomous node")

    payload = run_debug(inputs=INPUTS, timeout=300)
    # A correct resolution email states the disputed invoice number.
    assert_outputs_contain(payload, INVOICE)
    print(f"OK: inline agent drafted a resolution email citing {INVOICE}")


if __name__ == "__main__":
    main()
