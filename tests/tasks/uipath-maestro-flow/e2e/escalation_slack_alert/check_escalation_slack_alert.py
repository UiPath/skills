#!/usr/bin/env python3
"""Execute the seeded Sev1 escalation case and verify the Slack alert was sent.

Outcome-based, not "did it run": beyond a green `finalStatus`, this asserts the
Slack `Send Message to channel` activity actually posted — the flow surfaces the
posted message's identifier as the `slackMessageId` out variable, and a Slack
API call only returns a message id when a message was really delivered. The
classification outputs (severity, engineeringNeeded, caseKey) are checked too so
a flow that posts to Slack but misclassifies still fails.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# Walk up to the directory that holds `_shared` so the import works regardless
# of how deep this task lives under tests/tasks/uipath-maestro-flow/.
_directory = os.path.dirname(os.path.abspath(__file__))
while _directory != os.path.dirname(_directory) and not os.path.isdir(
    os.path.join(_directory, "_shared")
):
    _directory = os.path.dirname(_directory)
sys.path.insert(0, _directory)

from _shared.flow_check import (  # noqa: E402
    assert_flow_uses_connector_target,
    assert_output_nonempty,
    run_debug,
)

SLACK_KEY = "uipath-salesforce-slack"


def normalized(value: Any) -> Any:
    if isinstance(value, str):
        lowered = value.strip().casefold()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        return lowered
    return value


def assert_named_equals(payload: dict, name: str, expected: Any) -> None:
    actual = assert_output_nonempty(payload, name)
    if normalized(actual) != normalized(expected):
        raise SystemExit(f"FAIL: output {name!r}: expected {expected!r}, got {actual!r}")


def main() -> None:
    # The flow must reach Slack through the real connector (or a connector-auth
    # HTTP proxy), not a hand-rolled unauthenticated HTTP call.
    assert_flow_uses_connector_target(SLACK_KEY)

    seed_path = Path("seed.json")
    if not seed_path.is_file():
        raise SystemExit("FAIL: seed.json is missing; pre_run did not complete")
    cases = json.loads(seed_path.read_text(encoding="utf-8")).get("cases")
    if not isinstance(cases, list) or len(cases) != 1:
        raise SystemExit("FAIL: seed.json must contain exactly one case")
    case = cases[0]

    payload = run_debug(inputs=case["inputs"], timeout=300)

    # Classification outcomes.
    for name, expected in case["expected"].items():
        assert_named_equals(payload, name, expected)

    # The Slack side effect: a posted-message identifier proves the alert was
    # actually delivered to the channel.
    assert_output_nonempty(payload, "slackMessageId")

    print(
        f"OK: {case['name']} completed — Sev1 + engineering classified, "
        "correlationId preserved, and the Slack alert was posted (message id present)"
    )


if __name__ == "__main__":
    main()
