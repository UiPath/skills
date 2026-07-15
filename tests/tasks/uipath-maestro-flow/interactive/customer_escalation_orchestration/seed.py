#!/usr/bin/env python3
"""Seed deterministic business cases for the full escalation orchestration eval."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4


def _case_key(run_id: str, label: str) -> str:
    return f"E2E-{run_id}-{label}"


def build_seed() -> dict:
    run_id = uuid4().hex[:12]
    return {
        "run_id": run_id,
        "cases": [
            {
                "name": "enterprise-sev1-new-issue",
                "inputs": {
                    "senderEmail": "ava.chen@northwind.example",
                    "subject": "Production outage for checkout",
                    "body": "Enterprise customer Northwind has checkout fully down. No workaround is available.",
                    "attachmentsJson": json.dumps(
                        [
                            {
                                "fileName": "outage-log.txt",
                                "mimeType": "text/plain",
                                "bytes": 2048,
                            }
                        ],
                        separators=(",", ":"),
                    ),
                    "salesforceMatchesJson": json.dumps(
                        [
                            {
                                "accountId": "001NW",
                                "accountName": "Northwind",
                                "tier": "Enterprise",
                                "contactId": "003AVA",
                            }
                        ],
                        separators=(",", ":"),
                    ),
                    "salesforceOpenCasesJson": "[]",
                    "jiraMatchesJson": "[]",
                    "jiraAvailable": True,
                    "severityAgentJson": json.dumps(
                        {
                            "severity": "Sev1",
                            "rationale": "Production unavailable and no workaround.",
                        },
                        separators=(",", ":"),
                    ),
                    "draftAgentJson": json.dumps(
                        {
                            "subject": "Draft acknowledgement for checkout outage",
                            "body": "We are triaging the checkout outage with engineering and will update you shortly.",
                        },
                        separators=(",", ":"),
                    ),
                    "correlationId": _case_key(run_id, "A19"),
                },
                "expected": {
                    "accountId": "001NW",
                    "contactId": "003AVA",
                    "severity": "Sev1",
                    "engineeringHandoff": True,
                    "route": "EngineeringEscalation",
                    "jiraAction": "Create",
                    "jiraIssueKey": "NEW",
                    "driveAction": "SaveSummaryAndAttachments",
                    "outlookAction": "DraftAcknowledgement",
                    "slackAction": "PostSev1Alert",
                    "exceptionCode": "None",
                    "caseKey": _case_key(run_id, "A19"),
                },
                "draft_contains": ["checkout outage", "engineering"],
            },
            {
                "name": "duplicate-sev2-existing-jira",
                "inputs": {
                    "senderEmail": "ops@contoso.example",
                    "subject": "API degraded after deploy",
                    "body": "Contoso is degraded but a cached workflow workaround is available.",
                    "attachmentsJson": "[]",
                    "salesforceMatchesJson": json.dumps(
                        [
                            {
                                "accountId": "001CO",
                                "accountName": "Contoso",
                                "tier": "Strategic",
                                "contactId": "003OPS",
                            }
                        ],
                        separators=(",", ":"),
                    ),
                    "salesforceOpenCasesJson": json.dumps(
                        [{"caseNumber": "500-778", "subject": "API degraded"}],
                        separators=(",", ":"),
                    ),
                    "jiraMatchesJson": json.dumps(
                        [{"key": "CE-2042", "summary": "Contoso API degraded"}],
                        separators=(",", ":"),
                    ),
                    "jiraAvailable": True,
                    "severityAgentJson": json.dumps(
                        {
                            "severity": "Sev2",
                            "rationale": "Production degraded with workaround.",
                        },
                        separators=(",", ":"),
                    ),
                    "draftAgentJson": json.dumps(
                        {
                            "subject": "Draft update for API degradation",
                            "body": "We found the existing engineering ticket and will keep the acknowledgement in draft for review.",
                        },
                        separators=(",", ":"),
                    ),
                    "correlationId": _case_key(run_id, "B42"),
                },
                "expected": {
                    "accountId": "001CO",
                    "contactId": "003OPS",
                    "severity": "Sev2",
                    "engineeringHandoff": True,
                    "route": "DuplicateEscalation",
                    "jiraAction": "UpdateExisting",
                    "jiraIssueKey": "CE-2042",
                    "driveAction": "SaveSummary",
                    "outlookAction": "DraftAcknowledgement",
                    "slackAction": "PostEngineeringUpdate",
                    "exceptionCode": "None",
                    "caseKey": _case_key(run_id, "B42"),
                },
                "draft_contains": ["existing engineering ticket", "draft"],
            },
            {
                "name": "unknown-customer-no-salesforce-match",
                "inputs": {
                    "senderEmail": "newbuyer@unknown.example",
                    "subject": "Question about onboarding",
                    "body": "We want to understand pricing and onboarding timelines.",
                    "attachmentsJson": "[]",
                    "salesforceMatchesJson": "[]",
                    "salesforceOpenCasesJson": "[]",
                    "jiraMatchesJson": "[]",
                    "jiraAvailable": True,
                    "severityAgentJson": json.dumps(
                        {"severity": "Sev3", "rationale": "Informational request."},
                        separators=(",", ":"),
                    ),
                    "draftAgentJson": json.dumps(
                        {
                            "subject": "Draft intake follow-up",
                            "body": "Needs human review because no Salesforce account matched the sender domain.",
                        },
                        separators=(",", ":"),
                    ),
                    "correlationId": _case_key(run_id, "C77"),
                },
                "expected": {
                    "accountId": "UNKNOWN",
                    "contactId": "UNKNOWN",
                    "severity": "Unclassified",
                    "engineeringHandoff": False,
                    "route": "HumanReview",
                    "jiraAction": "None",
                    "jiraIssueKey": "None",
                    "driveAction": "SaveExceptionSummary",
                    "outlookAction": "DraftNeedsReview",
                    "slackAction": "None",
                    "exceptionCode": "SALESFORCE_NO_MATCH",
                    "caseKey": _case_key(run_id, "C77"),
                },
                "draft_contains": ["human review", "salesforce"],
            },
            {
                "name": "invalid-severity-agent-json",
                "inputs": {
                    "senderEmail": "lead@fabrikam.example",
                    "subject": "Intermittent latency",
                    "body": "Fabrikam reports intermittent latency. Workaround is available.",
                    "attachmentsJson": "[]",
                    "salesforceMatchesJson": json.dumps(
                        [
                            {
                                "accountId": "001FA",
                                "accountName": "Fabrikam",
                                "tier": "Enterprise",
                                "contactId": "003LEAD",
                            }
                        ],
                        separators=(",", ":"),
                    ),
                    "salesforceOpenCasesJson": "[]",
                    "jiraMatchesJson": "[]",
                    "jiraAvailable": True,
                    "severityAgentJson": "{not valid json",
                    "draftAgentJson": json.dumps(
                        {
                            "subject": "Draft exception note",
                            "body": "Needs human review because the severity agent returned invalid JSON.",
                        },
                        separators=(",", ":"),
                    ),
                    "correlationId": _case_key(run_id, "D05"),
                },
                "expected": {
                    "accountId": "001FA",
                    "contactId": "003LEAD",
                    "severity": "Unclassified",
                    "engineeringHandoff": False,
                    "route": "HumanReview",
                    "jiraAction": "None",
                    "jiraIssueKey": "None",
                    "driveAction": "SaveExceptionSummary",
                    "outlookAction": "DraftNeedsReview",
                    "slackAction": "None",
                    "exceptionCode": "INVALID_AGENT_JSON",
                    "caseKey": _case_key(run_id, "D05"),
                },
                "draft_contains": ["human review", "invalid json"],
            },
        ],
    }


def main() -> None:
    path = Path("seed.json")
    path.write_text(json.dumps(build_seed(), indent=2) + "\n", encoding="utf-8")
    print(f"seeded {path}")


if __name__ == "__main__":
    main()
