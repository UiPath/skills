#!/usr/bin/env python3
"""Seed isolated business inputs for the interactive escalation eval."""

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
                "name": "enterprise-production-down",
                "inputs": {
                    "customerTier": "Enterprise",
                    "productionDown": True,
                    "workaroundAvailable": False,
                    "businessImpact": "All production users are blocked",
                    "correlationId": f"E2E-{run_id}-SEV1",
                },
                "expected": {
                    "severity": "Sev1",
                    "engineeringNeeded": True,
                    "responseMode": "Draft",
                    "caseKey": f"E2E-{run_id}-SEV1",
                },
            },
            {
                "name": "informational-follow-up",
                "inputs": {
                    "customerTier": "Standard",
                    "productionDown": False,
                    "workaroundAvailable": True,
                    "businessImpact": "Informational product question only",
                    "correlationId": f"E2E-{run_id}-SEV3",
                },
                "expected": {
                    "severity": "Sev3",
                    "engineeringNeeded": False,
                    "responseMode": "Draft",
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
