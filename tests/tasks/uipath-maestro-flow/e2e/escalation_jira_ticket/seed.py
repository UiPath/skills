#!/usr/bin/env python3
"""pre_run: seed a Sev1 escalation case for the Jira-ticket outcome eval.

No live issue is created here — the agent's flow creates it when the grader runs
`flow debug`. The unique tag lives in the correlationId, which the flow must echo
into the Jira issue summary, so the check can prove the ticket the flow created
(not a fabricated key) really exists in Jira.
"""

from __future__ import annotations

import json
import secrets
from pathlib import Path

import jira_is

tag = secrets.token_hex(4)
correlation = f"ESC-JIRA-{tag}"
seed = {
    "tag": tag,
    "project_key": jira_is.PROJECT_KEY,
    "issuetype_id": jira_is.ISSUETYPE_ID,
    "correlationId": correlation,
    "inputs": {
        "senderEmail": "jane.doe@acmecorp.com",
        "senderDomain": "acmecorp.com",
        "subject": "Production down: checkout API returning 500s",
        "body": "Critical urgent outage, all users blocked.",
        "customerTier": "Enterprise",
        "productionDown": True,
        "workaroundAvailable": False,
        "hasAttachments": False,
        "customerMatchStatus": "single",
        "isDuplicate": False,
        "correlationId": correlation,
    },
    "expected": {"severity": "Sev1", "caseKey": correlation},
    # Classification the Script must compute but the prompt does not map to a named
    # End out — verified against the Script node's intermediate output. Sev1 (prod
    # down, no workaround) ⇒ engineeringNeeded true.
    "expected_script": {"engineeringNeeded": True},
}
Path("seed.json").write_text(json.dumps(seed, indent=2) + "\n", encoding="utf-8")
print(f"OK: wrote seed (correlationId={correlation}, project={jira_is.PROJECT_KEY}, issuetype={jira_is.ISSUETYPE_ID})")
