#!/usr/bin/env python3
"""Seed the escalation cases for the Slack-alert outcome eval.

Writes seed.json with two cases the grader runs through `flow debug --inputs`:

- Enterprise, production down, no workaround: Sev1, engineering needed.
- Standard, production down, no workaround: Sev3, no engineering. Sev1 needs
  the Enterprise tier and Sev2 needs a workaround, so this case is Sev3. It
  catches a classifier that ignores the tier or always answers Sev1.

A fresh correlationId per run ties each posted Slack message and the caseKey
assertion to this run.
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
            },
            {
                "name": "standard-production-down-sev3",
                "inputs": {
                    "senderEmail": "sam.lee@smallshop.com",
                    "subject": "Our storefront is down",
                    "body": "Every visitor gets an error page and we have no workaround.",
                    "customerTier": "Standard",
                    "productionDown": True,
                    "workaroundAvailable": False,
                    "correlationId": f"E2E-{run_id}-SEV3",
                },
                "expected": {
                    "severity": "Sev3",
                    "engineeringNeeded": False,
                    "caseKey": f"E2E-{run_id}-SEV3",
                },
            },
        ],
    }


def main() -> None:
    path = Path("seed.json")
    path.write_text(json.dumps(build_seed(), indent=2) + "\n", encoding="utf-8")
    print(f"seeded {path}")


if __name__ == "__main__":
    main()
