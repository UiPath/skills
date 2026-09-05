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

# Walk up to the directory that holds `_shared` so the import works regardless
# of how deep this task lives under tests/tasks/uipath-maestro-flow/.
_directory = os.path.dirname(os.path.abspath(__file__))
while _directory != os.path.dirname(_directory) and not os.path.isdir(
    os.path.join(_directory, "_shared")
):
    _directory = os.path.dirname(_directory)
_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-maestro-flow")
    if os.environ.get("SKILLS_REPO_PATH")
    else _directory
)
sys.path.insert(0, _shared_root)

from _shared.flow_check import (  # noqa: E402
    assert_connector_send_identity,
    assert_flow_uses_connector_target,
    assert_named_equals,
    assert_slack_message_posted,
    completed_node_ids_of_type,
    find_node_output_field,
    find_node_output_value,
    normalized,
    run_debug,
)

SLACK_KEY = "uipath-salesforce-slack"
SLACK_CHANNEL = "C0B2FDZD1M3"  # coding-agent-testing
CASE_SENSITIVE = {"caseKey", "jiraIssueKey"}  # opaque ids — exact-case match


def main() -> None:
    # The flow must reach Slack through the real connector (or a connector-auth
    # HTTP proxy), not a hand-rolled unauthenticated HTTP call.
    assert_flow_uses_connector_target(SLACK_KEY)

    # Prompt requires sending as `user` (not the default bot).
    assert_connector_send_identity(SLACK_KEY, expected="user", native_op_hint="send-message-to-channel")

    seed_path = Path("seed.json")
    if not seed_path.is_file():
        raise SystemExit("FAIL: seed.json is missing; pre_run did not complete")
    cases = json.loads(seed_path.read_text(encoding="utf-8")).get("cases")
    if not isinstance(cases, list) or len(cases) != 1:
        raise SystemExit("FAIL: seed.json must contain exactly one case")
    case = cases[0]

    # retries=1: this flow POSTS to the shared Slack channel, so a whole-flow
    # retry on a transient poll/5xx failure would post a duplicate alert. One
    # attempt only; a genuine transient failure fails the run cleanly.
    payload = run_debug(inputs=case["inputs"], timeout=300, retries=1)

    # Classification outcomes. Opaque identifiers (caseKey) compare
    # case-sensitively; enum-like values (severity, engineeringNeeded) do not.
    for name, expected in case["expected"].items():
        assert_named_equals(payload, name, expected, case_sensitive=(name in CASE_SENSITIVE))

    # The prompt requires the alert to include severity, correlationId, AND the
    # next steps. nextSteps is computed by the Script (not a named End out), so read
    # it from the ONE classification Script — the executed Script whose own output
    # carries the expected severity — so an unrelated Script can't supply it. Require
    # that exact string in the posted message.
    script_nodes = completed_node_ids_of_type(payload, "script")
    sev = case["expected"]["severity"]
    sev_scripts = [
        nid for nid in sorted(n for n in script_nodes if n)
        if normalized(find_node_output_value(payload, "severity", node_ids={nid})) == normalized(sev)
    ]
    if not sev_scripts:
        raise SystemExit(
            f"FAIL: no executed Script node produced the expected severity {sev!r} — "
            "cannot bind the nextSteps check to the classification Script"
        )
    # Bind to ONE node: the same Script that produced severity must ALSO produce
    # nextSteps, so the classification can't be split across cosmetic Scripts.
    next_steps = next(
        (ns for nid in sev_scripts for ns in [find_node_output_field(payload, "nextSteps", node_ids={nid})] if ns),
        None,
    )
    if not next_steps:
        raise SystemExit(
            "FAIL: the Script that produced the expected severity did not also produce "
            "a nextSteps value — the prompt requires classifying a short next-steps string"
        )

    # The Slack side effect, verified against the executed send's own response:
    # a real ts from an executed Slack SEND node, posted to the coding-agent-testing
    # channel, whose message carries every required field (correlationId, severity,
    # next steps), not just the id.
    assert_slack_message_posted(
        payload,
        "slackMessageId",
        expected_channel=SLACK_CHANNEL,
        must_contain=[case["inputs"]["correlationId"], case["expected"]["severity"], next_steps],
    )

    print(
        f"OK: {case['name']} completed — Sev1 + engineering classified, "
        "correlationId preserved, and the Slack alert was posted (real message ts)"
    )


if __name__ == "__main__":
    main()
