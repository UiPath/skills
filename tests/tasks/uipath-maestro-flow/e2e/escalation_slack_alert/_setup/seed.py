#!/usr/bin/env python3
"""Seed a Sev1 escalation case for the Slack-alert outcome eval.

Writes seed.json with one Enterprise / production-down / no-workaround case.
A fresh correlationId per run keeps the posted Slack message and the caseKey
assertion isolated across runs. The grader (check_escalation_slack_alert.py)
runs `flow debug --inputs <inputs>` and asserts both the classification outputs
and that a Slack message was actually posted.
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
                "name": "enterprise-production-down-sev1",
                "inputs": {
                    "senderEmail": "jane.doe@acmecorp.com",
                    "subject": "Production down: checkout API returning 500s",
                    "body": (
                        "Critical outage since 09:15 UTC. All checkout requests "
                        "are failing with HTTP 500 and orders are blocked."
                    ),
                    "customerTier": "Enterprise",
                    "productionDown": True,
                    "workaroundAvailable": False,
                    "correlationId": f"E2E-{run_id}-SEV1",
                },
                "expected": {
                    "severity": "Sev1",
                    "engineeringNeeded": True,
                    "caseKey": f"E2E-{run_id}-SEV1",
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
