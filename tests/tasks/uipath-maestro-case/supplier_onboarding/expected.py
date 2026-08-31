#!/usr/bin/env python3
"""Every fact the SupplierOnboarding graders assert, in one place.

Two kinds of constant live here:

1. **Transcribed from `fixtures/sdd.md`** — stage labels, task sets, SLA durations,
   guard literals, resource identities. Re-sweep these whenever the fixture changes;
   `sdd_facts()` below re-derives the volatile subset from the fixture at grade time
   and fails loudly when its parse comes up short, so a fixture reshuffle cannot
   silently turn an assertion into a no-op.

2. **Read off the deployed tenant**: the fourteen resource identities and the Outlook
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
FIXTURE_SHA256 = "9c78112f0679c7cf2592925ac9171c7014ce75417e6eece675a6f761c7f3a14d"

CASEPLAN_GLOB = "**/caseplan.json"

# --- Stages -------------------------------------------------------------------

CHECKING = "Checking the application"
BUYER = "Buyer review"
COMPLIANCE = "Compliance and risk review"
SETUP = "Setting up the supplier"
ONBOARDED = "Supplier onboarded"
REJECTED = "Application rejected"
WITHDRAWN = "Application withdrawn"

STAGES = [
    (CHECKING, "checking_application", "primary"),
    (BUYER, "buyer_review", "primary"),
    (COMPLIANCE, "compliance_risk_review", "primary"),
    (SETUP, "supplier_setup", "primary"),
    (ONBOARDED, "supplier_onboarded", "primary"),
    (REJECTED, "application_rejected", "secondary"),
    (WITHDRAWN, "application_withdrawn", "secondary"),
]
PRIMARY_STAGES = {label for label, _, kind in STAGES if kind == "primary"}
SECONDARY_STAGES = {label for label, _, kind in STAGES if kind == "secondary"}

# The three stages whose completion is user-routed, which is what exposes the
# withdrawal lane. `Setting up the supplier` deliberately is NOT one of them: the
# source allows withdrawal only before setup begins. Getting this set wrong is the
# single most likely way to mis-implement this case.
WAIT_FOR_USER_STAGES = {CHECKING, BUYER, COMPLIANCE}

# Both secondary lanes take the application over: entering one is how the application ends.
INTERRUPTING_SECONDARY = {REJECTED, WITHDRAWN}
NON_INTERRUPTING_SECONDARY: set[str] = set()

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
    ],
    COMPLIANCE: [
        ("Record compliance review decision", "action", True, False),
    ],
    SETUP: [
        ("Register supplier in ERP", "api-workflow", True, True),
        ("Open contract negotiation case", "case-management", False, True),
    ],
    ONBOARDED: [
        ("Send supplier welcome message", "execute-connector-activity", True, True),
    ],
    REJECTED: [
        ("Send rejection notice to supplier", "execute-connector-activity", True, True),
    ],
    WITHDRAWN: [
        ("Send withdrawal confirmation", "execute-connector-activity", True, True),
    ],
}

TOTAL_TASKS = sum(len(rows) for rows in STAGE_TASKS.values())          # 14
TASK_TYPE_COUNTS = {
    "action": 5,
    "api-workflow": 2,
    "agent": 1,
    "execute-connector-activity": 5,
    "case-management": 1,
}

# Optional tasks a person launches on their own judgement, each locked to one stage.
# The one optional task a person launches on their own judgement. It is the supplier's, and it is
# the only way a corrected document reaches an application the buyer sent back, so a send-back that
# re-enters the intake phase has something to answer it.
ADHOC_TASKS = {
    "Attach supporting documents": CHECKING,
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
}
# The two terminal lanes carry no SLA of their own: the source gives one wrap-up target for all
# three wrap-ups, and the onboarding wrap-up is the one inside the 120-minute arithmetic.
NO_SLA_STAGES = {REJECTED, WITHDRAWN}

# Breach answered by starting a task INSIDE the breached stage: the task carries the
# `sla-status-change` rule on its OWN entry. A stage-entry rule instead would re-enter
# the stage and re-run its other tasks. `validate` accepts both shapes.
# One phase answers a breach this way. The source states the phase-breach behaviour once, so it is
# authored once, on the intake check.
START_TASK_ON_BREACH = {
    "Escalate delayed application check": (CHECKING, "Application check SLA"),
}

# No breach enters a separate lane. The case-level breach notifies and starts nothing.
ENTER_STAGE_ON_BREACH: dict[str, tuple[str, str]] = {}

# Phases that warn and notify but never start remediation work. The two review phases without an
# escalation task are here for the same reason as the wrap-ups: nothing is left to remediate that a
# notification does not already cover.
NOTIFY_ONLY_BREACH_STAGES = {BUYER, COMPLIANCE, SETUP, ONBOARDED}

# Group the buyer's at-risk warning goes to, so a stalled review is bumped up before
# the deadline rather than after it.
BUYER_AT_RISK_GROUP = "Category Management"

# --- Per-phase revised dates --------------------------------------------------
# The intake check is the one phase that answers a breach with work, so it owns the one slot.
# A note reading anything else quotes a date the phase never committed to.

PHASE_REVISED_DATE = {
    CHECKING: "applicationCheckRevisedDate",
}
ESCALATION_OF_PHASE = {
    CHECKING: "Escalate delayed application check",
}
DELAY_NOTE_OF_PHASE = {
    CHECKING: "Send delay note for the application check",
}

# --- Literal fidelity ---------------------------------------------------------
# Each escalation task names its own phase as a plain string. Cross two of them and the
# supplier is told the wrong phase missed its deadline — the same failure the per-phase
# revised-date slots guard against, one field over. No indirection here, so the
# assertion is exact.

STAGE_NAME_LITERAL = {
    "Escalate delayed application check": CHECKING,
}
STAGE_NAME_INPUT = "stageName"

# --- Guard literals -----------------------------------------------------------
# Taken from the deployed Action Apps' own output enums, not invented. Verified with
# `uip maestro case tasks describe --type action --id <app> --output json`.

BUYER_DECISION_VALUES = {"approve", "reject", "sendback"}
COMPLIANCE_DECISION_VALUES = {"approve", "reject"}
BANK_VERIFIED_VALUE = "verified"

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
    "SupplierErpRegistration": "d5c07b08-d673-477c-b047-de330699a183",
}
AGENTS = {
    "SupplierOfferingCategoryMatch": "567afdb0-ee17-4c27-9b69-09b2bc7a34c8",
}
ACTION_APPS = {
    "Supplier Application Validation": "604acda5-8894-447f-b007-1989ec74a7e2",
    "supplier-document-upload": "e0145242-77aa-40b5-8752-e037ec022d40",
    "buyer-supplier-review-v2": "ec16bdfe-6f7b-4f4e-9988-70ee7c86b803",
    "Supplier Compliance Review": "1229c1ed-ca6b-4a89-9776-883bd0669684",
    "supplier-delay-escalation": "fb171d7c-33a1-4bb6-b09a-030044a7c0b6",
}
CHILD_CASES = {"SupplierContractNegotiation": "a028146a-e14f-489b-a6ca-e1ffa1d315f6"}

ALL_RESOURCE_IDS = set(API_WORKFLOWS.values()) | set(AGENTS.values()) \
    | set(ACTION_APPS.values()) | set(CHILD_CASES.values())          # 14

# The caseplan never carries a raw resource GUID. Each non-connector task binds its
# resource through a composite `resourceKey` of `<folderPath>.<name>`; the Outlook
# connector binds its connection UUID directly. These are what the plan actually holds,
# so these are what a grader can assert. The GUIDs above stay as the tenant-side
# identities the fixture pins and `sweep_guids.py` re-verifies.
RESOURCE_KEYS = {
    "Shared/uipath-maestro-case.buyer-supplier-review-v2": ("app", None),
    "Shared/uipath-maestro-case.supplier-delay-escalation": ("app", None),
    "Shared/uipath-maestro-case.supplier-document-upload": ("app", None),
    "Shared/uipath-maestro-case/Supplier Application Validation.Supplier Application Validation": ("app", None),
    "Shared/uipath-maestro-case/Supplier Compliance Review.Supplier Compliance Review": ("app", None),
    "Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierErpRegistration": ("process", "Api"),
    "Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierMasterScreeningLookup": ("process", "Api"),
    "Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierOfferingCategoryMatch": ("process", "Agent"),
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
    "bankVerificationStatus": ["Register supplier in ERP"],
    "buyerComments": ["Record buyer review decision"],
    "buyerDecision": ["Record buyer review decision"],
    "categoryMatches": ["Confirm offering category match"],
    "complianceComments": ["Record compliance review decision"],
    "complianceDecision": ["Record compliance review decision"],
    "duplicateSupplierIds": ["Pull supplier records and screening"],
    "escalationNotes": ["Escalate delayed application check"],
    "lastEmailStatus": ["Notify buyer of application", "Send delay note for the application check", "Send rejection notice to supplier", "Send supplier welcome message", "Send withdrawal confirmation"],
    "reviewNotes": ["Confirm offering category match"],
    "sanctionsFindings": ["Pull supplier records and screening"],
    "suggestedCategory": ["Confirm offering category match"],
    "supplierId": ["Register supplier in ERP"],
    "validationIssues": ["Validate application details"],
    "validationOutcome": ["Validate application details"],
}

# --- Recipients ---------------------------------------------------------------
# Type 3 is the runtime expression form. Roles carry no recipient in the caseplan at
# all: group assignment is configured in the Actions app, not here.

EXPRESSION_RECIPIENT_TASKS = {
    "Record buyer review decision",
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
CONNECTOR_TASK_COUNT = 5

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
    if len(xrefs) < 3:
        _fail(
            "fixture parse error: expected >=3 distinct $xref triples reading a task's "
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
    # A floor, not a count: it catches a regex that matched nothing, and stays well under
    # the real figure so trimming the case does not move it.
    if len(var_reads) < 20:
        _fail(
            f"fixture parse error: expected >=20 distinct vars.* reads; got {len(var_reads)}"
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
