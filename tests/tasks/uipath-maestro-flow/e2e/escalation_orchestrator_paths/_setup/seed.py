#!/usr/bin/env python3
"""Seed path cases for the escalation-orchestrator outcome eval.

The prompt names no variables, so each case's inputs are keyed by MEANING
(the grader maps them onto whatever inputs the agent declared) and its
expected results are values the grader looks for among the declared outputs.
`match` is the state the prompt describes ("one", "none" or "several"); the
grader turns it into the value the agent's flow compares against.

The prompt's rules, in its order:

- path: no sender domain -> "missing_domain"; no matching customer ->
  "unknown_customer"; several matching customers -> "multiple_matches"; a
  duplicate -> "duplicate"; otherwise "escalation".
- escalation severity ignores the tier: Sev1 when production is down with no
  workaround, Sev2 when it is down with a workaround, Sev3 when it is not
  down. Engineering is needed for Sev1 and Sev2, and the response is drafted.
- anything that is not an escalation is "informational", with no
  engineering and response mode "None".

Each triage case also meets every LATER condition in that order, so a flow
that checks them in another order takes the wrong path. The missing-domain
sender has no domain in the email address either, so a flow that derives the
domain from the address still sees none. The Sev1 case is Standard tier and
the Sev3 case Enterprise, so a classifier that reads the tier fails.

Sev3's response mode is not pinned: "we'll draft a response" follows the
Sev1/Sev2 engineering sentence, so "None" for Sev3 is a fair reading too.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

_COMMON = {
    "senderEmail": "jane.doe@acmecorp.com",
    "senderDomain": "acmecorp.com",
    "subject": "Help with our account",
    "body": "We have a question about our service.",
    "tier": "Standard",
    "productionDown": False,
    "workaround": False,
    "attachments": False,
    "match": "one",
    "duplicate": False,
}
_TRIAGE = {"severity": "informational", "engineering": False, "responseMode": "None"}


def _case(name, run_id, suffix, overrides, expected):
    return {
        "name": name,
        "inputs": {**_COMMON, **overrides, "caseRef": f"ORCH-{run_id}-{suffix}"},
        "expected": expected,
    }


def build_seed() -> dict:
    r = uuid4().hex[:12]
    cases = [
        # ── Escalations (the alert) ─────────────────────────────────────────
        _case(
            "sev1-standard-down-no-workaround", r, "SEV1",
            {"subject": "Production down: checkout 500s", "body": "All users are blocked.",
             "productionDown": True, "workaround": False},
            {"path": "escalation", "severity": "Sev1", "engineering": True, "responseMode": "Draft"},
        ),
        _case(
            "sev2-down-with-workaround", r, "SEV2",
            {"subject": "Checkout degraded", "body": "Slow, but retrying works for now.",
             "productionDown": True, "workaround": True, "attachments": True},
            {"path": "escalation", "severity": "Sev2", "engineering": True, "responseMode": "Draft"},
        ),
        _case(
            "sev3-enterprise-not-down", r, "SEV3",
            {"subject": "Report formatting off", "body": "The monthly export looks wrong.",
             "tier": "Enterprise"},
            {"path": "escalation", "severity": "Sev3", "engineering": False,
             "responseMode": ["Draft", "None"]},
        ),
        # ── Triage (the notice), each also meeting every later condition ────
        _case(
            "duplicate-of-an-outage", r, "DUP",
            {"subject": "Prod down", "body": "Still down, see my earlier email.", "tier": "Enterprise",
             "productionDown": True, "workaround": False, "duplicate": True},
            {"path": "duplicate", **_TRIAGE},
        ),
        _case(
            "multiple-matches-and-duplicate", r, "MULTI",
            {"subject": "Prod down", "body": "urgent", "productionDown": True,
             "match": "several", "duplicate": True},
            {"path": "multiple_matches", **_TRIAGE},
        ),
        _case(
            "unknown-customer-and-duplicate", r, "UNK",
            {"subject": "Prod down", "body": "urgent", "productionDown": True,
             "match": "none", "duplicate": True},
            {"path": "unknown_customer", **_TRIAGE},
        ),
        _case(
            "missing-domain-no-match-duplicate", r, "MD",
            {"senderEmail": "jane.doe", "senderDomain": "", "productionDown": True,
             "match": "none", "duplicate": True},
            {"path": "missing_domain", **_TRIAGE},
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
