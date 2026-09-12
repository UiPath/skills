#!/usr/bin/env python3
"""Inline-agent writer flow that ALSO posts to Slack.

Tests a Maestro Flow whose inline low-code agent (`uipath.agent.autonomous`)
drafts a resolution and then posts it to Slack. Three layers:
  1. Structural: the flow contains an inline autonomous agent node (anti-hardcode
     — a Script node cannot stand in for the agent) AND a real Slack connector
     send node.
  2. Draft behavior: `flow debug` completes; the drafted email — landed in the
     mapped `emailBody` output — cites the invoice and the approved credit, AND
     `emailBody` is the EXECUTED agent node's own output (not a JS template that
     fabricates it from the trigger inputs — the node-type check is source-only).
  3. Slack outcome: the `Send Message to channel` activity actually posted — the
     flow surfaces the posted message's ts as `slackMessageId`, verified against
     the executed send node's own response, and the message carries the drafted
     `emailBody`, not only the trigger echoes.

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
    assert_named_equals,
    assert_named_output_contains,
    assert_output_nonempty,
    assert_slack_message_posted,
    completed_node_ids_of_type,
    node_output_leaves,
    run_debug,
)

INVOICE = "MCS-2026-04872"
SLACK_KEY = "uipath-salesforce-slack"
SLACK_CHANNEL = "C0B2FDZD1M3"  # coding-agent-testing
# Fresh correlationId per run is anti-hardcode: a per-run random token cannot be
# baked into the flow, so a passing Slack post must carry a value the flow read from
# this run's trigger, not a literal. (assert_slack_message_posted reads the ts +
# content off the executed send node's own response, so prior runs never interfere.)
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

    # retries=1: this flow POSTS to the shared Slack channel, so a whole-flow retry
    # on a transient poll/5xx failure would re-post a duplicate message. One attempt
    # only; a genuine transient failure fails the run cleanly.
    payload = run_debug(inputs=INPUTS, timeout=540, retries=1)
    # Subject must be mapped + non-empty.
    assert_output_nonempty(payload, "emailSubject")
    # Body must be mapped, cite the invoice, and state the approved credit.
    body = assert_output_nonempty(payload, "emailBody")
    assert_named_output_contains(payload, "emailBody", INVOICE)
    assert_named_output_contains(payload, "emailBody", ["1610", "1,610"], require_all=False)
    print(f"OK: emailBody drafted, cites invoice {INVOICE} and the approved credit")

    # emailBody must come FROM the executed agent, not a JS template that fabricates
    # it from the trigger inputs. assert_flow_has_node_type is source-only, so without
    # this an unexecuted agent node plus one template feeding both emailBody and the
    # Slack text would pass at full weight. Tie the value to the agent's own response.
    agent_ids = completed_node_ids_of_type(payload, "uipath.agent.autonomous")
    if str(body).strip() not in node_output_leaves(payload, agent_ids):
        sys.exit("FAIL: emailBody did not come from the executed uipath.agent.autonomous node")
    print("OK: emailBody is the executed agent's own output")

    # caseKey must echo the incoming correlationId (opaque id — exact case).
    assert_named_equals(payload, "caseKey", CORRELATION_ID, case_sensitive=True)

    # Slack outcome — verified against the executed send's own response: the posted
    # message must carry the mapped emailBody (body[:80]), not only the trigger echoes.
    assert_slack_message_posted(
        payload,
        "slackMessageId",
        expected_channel=SLACK_CHANNEL,
        must_contain=[CORRELATION_ID, INVOICE, str(body)[:80]],
    )
    print("OK: Slack message posted (real ts) carrying the correlationId + the drafted resolution")


if __name__ == "__main__":
    main()
