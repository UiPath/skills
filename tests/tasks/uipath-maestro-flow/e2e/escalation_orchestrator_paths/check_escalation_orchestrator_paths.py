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
    assert_connector_send_identity,
    assert_decision_branches_reach,
    assert_distinct_branch_ends,
    assert_flow_uses_connector_target,
    assert_named_equals,
    assert_node_type_executed,
    assert_slack_message_posted,
    completed_connector_node_ids,
    completed_node_ids_of_type,
    find_node_output_value,
    normalized,
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
        # right channel, whose message carries this case's correlationId (exact)
        # AND its escalationPath (prompt line 65 requires escalationPath +
        # correlationId in every message). escalationPath is matched
        # separator/case-insensitively so the enum "unknown_customer" also matches
        # a rendered "unknown customer". The severity taxonomy (e.g.
        # "informational") is an internal label the prompt does NOT require in the
        # text, so it stays a named-out assertion, not message content.
        assert_slack_message_posted(
            payload,
            "slackMessageId",
            expected_channel=SLACK_CHANNEL,
            must_contain=case["inputs"]["correlationId"],
            must_contain_loose=[case["expected"]["escalationPath"]],
        )
    # The prompt requires ALL routing logic in ONE Script node. Bind the core
    # classification (escalationPath + severity) to a single EXECUTED Script node:
    # a flow that computes routing in Decision/End expressions with no Script, or
    # splits escalationPath and severity across two nodes, has no single Script
    # carrying both and fails here. (engineeringNeeded/responseMode are trivial
    # derivations already verified as named outs above.)
    script_nodes = completed_node_ids_of_type(payload, "script")
    ep, sv = case["expected"]["escalationPath"], case["expected"]["severity"]
    classifier_candidates = {
        nid for nid in script_nodes if nid
        and normalized(find_node_output_value(payload, "escalationPath", node_ids={nid})) == normalized(ep)
        and normalized(find_node_output_value(payload, "severity", node_ids={nid})) == normalized(sv)
    }
    if not classifier_candidates:
        raise SystemExit(
            f"FAIL: {case['name']}: no single executed Script computed both escalationPath "
            f"({ep!r}) and severity ({sv!r}) — the prompt requires one classifier Script"
        )
    # The task is tagged node:decision: routing must go through a Decision that
    # actually executed — a disconnected Decision or a Script->Slack shortcut fails.
    assert_node_type_executed(payload, "core.logic.decision")
    fired = completed_connector_node_ids(payload, SLACK_KEY)
    executed_decisions = completed_node_ids_of_type(payload, "core.logic.decision")
    print(f"OK: {case['name']} produced the expected outcome"
          + (" + Slack message posted" if case.get("expect_slack") else ""))
    return fired, executed_decisions, classifier_candidates


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
    per_case_decisions: list = []
    per_case_classifiers: list = []
    for case in cases:
        fired, decisions, classifiers = verify_case(case)
        is_escalation = case["expected"]["escalationPath"] == "escalation"
        (escalation_nodes if is_escalation else triage_nodes).update(fired)
        per_case_decisions.append(decisions)
        per_case_classifiers.append(classifiers)

    # ONE classifier Script must classify EVERY case (prompt: ALL routing logic in
    # one Script). Intersect the per-case candidates: a flow with path-specific
    # Script nodes (a different classifier per case) has an empty intersection and fails.
    common_classifier = set.intersection(*per_case_classifiers) if per_case_classifiers else set()
    if not common_classifier:
        raise SystemExit(
            "FAIL: no single Script node classified every case — the prompt requires ALL "
            "routing logic in ONE Script, but the cases were classified by different "
            f"(path-specific) Scripts (per-case candidates: {[sorted(c) for c in per_case_classifiers]})"
        )
    print(f"OK: one classifier Script handled all cases: {sorted(common_classifier)}")

    # Prompt requires each Slack node's error port wired to a handler for graceful
    # degradation, and every send to go out as `user` — assert both structurally so
    # a flow omitting them can't get full credit.
    assert_connector_error_handlers(SLACK_KEY, native_op_hint="send-message-to-channel")
    assert_connector_send_identity(SLACK_KEY, expected="user", native_op_hint="send-message-to-channel")

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
    # And prove those two nodes are the Decision's OWN outgoing branches — routed by
    # ONE Decision that executed in EVERY case. The escalation-vs-triage split runs
    # on every email, so the routing Decision is in the intersection of the
    # completed-Decision sets across ALL cases. Intersecting across every case (not
    # a per-group union) blocks the flow that routes two cases through the real
    # Decision and the remaining five through other constructs.
    routing_decisions = set.intersection(*per_case_decisions) if per_case_decisions else set()
    assert_decision_branches_reach(
        escalation_nodes, triage_nodes, executed_decision_ids=routing_decisions
    )

    # The prompt requires TWO End nodes — one per branch. Each Slack branch must
    # reach its OWN End; a flow that merges both sends into a single shared End fails.
    assert_distinct_branch_ends(escalation_nodes, triage_nodes)
    print(
        f"OK: a Decision routes escalation vs triage through separate branches "
        f"(escalation={sorted(escalation_nodes)}, triage={sorted(triage_nodes)})"
    )


if __name__ == "__main__":
    main()
