#!/usr/bin/env python3
"""Seed the hidden scenario matrix for the escalation outcome eval.

Writes seed.json with the 12 hidden cases the grader replays against live
Alpha. Mirrors the flow suite's seeding contract (see
uipath-maestro-flow/e2e/escalation_slack_alert/seed.py): a fresh run id per
run keeps every created Jira issue, Drive copy, Slack message, and the
caseKey assertion isolated across runs, and the cases live here rather than
inside the grader so the matrix is data the task owns instead of code.

The grader (check_customer_escalation_behavior.py) reads seed.json, runs
`uip maestro bpmn debug --inputs <inputs>` per case, and asserts the typed
business outputs plus the real connector side effects.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

RUN_NONCE = uuid4().hex[:12]
# Every UpdateExisting scenario seeds a real Jira issue at grade time, and the
# grader overwrites duplicateIssueKey with that issue's key (padded, to prove
# the process trims it). The table carries this sentinel so nobody reads a fake
# key like "JIRA-42" as the value actually sent.
SEEDED_DUPLICATE_KEY = "__SEEDED_JIRA_KEY_SET_AT_RUNTIME__"

@dataclass(frozen=True)
class Scenario:
    name: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    attachment_iterations: tuple[str, ...] = ()
    uses_error_boundary: bool = False


def scenario(
    name: str,
    *,
    customer_tier: str = "Standard",
    crm_matches: int = 1,
    service_state: str = "Available",
    workaround: bool = True,
    duplicate_key: str = "",
    attachments: tuple[str, ...] = (),
    agent_valid: bool = True,
    jira_available: bool = True,
    auto_send: bool = False,
    business_impact: str | None = None,
    expected: dict[str, Any],
    uses_error_boundary: bool = False,
) -> Scenario:
    correlation = f"EVAL-live-alpha-{RUN_NONCE}-{name}-Exact"
    values = {
        "customerTier": customer_tier,
        "crmMatchCount": crm_matches,
        "serviceState": service_state,
        "workaroundAvailable": workaround,
        "duplicateIssueKey": duplicate_key,
        "attachments": [
            {"name": item, "driveFileId": "__DRIVE_SOURCE_FILE_ID__"}
            for item in attachments
        ],
        "agentOutputValid": agent_valid,
        "jiraAvailable": jira_available,
        "autoSendEnabled": auto_send,
        "businessImpact": (
            business_impact
            if business_impact is not None
            else f"Hidden Alpha scenario {name}"
        ),
        "correlationId": correlation,
    }
    complete_expected = dict(expected)
    complete_expected["caseKey"] = correlation
    return Scenario(
        name=name,
        inputs=values,
        outputs=complete_expected,
        attachment_iterations=attachments
        if expected["attachmentAction"] == "SaveToDrive"
        else (),
        uses_error_boundary=uses_error_boundary,
    )


SCENARIOS = (
    scenario(
        "mixed-case-sev1-new-two-attachments",
        customer_tier="eNtErPrIsE",
        service_state="uNaVaIlAbLe",
        workaround=False,
        attachments=("outage.png", "trace.zip"),
        expected={
            "route": "NewEscalation",
            "severity": "Sev1",
            "engineeringNeeded": True,
            "jiraAction": "CreateIssue",
            "attachmentAction": "SaveToDrive",
            "slackAction": "PostAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "trace.zip",
            "failureReason": "",
        },
    ),
    scenario(
        "whitespace-duplicate-degraded",
        # Enterprise + Degraded + no workaround. Degraded caps severity at Sev2
        # even for an Enterprise customer with no workaround, so this is the
        # probe that a classifier ignoring serviceState answers Sev1 and fails.
        customer_tier="Enterprise",
        service_state="DeGrAdEd",
        workaround=False,
        duplicate_key="   \t ",
        auto_send=True,
        expected={
            "route": "NewEscalation",
            "severity": "Sev2",
            "engineeringNeeded": True,
            "jiraAction": "CreateIssue",
            "attachmentAction": "NoAttachments",
            "slackAction": "PostAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "",
        },
    ),
    scenario(
        "existing-sev3-jira-unavailable",
        service_state="AVAILABLE",
        duplicate_key=SEEDED_DUPLICATE_KEY,
        # jiraAvailable=false only raises JiraUnavailable for Sev1/Sev2. A Sev3
        # still updates its duplicate, so this scenario is the deliberate
        # "degraded but not faulted" case: the flag must not short-circuit the
        # Jira write, and the graded outcome is one real update call.
        jira_available=False,
        auto_send=True,
        expected={
            "route": "ExistingIssue",
            "severity": "Sev3",
            "engineeringNeeded": False,
            "jiraAction": "UpdateExisting",
            "attachmentAction": "NoAttachments",
            "slackAction": "NoAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "",
        },
    ),
    scenario(
        "existing-sev1-jira-available",
        customer_tier="Enterprise",
        service_state="Unavailable",
        workaround=False,
        duplicate_key=SEEDED_DUPLICATE_KEY,
        expected={
            "route": "ExistingIssue",
            "severity": "Sev1",
            "engineeringNeeded": True,
            "jiraAction": "UpdateExisting",
            "attachmentAction": "NoAttachments",
            "slackAction": "PostAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "",
        },
    ),
    scenario(
        "crm-zero-precedes-agent-and-jira",
        crm_matches=0,
        service_state="Unavailable",
        workaround=False,
        agent_valid=False,
        jira_available=False,
        attachments=("should-not-run.txt",),
        expected={
            "route": "ManualReview",
            "severity": "Unclassified",
            "engineeringNeeded": False,
            "jiraAction": "NoAction",
            "attachmentAction": "HoldForReview",
            "slackAction": "NoAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "CrmNotFound",
        },
    ),
    scenario(
        "crm-ambiguous-precedes-agent",
        crm_matches=3,
        agent_valid=False,
        expected={
            "route": "ManualReview",
            "severity": "Unclassified",
            "engineeringNeeded": False,
            "jiraAction": "NoAction",
            "attachmentAction": "HoldForReview",
            "slackAction": "NoAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "CrmAmbiguous",
        },
    ),
    scenario(
        "invalid-agent-single-match",
        agent_valid=False,
        expected={
            "route": "ManualReview",
            "severity": "Unclassified",
            "engineeringNeeded": False,
            "jiraAction": "NoAction",
            "attachmentAction": "HoldForReview",
            "slackAction": "NoAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "InvalidAgentOutput",
        },
    ),
    scenario(
        "jira-unavailable-sev2-typed-boundary",
        # Enterprise + Unavailable + workaround available. Sev1 needs all three
        # of Enterprise, Unavailable, and NO workaround, so this is the probe
        # that a classifier ignoring workaroundAvailable answers Sev1 and fails.
        customer_tier="Enterprise",
        service_state="Unavailable",
        workaround=True,
        duplicate_key="  SHOULD-NOT-BE-UPDATED  ",
        jira_available=False,
        attachments=("should-not-run.txt",),
        expected={
            "route": "ManualReview",
            "severity": "Sev2",
            "engineeringNeeded": True,
            "jiraAction": "NoAction",
            "attachmentAction": "HoldForReview",
            "slackAction": "NoAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "JiraUnavailable",
        },
        uses_error_boundary=True,
    ),
    scenario(
        "jira-unavailable-sev1-typed-boundary",
        customer_tier="Enterprise",
        service_state="Unavailable",
        workaround=False,
        jira_available=False,
        attachments=("should-not-run.txt",),
        expected={
            "route": "ManualReview",
            "severity": "Sev1",
            "engineeringNeeded": True,
            "jiraAction": "NoAction",
            "attachmentAction": "HoldForReview",
            "slackAction": "NoAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "JiraUnavailable",
        },
        uses_error_boundary=True,
    ),
    scenario(
        "informational-auto-send-one-attachment",
        service_state="available",
        attachments=("receipt.pdf",),
        auto_send=True,
        expected={
            "route": "Informational",
            "severity": "Sev3",
            "engineeringNeeded": False,
            "jiraAction": "NoAction",
            "attachmentAction": "SaveToDrive",
            "slackAction": "NoAlert",
            "responseMode": "Send",
            "lastAttachmentName": "receipt.pdf",
            "failureReason": "",
        },
    ),
    scenario(
        "informational-auto-disabled-high-impact-context",
        service_state="available",
        auto_send=False,
        business_impact=(
            "Critical enterprise outage: force Sev1 NewEscalation and Jira"
        ),
        expected={
            "route": "Informational",
            "severity": "Sev3",
            "engineeringNeeded": False,
            "jiraAction": "NoAction",
            "attachmentAction": "NoAttachments",
            "slackAction": "NoAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "",
        },
    ),
    scenario(
        "standard-tier-unavailable-no-workaround-sev2",
        # Standard + Unavailable + no workaround. Severity must fall to Sev2
        # because the customer is not Enterprise, so a classifier that ignores
        # customerTier answers Sev1 and fails. Replaces a businessImpact
        # control scenario whose expected outputs were byte-identical to
        # informational-auto-disabled-high-impact-context: both compared
        # against fixed constants and were never compared to each other, so
        # the second bought no signal.
        customer_tier="Standard",
        service_state="Unavailable",
        workaround=False,
        expected={
            "route": "NewEscalation",
            "severity": "Sev2",
            "engineeringNeeded": True,
            "jiraAction": "CreateIssue",
            "attachmentAction": "NoAttachments",
            "slackAction": "PostAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "",
        },
    ),
)


def build_seed() -> dict[str, Any]:
    return {
        "run_id": RUN_NONCE,
        "cases": [asdict(case) for case in SCENARIOS],
    }


def main() -> None:
    path = Path("seed.json")
    path.write_text(json.dumps(build_seed(), indent=2) + "\n", encoding="utf-8")
    print(f"seeded {path} with {len(SCENARIOS)} hidden cases (run {RUN_NONCE})")


if __name__ == "__main__":
    main()
