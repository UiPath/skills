#!/usr/bin/env python3
"""pre_run: seed a Sev1 escalation case for the Jira-ticket outcome eval.

No live issue is created here; the agent's process creates it when
check_jira_ticket_run.py runs `uip maestro bpmn debug`. The unique tag lives in
the correlationId, which the process must echo into the Jira issue summary, so
the check can prove the ticket the process created (not a fabricated key)
really exists in Jira.
"""

from __future__ import annotations

import json
import secrets
from pathlib import Path

import jira_is

tag = secrets.token_hex(4)
correlation = f"ESC-JIRA-{tag}"
conn = jira_is.connection_id()
seed = {
    "tag": tag,
    "project_key": jira_is.PROJECT_KEY,
    "issuetype_id": jira_is.issuetype_id(conn),
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
}
Path("seed.json").write_text(json.dumps(seed, indent=2) + "\n", encoding="utf-8")
print(f"OK: wrote seed (correlationId={correlation}, project={jira_is.PROJECT_KEY}, issuetype={jira_is.issuetype_id(conn)})")
