#!/usr/bin/env python3
"""Every fact the SupplierOnboarding graders assert, in one place.

Two kinds of constant live here:

1. **Transcribed from `fixtures/sdd.md`** — stage labels, task sets, SLA durations,
   guard literals, resource identities. Re-sweep these whenever the fixture changes;
   `sdd_facts()` below re-derives the volatile subset from the fixture at grade time
   and fails loudly when its parse comes up short, so a fixture reshuffle cannot
   silently turn an assertion into a no-op.

2. **Read off the deployed tenant** — the twenty resource identities and the Outlook
   connection. A tenant reinstall re-mints every one of them; re-sweep the fixture,
   then re-run `sweep_guids.py` and paste the result here.

Nothing in this module reads the caseplan. `caseplan_reader.py` does that.
"""

from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE_SDD = os.path.join(HERE, "fixtures", "sdd.md")

# sha256 of the fixture as committed. The YAML asserts this separately; the graders
# do not, so a deliberate fixture edit does not have to touch every checker.
FIXTURE_SHA256 = "7a6e0312a846ed2a69cf287c94396ebafe3daeb75fa096a7f011c0d892390a24"

CASEPLAN_GLOB = "**/caseplan.json"

# --- Stages -------------------------------------------------------------------

CHECKING = "Checking the application"
BUYER = "Buyer review"
COMPLIANCE = "Compliance and risk review"
SETUP = "Setting up the supplier"
ONBOARDED = "Supplier onboarded"
REJECTED = "Application rejected"
WITHDRAWN = "Application withdrawn"
SLA_REVIEW = "Overall SLA review"

STAGES = [
    (CHECKING, "checking_application", "primary"),
    (BUYER, "buyer_review", "primary"),
    (COMPLIANCE, "compliance_risk_review", "primary"),
    (SETUP, "supplier_setup", "primary"),
    (ONBOARDED, "supplier_onboarded", "primary"),
    (REJECTED, "application_rejected", "secondary"),
    (WITHDRAWN, "application_withdrawn", "secondary"),
    (SLA_REVIEW, "overall_sla_review", "secondary"),
]
PRIMARY_STAGES = {label for label, _, kind in STAGES if kind == "primary"}
SECONDARY_STAGES = {label for label, _, kind in STAGES if kind == "secondary"}

# The three stages whose completion is user-routed, which is what exposes the
# withdrawal lane. `Setting up the supplier` deliberately is NOT one of them: the
# source allows withdrawal only before setup begins. Getting this set wrong is the
# single most likely way to mis-implement this case.
WAIT_FOR_USER_STAGES = {CHECKING, BUYER, COMPLIANCE}

# Secondary lanes that take the application over. The oversight lane runs alongside
# the application instead, so it is interrupting=False.
INTERRUPTING_SECONDARY = {REJECTED, WITHDRAWN}
NON_INTERRUPTING_SECONDARY = {SLA_REVIEW}

TERMINAL_STAGES = {ONBOARDED, REJECTED, WITHDRAWN}

# --- Tasks --------------------------------------------------------------------
# (display name, task type, isRequired, shouldRunOnlyOnce)

STAGE_TASKS = {
    CHECKING: [
        ("Validate application details", "action", True, False),
        ("Pull supplier records and screening", "api-workflow", True, False),
        ("Confirm offering category match", "agent", False, False),
        ("Attach supporting documents", "action", False, False),
        ("Escalate delayed application check", "action", False, False),
        ("Send delay note for the application check", "execute-connector-activity", False, False),
    ],
    BUYER: [
        ("Notify buyer of application", "execute-connector-activity", True, False),
        ("Record buyer review decision", "action", True, False),
        ("Request more information from supplier", "action", False, False),
        ("Order reference check", "action", False, False),
        ("Escalate delayed buyer review", "action", False, False),
        ("Send delay note for the buyer review", "execute-connector-activity", False, False),
    ],
    COMPLIANCE: [
        ("Run compliance and risk check", "api-workflow", True, False),
        ("Analyze supplier financial health", "agent", False, False),
        ("Determine sign-off tier", "api-workflow", True, False),
        ("Obtain procurement director sign-off", "action", False, False),
        ("Record compliance review decision", "action", True, False),
        ("Obtain legal opinion", "action", False, False),
        ("Escalate delayed compliance review", "action", False, False),
        ("Send delay note for the compliance review", "execute-connector-activity", False, False),
    ],
    SETUP: [
        ("Register supplier in ERP", "api-workflow", True, True),
        ("Open contract negotiation case", "case-management", False, True),
        ("Confirm supplier portal access", "action", True, True),
        ("Escalate delayed supplier setup", "action", False, False),
        ("Send delay note for the supplier setup", "execute-connector-activity", False, False),
    ],
    ONBOARDED: [
        ("Send supplier welcome message", "execute-connector-activity", True, True),
        ("Record supplier in approved register", "api-workflow", True, True),
    ],
    REJECTED: [
        ("Send rejection notice to supplier", "execute-connector-activity", True, True),
        ("Log rejection for audit", "api-workflow", True, True),
    ],
    WITHDRAWN: [
        ("Send withdrawal confirmation", "execute-connector-activity", True, True),
        ("Close out withdrawn application", "api-workflow", True, True),
    ],
    SLA_REVIEW: [
        ("Review overall SLA breach", "action", True, True),
    ],
}

TOTAL_TASKS = sum(len(rows) for rows in STAGE_TASKS.values())          # 32
TASK_TYPE_COUNTS = {
    "action": 14,
    "api-workflow": 7,
    "agent": 2,
    "execute-connector-activity": 8,
    "case-management": 1,
}

# Optional tasks a person launches on their own judgement, each locked to one stage.
ADHOC_TASKS = {
    "Attach supporting documents": CHECKING,
    "Request more information from supplier": BUYER,
    "Order reference check": BUYER,
    "Obtain legal opinion": COMPLIANCE,
}

# --- SLAs ---------------------------------------------------------------------

# The SDD states its targets in minutes, at the source's own proportions multiplied by 8. Eight is
# the smallest whole multiple that lifts the shortest phase above the platform's 15-minute floor for
# a minute-denominated SLA. The five primary stages still sum to the case target: 16+32+32+24+16=120.
CASE_SLA = (120, "min")
CASE_AT_RISK_PERCENT = 75          # 120 min is under 3 days, so the 75% band applies
STAGE_AT_RISK_PERCENT = 70         # stated by the source, so it is not re-derived from the band

STAGE_SLA = {                       # label -> (count, unit)
    CHECKING: (16, "min"),
    BUYER: (32, "min"),
    COMPLIANCE: (32, "min"),
    SETUP: (24, "min"),
    ONBOARDED: (16, "min"),
    REJECTED: (16, "min"),
    WITHDRAWN: (16, "min"),
}
# The oversight lane is the one stage with no SLA of its own.
NO_SLA_STAGES = {SLA_REVIEW}

# Breach answered by starting a task INSIDE the breached stage: the task carries the
# `sla-status-change` rule on its OWN entry. A stage-entry rule instead would re-enter
# the stage and re-run its other tasks. `validate` accepts both shapes.
START_TASK_ON_BREACH = {
    "Escalate delayed application check": (CHECKING, "Application check SLA"),
    "Escalate delayed buyer review": (BUYER, "Buyer review SLA"),
    "Escalate delayed compliance review": (COMPLIANCE, "Compliance review SLA"),
    "Escalate delayed supplier setup": (SETUP, "Supplier setup SLA"),
}

# Breach answered by entering a separate lane, which the root SLA does exactly once.
ENTER_STAGE_ON_BREACH = {SLA_REVIEW: ("root", "Supplier Onboarding SLA")}

# Wrap-up phases warn and notify but never start remediation work: apologising for a
# delay and promising a new date on an application that is already finished is wrong.
NOTIFY_ONLY_BREACH_STAGES = {ONBOARDED, REJECTED, WITHDRAWN}

# Group the buyer's at-risk warning goes to, so a stalled review is bumped up before
# the deadline rather than after it.
BUYER_AT_RISK_GROUP = "Category Management"

# --- Per-phase revised dates --------------------------------------------------
# Each phase owns its own slot. One shared slot, or a note reading another phase's
# slot, makes the delay note quote a date that phase never committed to.

PHASE_REVISED_DATE = {
    CHECKING: "applicationCheckRevisedDate",
    BUYER: "buyerReviewRevisedDate",
    COMPLIANCE: "complianceReviewRevisedDate",
    SETUP: "supplierSetupRevisedDate",
}
ESCALATION_OF_PHASE = {
    CHECKING: "Escalate delayed application check",
    BUYER: "Escalate delayed buyer review",
    COMPLIANCE: "Escalate delayed compliance review",
    SETUP: "Escalate delayed supplier setup",
}
DELAY_NOTE_OF_PHASE = {
    CHECKING: "Send delay note for the application check",
    BUYER: "Send delay note for the buyer review",
    COMPLIANCE: "Send delay note for the compliance review",
    SETUP: "Send delay note for the supplier setup",
}

# --- Literal fidelity ---------------------------------------------------------
# Each escalation task names its own phase as a plain string. Cross two of them and the
# supplier is told the wrong phase missed its deadline — the same failure the per-phase
# revised-date slots guard against, one field over. No indirection here, so the
# assertion is exact.

STAGE_NAME_LITERAL = {
    "Escalate delayed application check": CHECKING,
    "Escalate delayed buyer review": BUYER,
    "Escalate delayed compliance review": COMPLIANCE,
    "Escalate delayed supplier setup": SETUP,
    # The oversight lane is not a phase, so it names the case instead of a stage.
    "Review overall SLA breach": "Overall case",
}
STAGE_NAME_INPUT = "stageName"

# --- Guard literals -----------------------------------------------------------
# Taken from the deployed Action Apps' own output enums, not invented. Verified with
# `uip maestro case tasks describe --type action --id <app> --output json`.

BUYER_DECISION_VALUES = {"approve", "reject", "sendback"}
COMPLIANCE_DECISION_VALUES = {"approve", "reject"}
BANK_VERIFIED_VALUE = "verified"

DIRECTOR_THRESHOLD = "500000"
AUTO_THRESHOLD = "50000"

# --- Case-level ---------------------------------------------------------------

CASE_NAME = "SupplierOnboarding"
CASE_IDENTIFIER_PREFIX = "SUP"

# Exactly one case exit marks the case complete. Rejection and withdrawal close the
# application without completing it.
CASE_EXITS = [
    ("required-stages-completed", None, True),
    ("selected-stage-completed", REJECTED, False),
    ("selected-stage-completed", WITHDRAWN, False),
]

CASE_INPUTS = [
    "companyName", "contactName", "contactEmail", "countryOfRegistration",
    "offeringCategory", "expectedAnnualSpend", "spendCurrency", "offeringDescription",
    "submittedDate", "registrationCertificate", "insuranceDocument",
    "taxFormsDocument", "bankDetailsDocument",
]
CASE_OUTPUTS = ["supplierId", "caseOutcome"]

OFFERING_CATEGORIES = {"Raw materials", "Components", "Services", "Logistics", "Other"}

# --- Resource identities (tenant) ---------------------------------------------

API_WORKFLOWS = {
    "SupplierMasterScreeningLookup": "919ff26e-8bb4-4755-9bfd-0d04a51d6639",
    "SupplierComplianceRiskCheck": "69027bbb-2c90-43c3-93af-a09ba7821892",
    "SupplierSignOffTierRules": "b3e2c59b-c3bd-4794-86d1-689de7bc2d6c",
    "SupplierErpRegistration": "d5c07b08-d673-477c-b047-de330699a183",
    "SupplierApprovedRegisterUpdate": "0c3faaff-8e3e-4b68-bf69-2e3b869fb301",
    "SupplierRejectionAuditLog": "1279ba08-7d7d-4cb2-ba52-2fe9809dce00",
    "SupplierWithdrawalCleanup": "80321901-b4a8-45b4-a5b0-1924ee84f3f7",
}
AGENTS = {
    "SupplierOfferingCategoryMatch": "567afdb0-ee17-4c27-9b69-09b2bc7a34c8",
    "SupplierFinancialHealthCheck": "c6f0ecb7-26e2-4365-bc51-a03d5b2edafc",
}
ACTION_APPS = {
    "Supplier Application Validation": "604acda5-8894-447f-b007-1989ec74a7e2",
    "supplier-document-upload": "e0145242-77aa-40b5-8752-e037ec022d40",
    "buyer-supplier-review-v2": "ec16bdfe-6f7b-4f4e-9988-70ee7c86b803",
    "Supplier Information Request": "5bcb5523-93b1-459f-ad66-3bd947b32995",
    "Supplier Reference Check": "741e6c61-65ee-4c6e-8ce5-855e743b50dd",
    "Supplier Legal Opinion": "cb2ddeb4-75d2-4ec1-95cb-533c6d8bf2e7",
    "Supplier Compliance Review": "1229c1ed-ca6b-4a89-9776-883bd0669684",
    "Procurement Director Sign-off": "c20d48bf-4860-420c-b629-3ec8284acdc1",
    "Supplier Portal Access Confirmation": "8bfee375-9973-446d-b409-6799688ffe49",
    "supplier-delay-escalation": "fb171d7c-33a1-4bb6-b09a-030044a7c0b6",
}
CHILD_CASES = {"SupplierContractNegotiation": "a028146a-e14f-489b-a6ca-e1ffa1d315f6"}

ALL_RESOURCE_IDS = set(API_WORKFLOWS.values()) | set(AGENTS.values()) \
    | set(ACTION_APPS.values()) | set(CHILD_CASES.values())          # 20

# The caseplan never carries a raw resource GUID. Each non-connector task binds its
# resource through a composite `resourceKey` of `<folderPath>.<name>`; the Outlook
# connector binds its connection UUID directly. These are what the plan actually holds,
# so these are what a grader can assert. The GUIDs above stay as the tenant-side
# identities the fixture pins and `sweep_guids.py` re-verifies.
RESOURCE_KEYS = {
    "Shared/uipath-maestro-case.buyer-supplier-review-v2": ("app", None),
    "Shared/uipath-maestro-case.supplier-delay-escalation": ("app", None),
    "Shared/uipath-maestro-case.supplier-document-upload": ("app", None),
    "Shared/uipath-maestro-case/Procurement Director Sign-off.Procurement Director Sign-off": ("app", None),
    "Shared/uipath-maestro-case/Supplier Application Validation.Supplier Application Validation": ("app", None),
    "Shared/uipath-maestro-case/Supplier Compliance Review.Supplier Compliance Review": ("app", None),
    "Shared/uipath-maestro-case/Supplier Information Request.Supplier Information Request": ("app", None),
    "Shared/uipath-maestro-case/Supplier Legal Opinion.Supplier Legal Opinion": ("app", None),
    "Shared/uipath-maestro-case/Supplier Portal Access Confirmation.Supplier Portal Access Confirmation": ("app", None),
    "Shared/uipath-maestro-case/Supplier Reference Check.Supplier Reference Check": ("app", None),
    "Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierApprovedRegisterUpdate": ("process", "Api"),
    "Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierComplianceRiskCheck": ("process", "Api"),
    "Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierErpRegistration": ("process", "Api"),
    "Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierFinancialHealthCheck": ("process", "Agent"),
    "Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierMasterScreeningLookup": ("process", "Api"),
    "Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierOfferingCategoryMatch": ("process", "Agent"),
    "Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierRejectionAuditLog": ("process", "Api"),
    "Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierSignOffTierRules": ("process", "Api"),
    "Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierWithdrawalCleanup": ("process", "Api"),
    "Shared/uipath-maestro-case/SupplierNegotiationKit.SupplierContractNegotiation": ("process", "CaseManagement"),
    "dd657127-91f5-4568-a3a3-c024bc03fb0f": ("Connection", None),
}

OUTLOOK_CONNECTION_ID = "dd657127-91f5-4568-a3a3-c024bc03fb0f"
OUTLOOK_ACTIVITY_TYPE_ID = "c7ce0a96-2091-3d94-b16f-706ebb1eb351"
OUTLOOK_CONNECTOR_KEY = "uipath-microsoft-outlook365"

# The one task the child case runs, and the fact the parent must not wait for it.
CHILD_CASE_TASK = "Open contract negotiation case"
CHILD_CASE_WAITS = False

RUN_ONCE_TASKS = {
    name
    for rows in STAGE_TASKS.values()
    for name, _type, _req, once in rows
    if once
}

# --- Output reassigns ---------------------------------------------------------
# Every `-> <variable>` row in the fixture's task Output tables, keyed by the variable
# and listing the task(s) the SDD makes responsible for writing it. Asserting in this
# direction — "each declared target IS written by its task" — catches a dropped output.
# The reverse direction does not work: a task also carries auto-minted output slots
# whose `var` equals their own `id` and which deliberately live outside the case's
# variable namespace, so requiring every `var` to be a declared variable false-fails
# every connector task.

OUTPUT_TARGETS = {
    "addedDocumentContent": ["Attach supporting documents"],
    "addedDocumentName": ["Attach supporting documents"],
    "addedDocumentSubmittedOn": ["Attach supporting documents"],
    "addedDocumentType": ["Attach supporting documents"],
    "applicationCheckRevisedDate": ["Escalate delayed application check"],
    "assignedBuyerEmail": ["Pull supplier records and screening"],
    "auditRecordId": ["Log rejection for audit"],
    "bankVerificationStatus": ["Register supplier in ERP"],
    "buyerComments": ["Record buyer review decision", "Request more information from supplier"],
    "buyerDecision": ["Record buyer review decision"],
    "buyerReviewRevisedDate": ["Escalate delayed buyer review"],
    "categoryMatches": ["Confirm offering category match"],
    "cleanupSummary": ["Close out withdrawn application"],
    "complianceComments": ["Record compliance review decision"],
    "complianceDecision": ["Record compliance review decision"],
    "complianceFlags": ["Run compliance and risk check"],
    "complianceReviewRevisedDate": ["Escalate delayed compliance review"],
    "concernLevel": ["Analyze supplier financial health"],
    "directorSignOffDecision": ["Obtain procurement director sign-off"],
    "directorSignOffNotes": ["Obtain procurement director sign-off"],
    "directorSignOffRequired": ["Determine sign-off tier"],
    "duplicateSupplierIds": ["Pull supplier records and screening"],
    "escalationNotes": [
        "Escalate delayed application check",
        "Escalate delayed buyer review",
        "Escalate delayed compliance review",
        "Escalate delayed supplier setup",
        "Review overall SLA breach",
    ],
    "financialHealthSummary": ["Analyze supplier financial health"],
    "fraudIndicators": ["Analyze supplier financial health"],
    "lastEmailStatus": [
        "Notify buyer of application",
        "Send delay note for the application check",
        "Send delay note for the buyer review",
        "Send delay note for the compliance review",
        "Send delay note for the supplier setup",
        "Send rejection notice to supplier",
        "Send supplier welcome message",
        "Send withdrawal confirmation",
    ],
    "legalOpinion": ["Obtain legal opinion"],
    "portalAccessConfirmation": ["Confirm supplier portal access"],
    "referenceCheckFindings": ["Order reference check"],
    "registeredAt": ["Record supplier in approved register"],
    "reviewNotes": ["Confirm offering category match"],
    "reviewsCancelled": ["Close out withdrawn application"],
    "riskRating": ["Run compliance and risk check"],
    "sanctionsFindings": ["Pull supplier records and screening"],
    "signOffTier": ["Determine sign-off tier"],
    "suggestedCategory": ["Confirm offering category match"],
    "supplierId": ["Register supplier in ERP"],
    "supplierSetupRevisedDate": ["Escalate delayed supplier setup"],
    "timersStopped": ["Close out withdrawn application"],
    "validationIssues": ["Validate application details"],
    "validationOutcome": ["Validate application details"],
}

# --- Recipients ---------------------------------------------------------------
# Type 3 is the runtime expression form. Roles carry no recipient in the caseplan at
# all: group assignment is configured in the Actions app, not here.

EXPRESSION_RECIPIENT_TASKS = {
    "Record buyer review decision",
    "Request more information from supplier",
    "Order reference check",
}
EXPRESSION_RECIPIENT_VALUE = "=vars.assignedBuyerEmail"
EMAIL_RECIPIENT_TYPE = 2            # a literal mailbox address
EXPRESSION_RECIPIENT_TYPE = 3

# --- Wire-path casing ---------------------------------------------------------
# The connector's output path is lowercase `response.status`. A build that PascalCases
# it validates clean and then dies at runtime. `displayName` is a human label and is
# NOT part of this contract — asserting on it false-fails a correct build.

CONNECTOR_OUTPUT_PATH = "response.status"
CONNECTOR_OUTPUT_ROOT = "response"
CONNECTOR_OUTPUT_TARGET = "lastEmailStatus"
CONNECTOR_TASK_COUNT = 8

# The four supporting documents the category-match agent reads. The fixture reads them
# through a guarded array walk rather than a bare `vars.X.FullName`, so the names are
# pinned here instead of parsed back out of an expression whose shape is free.
SUPPORTING_DOCUMENT_VARIABLES = {
    "registrationCertificate",
    "insuranceDocument",
    "taxFormsDocument",
    "bankDetailsDocument",
}
DOCUMENT_READER_TASK = "Confirm offering category match"


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")


def read_fixture() -> str:
    try:
        with open(FIXTURE_SDD, encoding="utf-8") as stream:
            return stream.read()
    except OSError as exc:
        _fail(f"cannot read fixture SDD {FIXTURE_SDD}: {exc}")


_XREF_RE = re.compile(r"\$xref\('([^']+)','([^']+)','([^']+)'\)")
_GUARD_LITERAL_RE = re.compile(r"[!=]==\s*\"([A-Za-z][\w-]*)\"")
_CONNECTOR_EXTRACT_RE = re.compile(r"^\|\s*(response\.status)\s*\|\s*->\s*(\w+)\s*\|", re.M)
_VARS_RE = re.compile(r"vars\.([A-Za-z_]\w*)")


def sdd_facts() -> dict:
    """Re-derive the volatile facts from the fixture, and refuse a thin parse.

    A regex that stops matching after a fixture edit would otherwise hand the graders
    an empty set, and an assertion over an empty set passes. Every parse below carries
    its own floor so that failure reads `fixture parse error`, not `OK`.
    """
    sdd = read_fixture()

    xrefs = set(_XREF_RE.findall(sdd))
    if len(xrefs) < 4:
        _fail(
            "fixture parse error: expected >=4 distinct $xref triples reading a task's "
            f"own output; got {sorted(xrefs)}"
        )

    literals = set(_GUARD_LITERAL_RE.findall(sdd))
    expected_literals = BUYER_DECISION_VALUES | {BANK_VERIFIED_VALUE}
    if not expected_literals <= literals:
        _fail(
            "fixture parse error: the guard literals this case routes on are missing "
            f"from the fixture. found={sorted(literals)} required={sorted(expected_literals)}"
        )

    extracts = _CONNECTOR_EXTRACT_RE.findall(sdd)
    if len(extracts) != CONNECTOR_TASK_COUNT:
        _fail(
            f"fixture parse error: expected {CONNECTOR_TASK_COUNT} `response.status | -> "
            f"...` extract rows, one per connector task; got {len(extracts)}"
        )
    targets = {target for _path, target in extracts}
    if targets != {CONNECTOR_OUTPUT_TARGET}:
        _fail(
            f"fixture parse error: connector extracts should all land in "
            f"{CONNECTOR_OUTPUT_TARGET!r}; got {sorted(targets)}"
        )

    var_reads = set(_VARS_RE.findall(sdd)) - {"$xref"}
    if len(var_reads) < 40:
        _fail(
            f"fixture parse error: expected >=40 distinct vars.* reads; got {len(var_reads)}"
        )

    missing_dates = [
        var for var in PHASE_REVISED_DATE.values() if var not in var_reads
    ]
    if missing_dates:
        _fail(
            "fixture parse error: these per-phase revised-date variables are not read "
            f"anywhere in the fixture: {missing_dates}"
        )

    return {
        "xrefs": xrefs,
        "guard_literals": literals,
        "connector_extracts": extracts,
        "var_reads": var_reads,
    }
