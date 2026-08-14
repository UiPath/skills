#!/usr/bin/env python3
"""Run each seeded path case and verify its business outcome.

Outcome-based: for every case the grader runs `flow debug --inputs` and asserts
the expected `out` variables. For cases flagged `expect_slack`, it additionally
asserts a non-empty `slackMessageId` — the escalation path must have actually
posted a Slack alert (Slack only returns a message id when a message is really
delivered), not merely reached the node.
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
    assert_flow_uses_connector_target,
    assert_named_equals,
    assert_node_type_executed,
    assert_slack_message_posted,
    run_debug,
)

SLACK_KEY = "uipath-salesforce-slack"


def verify_case(case: dict) -> None:
    payload = run_debug(inputs=case["inputs"], timeout=300)
    for name, expected in case["expected"].items():
        assert_named_equals(payload, name, expected)
    if case.get("expect_slack"):
        # Real Slack ts, tied to an executed Slack node's own response.
        assert_slack_message_posted(payload, "slackMessageId")
    # The task is tagged node:decision: routing must go through a Decision that
    # actually executed — a disconnected Decision or a Script->Slack shortcut fails.
    assert_node_type_executed(payload, "core.logic.decision")
    print(f"OK: {case['name']} produced the expected outcome"
          + (" + Slack message posted" if case.get("expect_slack") else ""))


def main() -> None:
    # The escalation alert must go through the real Slack connector.
    assert_flow_uses_connector_target(SLACK_KEY)

    seed_path = Path("seed.json")
    if not seed_path.is_file():
        raise SystemExit("FAIL: seed.json is missing; pre_run did not complete")
    cases = json.loads(seed_path.read_text(encoding="utf-8")).get("cases")
    if not isinstance(cases, list) or not cases:
        raise SystemExit("FAIL: seed.json must contain at least one case")
    for case in cases:
        verify_case(case)


if __name__ == "__main__":
    main()
