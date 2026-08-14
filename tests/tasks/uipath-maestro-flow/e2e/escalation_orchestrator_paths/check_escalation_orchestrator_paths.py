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
    assert_connector_error_handlers,
    assert_decision_branches_reach,
    assert_flow_uses_connector_target,
    assert_named_equals,
    assert_node_type_executed,
    assert_slack_message_posted,
    completed_connector_node_ids,
    completed_node_ids_of_type,
    run_debug,
)

SLACK_KEY = "uipath-salesforce-slack"
SLACK_CHANNEL = "C0B2FDZD1M3"  # coding-agent-testing
CASE_SENSITIVE = {"caseKey", "jiraIssueKey"}  # opaque ids — exact-case match


def verify_case(case: dict) -> tuple:
    # retries=1: seven cases run serially, so a bounded per-case budget keeps the
    # total within the criterion timeout; a genuine transient failure fails cleanly.
    payload = run_debug(inputs=case["inputs"], timeout=300, retries=1)
    for name, expected in case["expected"].items():
        assert_named_equals(payload, name, expected, case_sensitive=(name in CASE_SENSITIVE))
    if case.get("expect_slack"):
        # Real ts tied to the executed Slack SEND node's response, posted to the
        # right channel, whose message carries this case's correlationId. The
        # orchestrator's severity taxonomy (e.g. "informational") is an internal
        # classification label its prompt does not require verbatim in the alert
        # text, so it is asserted as a named `out` (above), not as message content.
        # Routing (escalation vs triage) is verified separately via the
        # decision-branch check below.
        assert_slack_message_posted(
            payload,
            "slackMessageId",
            expected_channel=SLACK_CHANNEL,
            must_contain=case["inputs"]["correlationId"],
        )
    # The task is tagged node:decision: routing must go through a Decision that
    # actually executed — a disconnected Decision or a Script->Slack shortcut fails.
    assert_node_type_executed(payload, "core.logic.decision")
    fired = completed_connector_node_ids(payload, SLACK_KEY)
    executed_decisions = completed_node_ids_of_type(payload, "core.logic.decision")
    print(f"OK: {case['name']} produced the expected outcome"
          + (" + Slack message posted" if case.get("expect_slack") else ""))
    return fired, executed_decisions


def main() -> None:
    # The escalation alert must go through the real Slack connector.
    assert_flow_uses_connector_target(SLACK_KEY)

    seed_path = Path("seed.json")
    if not seed_path.is_file():
        raise SystemExit("FAIL: seed.json is missing; pre_run did not complete")
    cases = json.loads(seed_path.read_text(encoding="utf-8")).get("cases")
    if not isinstance(cases, list) or not cases:
        raise SystemExit("FAIL: seed.json must contain at least one case")

    escalation_nodes: set = set()
    triage_nodes: set = set()
    executed_decisions: set = set()
    for case in cases:
        fired, decisions = verify_case(case)
        target = escalation_nodes if case["expected"]["escalationPath"] == "escalation" else triage_nodes
        target.update(fired)
        executed_decisions.update(decisions)

    # Prompt requires each Slack node's error port wired to a handler for graceful
    # degradation — assert that structurally so a flow omitting it can't get full credit.
    assert_connector_error_handlers(SLACK_KEY, native_op_hint="send-message-to-channel")

    # The Decision must genuinely branch: escalation and triage paths post via
    # DIFFERENT Slack nodes. A single dynamic Slack node behind a cosmetic
    # always-true Decision would make these sets overlap.
    if not escalation_nodes or not triage_nodes:
        raise SystemExit(
            "FAIL: expected both escalation and triage cases to fire a Slack node "
            f"(escalation={escalation_nodes}, triage={triage_nodes})"
        )
    overlap = escalation_nodes & triage_nodes
    if overlap:
        raise SystemExit(
            f"FAIL: escalation and triage cases fired the SAME Slack node(s) {overlap} — "
            "the Decision does not route to two distinct branches"
        )
    # And prove those two nodes are the Decision's OWN outgoing branches — and that
    # the routing Decision is one that ACTUALLY EXECUTED (not a second, unexecuted
    # Decision that merely has the two source edges behind a cosmetic always-true one).
    assert_decision_branches_reach(
        escalation_nodes, triage_nodes, executed_decision_ids=executed_decisions
    )
    print(
        f"OK: a Decision routes escalation vs triage through separate branches "
        f"(escalation={sorted(escalation_nodes)}, triage={sorted(triage_nodes)})"
    )


if __name__ == "__main__":
    main()
