#!/usr/bin/env python3
"""Run each seeded path case and check what the run did.

For every case in seed.json the grader runs `flow debug --inputs` once and asserts:

- the named outputs the prompt asks for: escalationPath, severity,
  engineeringNeeded, responseMode and caseKey;
- the Slack effect: slackMessageId is a real message ts returned by a Slack
  send that completed in this run, posted to #coding-agent-testing, whose
  text carries the case's correlation id and escalation path;
- what did NOT run: exactly one Slack send completed, so a case gets the
  escalation alert or the triage notice, never both.

Any layout that produces those outputs and that one message passes: one
Script or several, a Decision or a Switch, one Slack node or two, one End or
two. Nothing pins node ids or variables the prompt does not name.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Walk up to the directory that holds `_shared` so the import resolves.
_directory = os.path.dirname(os.path.abspath(__file__))
while _directory != os.path.dirname(_directory) and not os.path.isdir(
    os.path.join(_directory, "_shared")
):
    _directory = os.path.dirname(_directory)
sys.path.insert(0, _directory)

from _shared.flow_check import (  # noqa: E402
    _fail_with_capture,
    assert_connector_send_identity,
    assert_flow_uses_connector_target,
    assert_named_equals,
    assert_slack_message_posted,
    completed_connector_node_ids,
    run_debug,
)

SLACK_KEY = "uipath-salesforce-slack"
SLACK_SEND = "send-message-to-channel"
SLACK_CHANNEL = "C0B2FDZD1M3"  # coding-agent-testing
CASE_SENSITIVE = {"caseKey"}  # opaque id: exact-case match


def check_case(payload: dict, case: dict) -> str:
    """Assert one case's outputs and its single Slack message; return the ts."""
    for name, expected in case["expected"].items():
        assert_named_equals(payload, name, expected, case_sensitive=(name in CASE_SENSITIVE))
    fired = completed_connector_node_ids(payload, SLACK_KEY, native_op_hint=SLACK_SEND)
    if len(fired) > 1:
        _fail_with_capture(
            f"{case['name']}: {len(fired)} Slack sends completed ({sorted(fired)}); "
            "a case gets the escalation alert or the triage notice, not both"
        )
    # The correlation id is opaque and must appear verbatim. The path is matched
    # ignoring case and separators, so "unknown_customer" also matches a
    # rendered "Unknown customer".
    return assert_slack_message_posted(
        payload,
        "slackMessageId",
        expected_channel=SLACK_CHANNEL,
        must_contain=case["inputs"]["correlationId"],
        must_contain_loose=[case["expected"]["escalationPath"]],
        send_op=SLACK_SEND,
    )


def main() -> None:
    # Slack must be reached through the real connector (or a connector-auth
    # HTTP proxy), not a hand-rolled unauthenticated call.
    assert_flow_uses_connector_target(SLACK_KEY)
    # The prompt asks for every message to go out as the user, not the bot.
    assert_connector_send_identity(SLACK_KEY, expected="user", native_op_hint=SLACK_SEND)

    seed_path = Path("seed.json")
    if not seed_path.is_file():
        raise SystemExit("FAIL: seed.json is missing; pre_run did not complete")
    cases = json.loads(seed_path.read_text(encoding="utf-8")).get("cases")
    if not isinstance(cases, list) or not cases:
        raise SystemExit("FAIL: seed.json must contain at least one case")

    for case in cases:
        # retries=1: every case posts to a shared channel, so a whole-flow retry
        # would post a duplicate; seven serial cases also need a bounded budget.
        payload = run_debug(inputs=case["inputs"], timeout=300, retries=1)
        ts = check_case(payload, case)
        print(
            f"OK: {case['name']}: path={case['expected']['escalationPath']}, "
            f"severity={case['expected']['severity']}, one Slack message posted (ts {ts})"
        )


if __name__ == "__main__":
    main()
