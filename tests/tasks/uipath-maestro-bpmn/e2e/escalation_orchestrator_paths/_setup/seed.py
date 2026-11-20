#!/usr/bin/env python3
"""Seed path cases for the escalation-orchestrator outcome eval.

Each case pins the process inputs that steer one branch and the outputs the
grader asserts. Every case posts one Slack message (the escalation alert or
the triage notice); check_orchestrator_run.py runs each case under `uip
maestro bpmn debug --inputs` and requires slackMessageId to equal the ts in
the Slack step's own response. It iterates this list generically, so a new
path drops in here with no checker change. The last cases trip several routing
rules at once; the winner is the first rule in the prompt's order.
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


def _case(name, run_id, suffix, overrides, expected):
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
        ),
        _case(
            "sev2-degraded-with-workaround", r, "SEV2",
            {"subject": "Degraded checkout", "body": "Slow but a workaround exists",
             "productionDown": True, "workaroundAvailable": True},
            {"escalationPath": "escalation", "severity": "Sev2", "engineeringNeeded": True, "responseMode": "Draft"},
        ),
        _case(
            "sev3-no-production-impact", r, "SEV3",
            {"subject": "Report formatting off", "body": "The export looks wrong"},
            {"escalationPath": "escalation", "severity": "Sev3", "engineeringNeeded": False, "responseMode": "None"},
        ),
        _case(
            # productionDown False with a workaround: pins that Sev2 needs
            # productionDown, so a classifier keyed on workaroundAvailable alone fails.
            "sev3-workaround-without-outage", r, "SEV3WA",
            {"subject": "Minor glitch", "body": "A workaround exists",
             "productionDown": False, "workaroundAvailable": True},
            {"escalationPath": "escalation", "severity": "Sev3", "engineeringNeeded": False, "responseMode": "None"},
        ),
        # ── Triage paths (Slack triage notice) ─────────────────────────────
        _case(
            "duplicate-escalation", r, "DUP",
            {"subject": "Prod down", "body": "urgent", "customerTier": "Enterprise",
             "productionDown": True, "workaroundAvailable": False, "isDuplicate": True},
            {"escalationPath": "duplicate", "severity": "informational", "engineeringNeeded": False, "responseMode": "None"},
        ),
        _case(
            "unknown-customer", r, "UNK",
            {"subject": "Help", "body": "an issue", "customerMatchStatus": "none"},
            {"escalationPath": "unknown_customer", "severity": "informational", "engineeringNeeded": False, "responseMode": "None"},
        ),
        _case(
            "missing-domain", r, "MD",
            {"subject": "Help", "body": "an issue", "senderDomain": ""},
            {"escalationPath": "missing_domain", "severity": "informational", "engineeringNeeded": False, "responseMode": "None"},
        ),
        _case(
            "multiple-matches", r, "MULTI",
            {"subject": "Help", "body": "an issue", "customerMatchStatus": "multiple"},
            {"escalationPath": "multiple_matches", "severity": "informational", "engineeringNeeded": False, "responseMode": "None"},
        ),
        # ── Overlaps: the first rule in the prompt's order wins ────────────
        _case(
            "missing-domain-beats-unknown-customer", r, "MDUNK",
            {"subject": "Help", "body": "an issue", "senderDomain": "", "customerMatchStatus": "none"},
            {"escalationPath": "missing_domain", "severity": "informational", "engineeringNeeded": False, "responseMode": "None"},
        ),
        _case(
            "missing-domain-beats-multiple-matches", r, "MDMULTI",
            {"subject": "Help", "body": "an issue", "senderDomain": "", "customerMatchStatus": "multiple"},
            {"escalationPath": "missing_domain", "severity": "informational", "engineeringNeeded": False, "responseMode": "None"},
        ),
        _case(
            "unknown-customer-beats-duplicate", r, "UNKDUP",
            {"subject": "Prod down", "body": "urgent", "customerMatchStatus": "none", "isDuplicate": True,
             "productionDown": True, "workaroundAvailable": False},
            {"escalationPath": "unknown_customer", "severity": "informational", "engineeringNeeded": False, "responseMode": "None"},
        ),
        _case(
            "multiple-matches-beats-duplicate", r, "MULTIDUP",
            {"subject": "Prod down", "body": "urgent", "customerMatchStatus": "multiple", "isDuplicate": True,
             "customerTier": "Enterprise", "productionDown": True},
            {"escalationPath": "multiple_matches", "severity": "informational", "engineeringNeeded": False, "responseMode": "None"},
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
