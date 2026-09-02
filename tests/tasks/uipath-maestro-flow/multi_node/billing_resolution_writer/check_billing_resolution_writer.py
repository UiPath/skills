#!/usr/bin/env python3
"""Inline-agent writer flow that ALSO posts to Slack.

Tests a Maestro Flow whose inline low-code agent (`uipath.agent.autonomous`)
drafts a resolution and then posts it to Slack. Three layers:
  1. Structural: the flow contains an inline autonomous agent node (anti-hardcode
     — a Script node cannot stand in for the agent) AND a real Slack connector
     send node.
  2. Draft behavior: `flow debug` completes and the drafted email — landed in the
     mapped `emailBody` output — cites the invoice and the approved credit.
  3. Slack outcome: the `Send Message to channel` activity actually posted — the
     flow surfaces the posted message's ts as `slackMessageId`, verified against
     the executed send node's own response, and the message carries the
     correlationId and the invoice number.

The behavior grade scopes to the `emailBody` output global, NOT the whole debug
payload. Matching the whole payload is a false pass: the trigger echoes the
`invoiceNumber` input back into the outputs, so the invoice string is "present"
even when the agent refuses to draft OR the End node never maps the agent's
result into `emailBody`. Scoping to `emailBody` catches both.
"""
import os
import sys
from uuid import uuid4

# Walk up to the skill's tests root (the dir holding the _shared package).
_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from _shared.flow_check import (  # noqa: E402
    assert_connector_send_identity,
    assert_flow_has_node_type,
    assert_flow_uses_connector_target,
    assert_named_output_contains,
    assert_output_nonempty,
    assert_slack_message_posted,
    run_debug,
)

INVOICE = "MCS-2026-04872"
SLACK_KEY = "uipath-salesforce-slack"
SLACK_CHANNEL = "C0B2FDZD1M3"  # coding-agent-testing
# Fresh correlationId per run isolates this run's Slack message from prior runs.
CORRELATION_ID = f"RESO-{uuid4().hex[:12]}"
INPUTS = {
    "customerName": "Northwind Traders",
    "invoiceNumber": INVOICE,
    "creditAmount": 1610,
    "correlationId": CORRELATION_ID,
}


def main():
    assert_flow_has_node_type(["uipath.agent.autonomous"])
    assert_flow_uses_connector_target(SLACK_KEY)
    assert_connector_send_identity(
        SLACK_KEY, expected="user", native_op_hint="send-message-to-channel"
    )
    print("OK: flow contains an inline uipath.agent.autonomous node + a Slack send node")

    payload = run_debug(inputs=INPUTS, timeout=540)
    # Subject must be mapped + non-empty.
    assert_output_nonempty(payload, "emailSubject")
    # Body must be mapped, cite the invoice, and state the approved credit.
    assert_named_output_contains(payload, "emailBody", INVOICE)
    assert_named_output_contains(payload, "emailBody", ["1610", "1,610"], require_all=False)
    print(f"OK: emailBody drafted, cites invoice {INVOICE} and the approved credit")

    # Slack outcome — verified against the executed send's own response.
    assert_slack_message_posted(
        payload,
        "slackMessageId",
        expected_channel=SLACK_CHANNEL,
        must_contain=[CORRELATION_ID, INVOICE],
    )
    print("OK: Slack alert posted (real message ts) carrying the correlationId + invoice")


if __name__ == "__main__":
    main()
