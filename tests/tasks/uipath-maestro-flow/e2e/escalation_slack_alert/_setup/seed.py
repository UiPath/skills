#!/usr/bin/env python3
"""Seed the escalation cases for the Slack-alert outcome eval.

The prompt names no variables, so each case's inputs are keyed by MEANING
(the grader maps them onto whatever inputs the agent declared) and its
expected results are values the grader looks for among the declared outputs.
The prompt's severity rules:

- Sev1: an Enterprise customer's production is down with no workaround.
- Sev2: production is down but there is a workaround.
- Sev3: everything else, including non-Enterprise customers who are down
  without a workaround.
- Engineering is needed for Sev1 and Sev2.

Three cases, one per severity. The Sev3 case is a Standard-tier outage with
no workaround, the case the prompt calls out, so a classifier that ignores
the tier fails it. The Sev2 case is Standard tier too: a workaround makes it
Sev2 whatever the tier.

A fresh case reference per run ties each posted Slack message to this run.
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
                "name": "enterprise-down-no-workaround-sev1",
                "inputs": {
                    "senderEmail": "jane.doe@acmecorp.com",
                    "subject": "Production down: checkout API returning 500s",
                    "body": (
                        "Critical outage since 09:15 UTC. All checkout requests "
                        "are failing with HTTP 500 and orders are blocked."
                    ),
                    "tier": "Enterprise",
                    "productionDown": True,
                    "workaround": False,
                    "caseRef": f"ESC-{run_id}-1",
                },
                "expected": {"severity": "Sev1", "engineering": True},
            },
            {
                "name": "standard-down-no-workaround-sev3",
                "inputs": {
                    "senderEmail": "sam.lee@smallshop.com",
                    "subject": "Our storefront is down",
                    "body": "Every visitor gets an error page and we have no workaround.",
                    "tier": "Standard",
                    "productionDown": True,
                    "workaround": False,
                    "caseRef": f"ESC-{run_id}-3",
                },
                "expected": {"severity": "Sev3", "engineering": False},
            },
            {
                "name": "standard-down-with-workaround-sev2",
                "inputs": {
                    "senderEmail": "li.wei@northwind.com",
                    "subject": "Order sync failing",
                    "body": "Orders stopped syncing; we re-enter them by hand for now.",
                    "tier": "Standard",
                    "productionDown": True,
                    "workaround": True,
                    "caseRef": f"ESC-{run_id}-2",
                },
                "expected": {"severity": "Sev2", "engineering": True},
            },
        ],
    }


def main() -> None:
    path = Path("seed.json")
    path.write_text(json.dumps(build_seed(), indent=2) + "\n", encoding="utf-8")
    print(f"seeded {path}")


if __name__ == "__main__":
    main()
