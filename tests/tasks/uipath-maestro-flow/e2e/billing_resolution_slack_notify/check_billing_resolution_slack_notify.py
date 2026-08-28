#!/usr/bin/env python3
"""Inline-agent writer flow that ALSO posts to Slack — outcome-graded.

Extends the DevCon billing-resolution-writer scenario with a real third-party
side effect. Three layers, so nothing can be faked:

  1. Structural: the flow contains an inline `uipath.agent.autonomous` node
     (a Script cannot stand in for the agent) AND a real Slack connector send.
  2. Draft behavior: `flow debug` completes and the drafted email — landed in
     the mapped `emailBody` output — cites the invoice and the approved credit.
     Scoped to the `emailBody` global, not the whole payload (the trigger echoes
     `invoiceNumber` back, so a whole-payload match is a false pass).
  3. Slack outcome: the `Send Message to channel` activity actually posted — the
     flow surfaces the posted message's ts as `slackMessageId`, verified against
     the executed send node's own response, and the message carries the
     correlationId and the invoice number.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Walk up to the directory that holds `_shared` so the import works regardless
# of how deep this task lives under tests/tasks/uipath-maestro-flow/.
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

SLACK_KEY = "uipath-salesforce-slack"
SLACK_CHANNEL = "C0B2FDZD1M3"  # coding-agent-testing
INVOICE = "MCS-2026-04872"
CREDIT = ["1610", "1,610"]


def main() -> None:
    # Structural anti-hardcode: a real inline agent AND a real Slack send node.
    assert_flow_has_node_type(["uipath.agent.autonomous"])
    assert_flow_uses_connector_target(SLACK_KEY)
    assert_connector_send_identity(
        SLACK_KEY, expected="user", native_op_hint="send-message-to-channel"
    )
    print("OK: inline agent + Slack send node present")

    seed_path = Path("seed.json")
    if not seed_path.is_file():
        raise SystemExit("FAIL: seed.json is missing; pre_run did not complete")
    cases = json.loads(seed_path.read_text(encoding="utf-8")).get("cases")
    if not isinstance(cases, list) or len(cases) != 1:
        raise SystemExit("FAIL: seed.json must contain exactly one case")
    case = cases[0]

    # Default run_debug retry policy: a transient backend 5xx at provisioning
    # (e.g. HTTP 504 on create-debug-instance) fires before the flow runs, so a
    # retry is safe and does not risk a duplicate Slack post.
    payload = run_debug(inputs=case["inputs"], timeout=540)

    # Draft behavior — scoped to the mapped emailBody output.
    assert_output_nonempty(payload, "emailSubject")
    assert_named_output_contains(payload, "emailBody", INVOICE)
    assert_named_output_contains(payload, "emailBody", CREDIT, require_all=False)
    print(f"OK: emailBody drafted, cites invoice {INVOICE} and the approved credit")

    # Slack outcome — verified against the executed send's own response.
    assert_slack_message_posted(
        payload,
        "slackMessageId",
        expected_channel=SLACK_CHANNEL,
        must_contain=[case["inputs"]["correlationId"], INVOICE],
    )
    print(
        f"OK: {case['name']} completed — resolution drafted and the Slack alert "
        "was posted (real message ts) carrying the correlationId + invoice"
    )


if __name__ == "__main__":
    main()
