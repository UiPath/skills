#!/usr/bin/env python3
"""Run each seeded escalation case and check what the run did.

For every case in seed.json the grader runs `flow debug --inputs` once and asserts:

- the named outputs the prompt asks for: severity, engineeringNeeded, caseKey,
  and a non-empty nextSteps;
- the Slack effect: slackMessageId is a real message ts returned by a Slack
  send that completed in this run, posted to #coding-agent-testing, and the
  posted text carries the correlation id, the severity and the next steps.

Nothing here pins node ids, a Script node or a variable the prompt does not
name, so any layout that produces those outputs and that message passes.
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
    _leaves,
    assert_connector_send_identity,
    assert_flow_uses_connector_target,
    assert_named_equals,
    assert_output_nonempty,
    assert_slack_message_posted,
    run_debug,
)

SLACK_KEY = "uipath-salesforce-slack"
SLACK_SEND = "send-message-to-channel"
SLACK_CHANNEL = "C0B2FDZD1M3"  # coding-agent-testing
CASE_SENSITIVE = {"caseKey"}  # opaque id: exact-case match


def check_case(payload: dict, case: dict) -> str:
    """Assert one case's outputs and Slack message; return the posted ts."""
    for name, expected in case["expected"].items():
        assert_named_equals(payload, name, expected, case_sensitive=(name in CASE_SENSITIVE))
    next_steps = " ".join(
        str(v) for v in _leaves(assert_output_nonempty(payload, "nextSteps")) if v is not None
    ).strip()
    # The correlation id is opaque, so it must appear verbatim. Severity and
    # next steps are matched ignoring case, spacing and punctuation, so
    # "SEV1" or next steps rendered as a bulleted list still count.
    return assert_slack_message_posted(
        payload,
        "slackMessageId",
        expected_channel=SLACK_CHANNEL,
        must_contain=case["inputs"]["correlationId"],
        must_contain_loose=[case["expected"]["severity"], next_steps],
        send_op=SLACK_SEND,
    )


def main() -> None:
    # Slack must be reached through the real connector (or a connector-auth
    # HTTP proxy), not a hand-rolled unauthenticated call.
    assert_flow_uses_connector_target(SLACK_KEY)
    # The prompt asks for the alert to go out as the user, not the bot.
    assert_connector_send_identity(SLACK_KEY, expected="user", native_op_hint=SLACK_SEND)

    seed_path = Path("seed.json")
    if not seed_path.is_file():
        raise SystemExit("FAIL: seed.json is missing; pre_run did not complete")
    cases = json.loads(seed_path.read_text(encoding="utf-8")).get("cases")
    if not isinstance(cases, list) or not cases:
        raise SystemExit("FAIL: seed.json must contain at least one case")

    for case in cases:
        # retries=1: the flow posts to a shared channel, so a whole-flow retry
        # would post a duplicate alert.
        payload = run_debug(inputs=case["inputs"], timeout=300, retries=1)
        ts = check_case(payload, case)
        print(
            f"OK: {case['name']}: severity={case['expected']['severity']}, "
            f"engineeringNeeded={case['expected']['engineeringNeeded']}, caseKey preserved, "
            f"Slack alert posted (ts {ts})"
        )


if __name__ == "__main__":
    main()
