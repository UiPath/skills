#!/usr/bin/env python3
"""Seed path cases for the escalation-orchestrator outcome eval.

Each case pins the flow inputs that steer one branch and the outputs the grader
asserts. `expect_slack: true` means the case runs the escalation path and must
have actually posted a Slack alert (non-empty slackMessageId).

Start with the escalation → Slack path. Add more cases (informational, duplicate,
unknown-customer, multiple-match) here as coverage grows — the checker iterates
this list generically, so no checker change is needed to add a path.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4


def build_seed() -> dict:
    run_id = uuid4().hex[:12]
    return {
        "run_id": run_id,
        "cases": [
            {
                "name": "enterprise-production-down-sev1-escalation",
                "expect_slack": True,
                "inputs": {
                    "senderEmail": "jane.doe@acmecorp.com",
                    "senderDomain": "acmecorp.com",
                    "subject": "Production down: checkout API returning 500s",
                    "body": "Critical urgent outage since 09:15 UTC, all users blocked.",
                    "customerTier": "Enterprise",
                    "productionDown": True,
                    "workaroundAvailable": False,
                    "hasAttachments": False,
                    "customerMatchStatus": "single",
                    "isDuplicate": False,
                    "correlationId": f"ORCH-{run_id}-SEV1",
                },
                "expected": {
                    "escalationPath": "escalation",
                    "severity": "Sev1",
                    "engineeringNeeded": True,
                    "responseMode": "Draft",
                    "caseKey": f"ORCH-{run_id}-SEV1",
                },
            }
        ],
    }


def main() -> None:
    path = Path("seed.json")
    path.write_text(json.dumps(build_seed(), indent=2) + "\n", encoding="utf-8")
    print(f"seeded {path}")


if __name__ == "__main__":
    main()
