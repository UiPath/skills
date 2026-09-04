"""Expectations for the SupplierOnboarding case build, read from ``fixtures/sdd.md``.

One module so the topology / task / SLA / bindings graders and their unit tests
share a single transcription of the staged SDD. Names below are the SDD's own
stage names, task names, resource names and folder paths; matching is
normalization-insensitive (see ``norm``) so punctuation drift in a display name
is not graded as a defect.

Deliberately NOT graded (SDD carries a value the skill contract overrides or
leaves open):

- ``metadata.caseIdentifier`` — §1 states both "Type: constant. Prefix: SUP"
  and "Case Identifier source | =metadata.ExternalId"; those disagree, and
  `metadata.ExternalId` is the field being set, never a source
  (`plugins/case/planning.md`).
- Connector ``serviceType`` — the SDD prints ``Intsvc.ExecuteActivity`` while
  the canonical value is ``Intsvc.ActivityExecution``
  (`plugins/tasks/connector-activity/impl-json.md`). Connector identity is
  graded through the connection / activity-type IDs instead.
- ``resourceKey`` suffixes for api-workflow tasks — the suffix is the resolved
  registry entry's ``name``, not the SDD's "Resolved Resource" label
  (`plugins/tasks/api-workflow/planning.md`), so bindings are graded by folder
  path plus resourceKey self-consistency (Check 11).
"""

from __future__ import annotations

import os
import re

SOLUTION = "SupplierOnboarding"
CASEPLAN_PATH = os.path.join(SOLUTION, SOLUTION, "caseplan.json")

CONNECTOR_KEY = "uipath-microsoft-outlook365"
CONNECTION_ID = "dd657127-91f5-4568-a3a3-c024bc03fb0f"
ACTIVITY_TYPE_ID = "c7ce0a96-2091-3d94-b16f-706ebb1eb351"

CASE_SLA_TITLE = "Application Resolution SLA"
CASE_SLA = (15, "d")
AT_RISK_PERCENTAGE = 70

# ── stages ──────────────────────────────────────────────────────────────────
CHECKING = "Checking the Application"
BUYER = "Buyer Review"
COMPLIANCE = "Compliance and Risk Review"
SETUP = "Supplier Setup"
ONBOARDED = "Onboarded"
REJECTED = "Rejected"
WITHDRAWN = "Withdrawn"

PRIMARY_STAGES = [CHECKING, BUYER, COMPLIANCE, SETUP, ONBOARDED]
SECONDARY_STAGES = [REJECTED, WITHDRAWN]
ALL_STAGES = PRIMARY_STAGES + SECONDARY_STAGES

# stage → (count, unit) of its default SLA
STAGE_SLA = {
    CHECKING: (2, "d"),
    BUYER: (4, "d"),
    COMPLIANCE: (4, "d"),
    SETUP: (3, "d"),
    ONBOARDED: (2, "d"),
    REJECTED: (2, "d"),
    WITHDRAWN: (2, "d"),
}

# Condition-derived stage hops the SDD authors (either encoding: the target's
# entry rule or the source's exitToStageId).
EXPECTED_TRANSITIONS = [
    (CHECKING, BUYER),
    (BUYER, COMPLIANCE),
    (COMPLIANCE, SETUP),
    (SETUP, ONBOARDED),
    (BUYER, CHECKING),      # send-back for corrections
    (BUYER, REJECTED),
    (COMPLIANCE, REJECTED),
    (SETUP, REJECTED),
]

# ── guard expressions (normalized comparison — see norm_expr) ───────────────
SEND_BACK = 'vars.buyerDecision === "SendBack"'
BUYER_APPROVE = 'vars.buyerDecision === "Approve"'
BUYER_DECLINE = 'vars.buyerDecision === "Decline"'
SEND_TO_SETUP = 'vars.complianceDecision === "SendToSetup"'
COMPLIANCE_REJECT = 'vars.complianceDecision === "Reject"'
BANK_VERIFIED = "vars.bankDetailsVerified === true"
BANK_NOT_VERIFIED = "vars.bankDetailsVerified === false"
SIGN_OFF_REQUIRED = "vars.directorSignOffRequired === true"
SIGN_OFF_NOT_REQUIRED = "vars.directorSignOffRequired !== true"

# ── tasks ───────────────────────────────────────────────────────────────────
# entry kinds:
#   stage-entered      → current-stage-entered
#   adhoc              → adhoc (and nothing else)
#   sequential         → runs-sequentially
#   sla-stage          → sla-status-change against the task's own stage SLA
#   sla-root           → sla-status-change against the case (root) SLA
#   gate               → selected-tasks-completed (graded separately)
CONNECTOR_TASK = "execute-connector-activity"


def _task(name, task_type, required, entry, run_once=False):
    return {
        "name": name,
        "type": task_type,
        "required": required,
        "run_once": run_once,
        "entry": entry,
    }


TASKS = {
    CHECKING: [
        _task("Validate Application", "action", True, "stage-entered"),
        _task("Screen Company Records", "api-workflow", True, "stage-entered"),
        _task("Match Offering to Category", "agent", False, "stage-entered"),
        _task("Receive Additional Documents", "action", False, "adhoc"),
        _task(
            "Escalate Checking the Application to Procurement Operations Lead",
            "action", False, "sla-stage",
        ),
        _task(
            "Send Supplier Delay Notice - Checking the Application",
            CONNECTOR_TASK, False, "sla-stage",
        ),
    ],
    BUYER: [
        _task("Buyer Decision", "action", True, "stage-entered"),
        _task("Ask Supplier for Clarification", "action", False, "adhoc"),
        _task("Order Reference Check", "action", False, "adhoc"),
        _task(
            "Escalate Buyer Review to Procurement Operations Lead",
            "action", False, "sla-stage",
        ),
        _task("Send Supplier Delay Notice - Buyer Review", CONNECTOR_TASK, False, "sla-stage"),
    ],
    COMPLIANCE: [
        _task("Compliance and Risk Screening", "api-workflow", True, "stage-entered"),
        _task("Analyze Financial Health", "agent", False, "stage-entered"),
        _task("Procurement Director Sign-off", "action", False, "gate"),
        _task("Request Legal Counsel Opinion", "action", False, "adhoc"),
        _task("Compliance Decision", "action", True, "gate"),
        _task("Determine Supplier Sign-off Tier", "process", True, "stage-entered"),
        _task(
            "Escalate Compliance and Risk Review to Procurement Operations Lead",
            "action", False, "sla-stage",
        ),
        _task(
            "Send Supplier Delay Notice - Compliance and Risk Review",
            CONNECTOR_TASK, False, "sla-stage",
        ),
    ],
    SETUP: [
        _task("Create Supplier Record in ERP", "api-workflow", True, "sequential"),
        _task("Verify Supplier Portal Access", "action", True, "sequential"),
        _task("Open Contract Negotiation Record", "case-management", False, "adhoc"),
        _task(
            "Escalate Supplier Setup to Procurement Operations Lead",
            "action", False, "sla-stage",
        ),
        _task("Send Supplier Delay Notice - Supplier Setup", CONNECTOR_TASK, False, "sla-stage"),
    ],
    ONBOARDED: [
        _task("Send Welcome Message", CONNECTOR_TASK, True, "sequential"),
        _task("Record in Approved Supplier Register", "api-workflow", True, "sequential"),
        _task(
            "Escalate Onboarded to Procurement Operations Lead",
            "action", False, "sla-stage",
        ),
        _task("Send Supplier Delay Notice - Onboarded", CONNECTOR_TASK, False, "sla-stage"),
        _task(
            "Procurement Director Post-Mortem Review - Onboarded",
            "action", False, "sla-root",
        ),
    ],
    REJECTED: [
        _task("Notify Supplier of Rejection", CONNECTOR_TASK, True, "sequential"),
        _task("Log Rejection for Audit", "api-workflow", True, "sequential"),
        _task(
            "Escalate Rejected to Procurement Operations Lead",
            "action", False, "sla-stage",
        ),
        _task("Send Supplier Delay Notice - Rejected", CONNECTOR_TASK, False, "sla-stage"),
        _task(
            "Procurement Director Post-Mortem Review - Rejected",
            "action", False, "sla-root",
        ),
    ],
    WITHDRAWN: [
        _task("Confirm Withdrawal to Supplier", CONNECTOR_TASK, True, "sequential"),
        _task("Log Withdrawal for Audit", "api-workflow", True, "sequential"),
        _task(
            "Escalate Withdrawn to Procurement Operations Lead",
            "action", False, "sla-stage",
        ),
        _task("Send Supplier Delay Notice - Withdrawn", CONNECTOR_TASK, False, "sla-stage"),
        _task(
            "Procurement Director Post-Mortem Review - Withdrawn",
            "action", False, "sla-root",
        ),
    ],
}

TASK_TOTAL = sum(len(v) for v in TASKS.values())          # 39
TYPE_TOTALS = {
    "action": 19,
    "api-workflow": 6,
    "agent": 2,
    "process": 1,
    "case-management": 1,
    CONNECTOR_TASK: 10,
}

# Tasks whose recipient the SDD pins to a case-variable expression; the action
# plugin requires an object `{Type, Value}`, never a bare string.
EXPRESSION_RECIPIENTS = {
    "Buyer Decision": "=vars.assignedBuyer",
    "Ask Supplier for Clarification": "=vars.assignedBuyer",
    "Order Reference Check": "=vars.assignedBuyer",
    "Verify Supplier Portal Access": "=vars.contactEmail",
}

# ── conditional gates (§2 Stage 3, §2 Stage 4) ──────────────────────────────
SIGN_OFF_GATE = {
    "task": "Procurement Director Sign-off",
    "selected": ["Determine Supplier Sign-off Tier"],
    "expressions": [SIGN_OFF_REQUIRED],
}
COMPLIANCE_GATE = {
    "task": "Compliance Decision",
    # two DNF conditions: without sign-off, and with it
    "selected_without": ["Compliance and Risk Screening", "Determine Supplier Sign-off Tier"],
    "selected_with": [
        "Compliance and Risk Screening",
        "Determine Supplier Sign-off Tier",
        "Procurement Director Sign-off",
    ],
    "expressions": [SIGN_OFF_NOT_REQUIRED, SIGN_OFF_REQUIRED],
}
PORTAL_GATE = {"task": "Verify Supplier Portal Access", "expressions": [BANK_VERIFIED]}

# ── case variables (§1) ─────────────────────────────────────────────────────
IN_VARIABLES = [
    "companyName",
    "contactName",
    "contactEmail",
    "countryOfRegistration",
    "category",
    "expectedAnnualSpend",
    "spendCurrency",
    "offeringDescription",
    "submissionDate",
    "registrationCertificate",
    "insuranceDocument",
    "taxFormsDocument",
    "bankDetailsDocument",
]
FILE_VARIABLES = [
    "registrationCertificate",
    "insuranceDocument",
    "taxFormsDocument",
    "bankDetailsDocument",
]
GATE_VARIABLES = [
    "buyerDecision",
    "complianceDecision",
    "bankDetailsVerified",
    "directorSignOffRequired",
]

# ── resources (§4) ──────────────────────────────────────────────────────────
FOLDER_ROOT = "Shared/uipath-maestro-case"

API_WORKFLOWS = [
    "Supplier Master and Screening Lookup",
    "Supplier Compliance Risk Assessment",
    "ERP Supplier Setup",
    "Approved Supplier Register Update",
    "Supplier Rejection Audit Log",
    "Supplier Withdrawal Cleanup",
]
AGENTS = ["OfferingCategoryMatchAgent", "FinancialHealthFraudAnalysisAgent"]
PROCESSES = ["DetermineSupplierSignOffTier"]
CHILD_CASES = ["Supplier Contract Negotiation"]
ACTION_APPS = [
    "Supplier Application Validation",
    "Supplier Document Upload",
    "Buyer Supplier Review",
    "Supplier Information Request",
    "Supplier Reference Check",
    "Supplier Legal Opinion",
    "Supplier Compliance Review",
    "Supplier Portal Access Confirmation",
    "Procurement Director Sign-off",
]
SHARED_ESCALATION_APP = "Guardrail.Escalation.Action.App"

# resource-name → deployment folder path
RESOURCE_FOLDERS = {
    name: f"{FOLDER_ROOT}/{name}"
    for name in API_WORKFLOWS + AGENTS + PROCESSES + CHILD_CASES + ACTION_APPS
}
RESOURCE_FOLDERS[SHARED_ESCALATION_APP] = "Shared"

# binding contract per task type — plugins/variables/bindings/impl-json.md
BINDING_CONTRACT = {
    "api-workflow": ("process", "Api"),
    "agent": ("process", "Agent"),
    "process": ("process", "ProcessOrchestration"),
    "case-management": ("process", "CaseManagement"),
    "action": ("app", None),
}

# GUIDs the fixture pins; graded only as a fixture guard (tenant identities are
# discovery inputs, not runtime binding fields).
FIXTURE_GUIDS = [
    "d42bcbb3-a8d6-4a8d-9e55-7cf20d9d7dfe",
    "59cf8e5a-bd13-43ff-a9b4-6f404da6942f",
    "f99ab8f9-cae4-40e3-8e2d-091a7de09c28",
    "1fb9f714-89d8-4d00-bec1-1da93538c5ed",
    "8345bd59-c596-4107-8731-0029f19a02e5",
    "a6cf0dfb-b6dd-40cf-ac19-b11590ef6618",
    "ce93a98d-ed40-4b66-afda-33fa9e11b2bb",
    "61beb9ef-ad3b-4023-8960-fec893c7f1e8",
    "42759c87-cbf0-406d-bfb5-dda5bd34b259",
    "925ce1ba-9a51-4c53-9168-8d76c0b3b68b",
    "aeaf2e33-6e83-4f8b-822f-700439632b7a",
    CONNECTION_ID,
    ACTIVITY_TYPE_ID,
]


def norm(value: object) -> str:
    """Punctuation- and case-insensitive key for stage / task / resource names."""
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def norm_expr(value: object) -> str:
    """Whitespace- and quote-insensitive key for a `=js:` guard expression."""
    return re.sub(r"\s+", "", str(value or "")).replace("'", '"').lower()


# task → the §4 resource it binds ("Used By Tasks"). Escalation and post-mortem
# action tasks all bind the shared Guardrail app.
TASK_RESOURCE = {
    "Validate Application": "Supplier Application Validation",
    "Screen Company Records": "Supplier Master and Screening Lookup",
    "Match Offering to Category": "OfferingCategoryMatchAgent",
    "Receive Additional Documents": "Supplier Document Upload",
    "Buyer Decision": "Buyer Supplier Review",
    "Ask Supplier for Clarification": "Supplier Information Request",
    "Order Reference Check": "Supplier Reference Check",
    "Compliance and Risk Screening": "Supplier Compliance Risk Assessment",
    "Analyze Financial Health": "FinancialHealthFraudAnalysisAgent",
    "Procurement Director Sign-off": "Procurement Director Sign-off",
    "Request Legal Counsel Opinion": "Supplier Legal Opinion",
    "Compliance Decision": "Supplier Compliance Review",
    "Determine Supplier Sign-off Tier": "DetermineSupplierSignOffTier",
    "Create Supplier Record in ERP": "ERP Supplier Setup",
    "Verify Supplier Portal Access": "Supplier Portal Access Confirmation",
    "Open Contract Negotiation Record": "Supplier Contract Negotiation",
    "Record in Approved Supplier Register": "Approved Supplier Register Update",
    "Log Rejection for Audit": "Supplier Rejection Audit Log",
    "Log Withdrawal for Audit": "Supplier Withdrawal Cleanup",
}
TASK_RESOURCE.update(
    {
        spec["name"]: SHARED_ESCALATION_APP
        for specs in TASKS.values()
        for spec in specs
        if spec["type"] == "action"
        and (
            spec["name"].startswith("Escalate ")
            or spec["name"].startswith("Procurement Director Post-Mortem Review")
        )
    }
)
