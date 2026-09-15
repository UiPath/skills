#!/usr/bin/env python3
"""Seed one DevCon billing-dispute case for the Slack-alert outcome eval.

Writes seed.json with a single disputed-invoice case. The invoice number is
supplied in a messy form (wrong casing, missing "MCS-" prefix) so the flow's
normalization + real Data Service query are actually exercised — the seeded
invoice MCS-2026-04872 has exactly 8 line items, a deterministic oracle. A fresh
correlationId per run keeps the posted Slack message and the caseKey assertion
isolated across runs. The grader (check_billing_dispute_slack_alert.py) runs
`flow debug --inputs <inputs>` and asserts both the Data Service outcome and
that a Slack message was actually posted.
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
                "name": "disputed-invoice-messy-input",
                "inputs": {
                    "invoiceNumber": "mcs-2026-04872",
                    "correlationId": f"BILL-{run_id}",
                },
                "expected": {
                    "matchedInvoiceNumber": "MCS-2026-04872",
                    "lineItemCount": 8,
                    "caseKey": f"BILL-{run_id}",
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
