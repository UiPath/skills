#!/usr/bin/env python3
"""pre_run: seed a Sev1 escalation case for the Jira-ticket outcome eval.

No live issue is created here; the agent's flow creates it when the grader runs
`flow debug`. The unique tag lives in the correlationId, which the flow must put
in the Jira issue summary, so the check can prove the ticket the flow created
(not a fabricated key) really exists in Jira.

Resolving the connection and the CE project's Task type here doubles as the
preflight: when the Jira connection cannot read the project (403 Forbidden on
2026-11-17 15:00 and the 2026-11-18 nightlies), the run ends as ERROR before the
agent starts, instead of a FAILURE scored against the agent.
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
        "subject": "Production down: checkout API returning 500s",
        "body": "Critical urgent outage, all users blocked.",
        "customerTier": "Enterprise",
        "productionDown": True,
        "workaroundAvailable": False,
        "correlationId": correlation,
    },
    # Enterprise, production down, no workaround: Sev1, engineering needed.
    "expected": {"severity": "Sev1", "engineeringNeeded": True, "caseKey": correlation},
}
Path("seed.json").write_text(json.dumps(seed, indent=2) + "\n", encoding="utf-8")
print(f"OK: wrote seed (correlationId={correlation}, project={jira_is.PROJECT_KEY}, issuetype={seed['issuetype_id']})")
