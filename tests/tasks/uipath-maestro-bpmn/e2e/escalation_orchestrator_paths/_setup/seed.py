#!/usr/bin/env python3
"""Seed path cases for the escalation-orchestrator outcome eval.

Each case pins the flow inputs that steer one branch and the outputs the grader
asserts. `expect_slack: true` means the run must have actually posted a Slack
message (escalation alert on the escalation path, triage notice on the triage
paths) — a non-empty slackMessageId proves it.

Every expected value below was verified by running the reference orchestrator
through `uip maestro flow debug --inputs` on codereval/alpha. The checker
iterates this list generically, so new paths (e.g. multiple-match, missing-domain,
Sev2-with-attachments) drop in here with no checker change.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

_COMMON = {
    "senderEmail": "jane.doe@acmecorp.com",
    "senderDomain": "acmecorp.com",
    "hasAttachments": False,
}


def _case(name, run_id, suffix, overrides, expected, expect_slack):
    corr = f"ORCH-{run_id}-{suffix}"
    inputs = {
        **_COMMON,
        "subject": "",
        "body": "",
        "customerTier": "Standard",
        "productionDown": False,
        "workaroundAvailable": False,
        "customerMatchStatus": "single",
        "isDuplicate": False,
        "correlationId": corr,
        **overrides,
    }
    return {
        "name": name,
        "expect_slack": expect_slack,
        "inputs": inputs,
        "expected": {**expected, "caseKey": corr},
    }


def build_seed() -> dict:
    r = uuid4().hex[:12]
    cases = [
        # ── Escalation paths (Slack escalation alert) ──────────────────────
        _case(
            # Deliberately STANDARD tier: the orchestrator's Sev1 is tier-independent
            # (productionDown AND NOT workaroundAvailable). A classifier that wrongly
            # gates Sev1 on Enterprise (e.g. copied from the slack_alert task) would
            # misclassify this Standard outage and fail.
            "sev1-standard-production-down", r, "SEV1",
            {"subject": "Production down: checkout 500s", "body": "Critical urgent outage, all users blocked",
             "customerTier": "Standard", "productionDown": True, "workaroundAvailable": False},
            {"escalationPath": "escalation", "severity": "Sev1", "engineeringNeeded": True, "responseMode": "Draft"},
            True,
        ),
        _case(
            "sev2-degraded-with-workaround", r, "SEV2",
            {"subject": "Degraded checkout", "body": "Slow but a workaround exists",
             "productionDown": True, "workaroundAvailable": True},
            {"escalationPath": "escalation", "severity": "Sev2", "engineeringNeeded": True, "responseMode": "Draft"},
            True,
        ),
        _case(
            "sev3-no-production-impact", r, "SEV3",
            {"subject": "Report formatting off", "body": "The export looks wrong"},
            {"escalationPath": "escalation", "severity": "Sev3", "engineeringNeeded": False, "responseMode": "Draft"},
            True,
        ),
        # ── Triage paths (Slack triage notice) ─────────────────────────────
        _case(
            "duplicate-escalation", r, "DUP",
            {"subject": "Prod down", "body": "urgent", "customerTier": "Enterprise",
             "productionDown": True, "workaroundAvailable": False, "isDuplicate": True},
            {"escalationPath": "duplicate", "severity": "informational", "engineeringNeeded": False, "responseMode": "None"},
            True,
        ),
        _case(
            "unknown-customer", r, "UNK",
            {"subject": "Help", "body": "an issue", "customerMatchStatus": "none"},
            {"escalationPath": "unknown_customer", "severity": "informational", "engineeringNeeded": False, "responseMode": "None"},
            True,
        ),
        _case(
            "missing-domain", r, "MD",
            {"subject": "Help", "body": "an issue", "senderDomain": ""},
            {"escalationPath": "missing_domain", "severity": "informational", "engineeringNeeded": False, "responseMode": "None"},
            True,
        ),
        _case(
            "multiple-matches", r, "MULTI",
            {"subject": "Help", "body": "an issue", "customerMatchStatus": "multiple"},
            {"escalationPath": "multiple_matches", "severity": "informational", "engineeringNeeded": False, "responseMode": "None"},
            True,
        ),
    ]
    return {"run_id": r, "cases": cases}


def main() -> None:
    seed = build_seed()
    path = Path("seed.json")
    path.write_text(json.dumps(seed, indent=2) + "\n", encoding="utf-8")
    print(f"seeded {path} with {len(seed['cases'])} path cases")


if __name__ == "__main__":
    main()
