#!/usr/bin/env python3
"""Execute the seeded billing-dispute case and verify BOTH outcomes.

DevCon billing-dispute scenario, graded on delivered side effects (not "did it
run"):

  1. DATA SERVICE — a real ``uipath-dataservice.query`` node resolved the messy
     seeded invoice to MCS-2026-04872 with 8 line items. The count is a
     deterministic oracle; a required query node blocks hardcoding.
  2. SLACK — the ``Send Message to channel`` activity actually posted. The flow
     surfaces the posted message's ts as ``slackMessageId``, and a Slack API
     call only returns a real ts when a message was delivered. The posted
     message must carry the matched invoice number and the correlationId.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Walk up to the directory that holds `_shared` so the import works regardless
# of how deep this task lives under tests/tasks/uipath-maestro-flow/.
_directory = os.path.dirname(os.path.abspath(__file__))
while _directory != os.path.dirname(_directory) and not os.path.isdir(
    os.path.join(_directory, "_shared")
):
    _directory = os.path.dirname(_directory)
sys.path.insert(0, _directory)

from _shared.flow_check import (  # noqa: E402
    assert_connector_send_identity,
    assert_flow_has_node_type,
    assert_flow_uses_connector_target,
    assert_named_equals,
    assert_output_value,
    assert_slack_message_posted,
    run_debug,
)

SLACK_KEY = "uipath-salesforce-slack"
SLACK_CHANNEL = "C0B2FDZD1M3"  # coding-agent-testing
EXPECTED_INVOICE = "MCS-2026-04872"
EXPECTED_LINE_COUNT = 8


def main() -> None:
    # DevCon billing anchor + anti-hardcode: the flow must actually query Data
    # Service (you cannot fake lineItemCount == 8 without querying).
    assert_flow_has_node_type(["uipath-dataservice.query"])

    # The flow must reach Slack through the real connector (or a connector-auth
    # HTTP proxy), not a hand-rolled unauthenticated HTTP call, and send as
    # `user` (not the default bot).
    assert_flow_uses_connector_target(SLACK_KEY)
    assert_connector_send_identity(
        SLACK_KEY, expected="user", native_op_hint="send-message-to-channel"
    )

    seed_path = Path("seed.json")
    if not seed_path.is_file():
        raise SystemExit("FAIL: seed.json is missing; pre_run did not complete")
    cases = json.loads(seed_path.read_text(encoding="utf-8")).get("cases")
    if not isinstance(cases, list) or len(cases) != 1:
        raise SystemExit("FAIL: seed.json must contain exactly one case")
    case = cases[0]

    # retries=1: this flow POSTS to the shared Slack channel, so a whole-flow
    # retry on a transient poll/5xx failure would post a duplicate alert.
    payload = run_debug(inputs=case["inputs"], timeout=300, retries=1)

    # DATA SERVICE outcome: the messy invoice resolved to the seeded invoice
    # with its exact line-item count, via the real query.
    assert_named_equals(payload, "matchedInvoiceNumber", EXPECTED_INVOICE)
    assert_output_value(payload, EXPECTED_LINE_COUNT)
    assert_named_equals(
        payload, "caseKey", case["inputs"]["correlationId"], case_sensitive=True
    )

    # SLACK outcome: verified against the executed send's own response — a real
    # ts from an executed Slack SEND node, posted to coding-agent-testing, whose
    # message carries the matched invoice number and the correlationId.
    assert_slack_message_posted(
        payload,
        "slackMessageId",
        expected_channel=SLACK_CHANNEL,
        must_contain=[case["inputs"]["correlationId"], EXPECTED_INVOICE],
    )

    print(
        f"OK: {case['name']} completed — Data Service resolved {EXPECTED_INVOICE} "
        f"({EXPECTED_LINE_COUNT} line items), correlationId preserved, and the "
        "Slack alert was posted (real message ts)"
    )


if __name__ == "__main__":
    main()
