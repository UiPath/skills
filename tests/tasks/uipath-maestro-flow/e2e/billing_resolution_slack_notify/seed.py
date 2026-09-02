#!/usr/bin/env python3
"""Seed one DevCon billing-resolution case for the Slack-notify outcome eval.

Writes seed.json with a single case: the customer, the disputed invoice, and the
approved credit the inline agent drafts a resolution for. A fresh correlationId
per run keeps the posted Slack message and the caseKey assertion isolated across
runs. The invoice/credit are fixed oracles the grader checks in both the drafted
emailBody and the posted Slack message. The grader
(check_billing_resolution_slack_notify.py) runs `flow debug --inputs <inputs>`.
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
                "name": "northwind-resolution-slack-notify",
                "inputs": {
                    "customerName": "Northwind Traders",
                    "invoiceNumber": "MCS-2026-04872",
                    "creditAmount": 1610,
                    "correlationId": f"RESO-{run_id}",
                },
                "expected": {
                    "invoiceNumber": "MCS-2026-04872",
                    "creditAmount": 1610,
                    "caseKey": f"RESO-{run_id}",
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
