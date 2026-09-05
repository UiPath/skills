#!/usr/bin/env python3
"""pre_run: seed one Sev1 escalation case for the BPMN outcome eval.

No live record is created here — the agent's process creates the Jira issue
and Slack message when the grader runs `uip maestro bpmn debug`. The unique
tag lives in the correlationId, which the process must echo into the Jira
summary and the Slack text, so the checker can prove the records the process
created (not fabricated identifiers) really exist in the tenant.
"""

from __future__ import annotations

import json
import secrets
from pathlib import Path

import escalation_is

tag = secrets.token_hex(4)
correlation = f"ESC-BPMN-{tag}"
seed = {
    "tag": tag,
    "correlationId": correlation,
    "inputs": {
        "customerTier": "Enterprise",
        "serviceState": "Unavailable",
        "workaroundAvailable": False,
        "correlationId": correlation,
        "jiraProjectKey": escalation_is.JIRA_PROJECT_KEY,
        "jiraIssueTypeId": escalation_is.JIRA_ISSUE_TYPE_ID,
        "slackChannelId": escalation_is.SLACK_CHANNEL_ID,
    },
    # jiraIssueKey is asserted against the created issue's actual key, so only
    # the deterministic outputs are seeded here.
    "expected": {"severity": "Sev1", "caseKey": correlation},
}
Path("seed.json").write_text(json.dumps(seed, indent=2) + "\n", encoding="utf-8")
print(
    f"OK: wrote seed (correlationId={correlation}, "
    f"project={escalation_is.JIRA_PROJECT_KEY}, "
    f"channel={escalation_is.SLACK_CHANNEL_ID})"
)
