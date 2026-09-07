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

STAGES: list[tuple[str, str, str]] = []  # filled from the fixture at the bottom of this file
PRIMARY_STAGES: set[str] = set()   # both filled from the fixture, below
SECONDARY_STAGES: set[str] = set()

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

STAGE_TASKS: dict[str, list[tuple[str, str, bool, bool]]] = {}  # from the fixture, below
TOTAL_TASKS = 0                     # both recomputed once STAGE_TASKS is filled
TASK_TYPE_COUNTS: dict[str, int] = {}

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

STAGE_SLA: dict[str, tuple[int, str]] = {}   # label -> (count, unit), from the fixture below
STAGE_SLA_TITLE: dict[str, str] = {}         # label -> the SLA rule title the SDD names
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
RESOURCE_KEYS: dict[str, tuple] = {}   # folder-qualified name -> (kind, version), below


OUTLOOK_CONNECTION_ID = "dd657127-91f5-4568-a3a3-c024bc03fb0f"
OUTLOOK_ACTIVITY_TYPE_ID = "c7ce0a96-2091-3d94-b16f-706ebb1eb351"
OUTLOOK_CONNECTOR_KEY = "uipath-microsoft-outlook365"

# The one task the child case runs, and the fact the parent must not wait for it.
CHILD_CASE_TASK = "Open contract negotiation case"
CHILD_CASE_WAITS = False

RUN_ONCE_TASKS: set[str] = set()    # filled with STAGE_TASKS, below

# --- Output reassigns ---------------------------------------------------------
# Every `-> <variable>` row in the fixture's task Output tables, keyed by the variable
# and listing the task(s) the SDD makes responsible for writing it. Asserting in this
# direction — "each declared target IS written by its task" — catches a dropped output.
# The reverse direction does not work: a task also carries auto-minted output slots
# whose `var` equals their own `id` and which deliberately live outside the case's
# variable namespace, so requiring every `var` to be a declared variable false-fails
# every connector task.

OUTPUT_TARGETS: dict[str, list[str]] = {}   # target variable -> the tasks the SDD makes write it


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


# A task's `**Inputs:**` table, keyed by the task display name its detail block sits under.
# Both binding kinds count. An expression is the obvious one; a literal is not safer — the
# escalation task's `stageName | String | Checking the application` came out `""` in the
# same build that dropped the expressions, so a delay note would have named no phase.
# `—` is the only cell that means there is nothing to bind.
_TASK_HEADING_RE = re.compile(r"^#{5}\s+Task\s+\S+:\s+(.+?)\s*$", re.M)
_INPUT_ROW_RE = re.compile(
    r"^\|\s*([A-Za-z][\w.]*)\s*\|\s*[A-Za-z][\w\[\] ]*\s*\|\s*([^|]*?)\s*\|", re.M
)
_NO_BINDING = {"", "—", "-", "n/a"}




_STAGE_HEADING_RE = re.compile(
    r"^### (?:Stage \d+|Secondary Stage): (.+?) \(`([a-z0-9_]+)`\)\s*$", re.M
)


def _sdd_stages(sdd: str) -> list[tuple[str, str, str]]:
    """(label, stage id, kind) for every stage the SDD declares, in document order.

    Read rather than listed, so a second fixture describing the same process with
    different stages needs no edit here. The floor below is what stops a regex that
    stopped matching from handing the checkers an empty case.
    """
    out = []
    for match in _STAGE_HEADING_RE.finditer(sdd):
        label, stage_id = match.group(1).strip(), match.group(2)
        kind = "secondary" if match.group(0).startswith("### Secondary") else "primary"
        out.append((label, stage_id, kind))
    return out


STAGES[:] = _sdd_stages(read_fixture())
if len(STAGES) < 5 or not any(k == "secondary" for _l, _i, k in STAGES):
    _fail(
        "fixture parse error: expected >=5 stage headings including at least one "
        f"secondary; got {STAGES}"
    )
PRIMARY_STAGES.update(label for label, _i, kind in STAGES if kind == "primary")
SECONDARY_STAGES.update(label for label, _i, kind in STAGES if kind == "secondary")

_SLA_TITLE_RE = re.compile(r"^\*\*SLA Title:\*\*\s*(.+?)\s*$", re.M)
_SLA_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|\s*(min|hour|day|days|hours)\s*\|", re.M)


def _sdd_stage_slas(sdd: str) -> tuple[dict, dict]:
    """Each stage's SLA duration and rule title, read off its own `#### Stage SLA` block.

    Scoped to the text between one stage heading and the next, so a stage with no SLA
    block contributes nothing rather than borrowing its neighbour's.
    """
    durations, titles = {}, {}
    marks = [(m.start(), m.group(1).strip()) for m in _STAGE_HEADING_RE.finditer(sdd)]
    for index, (start, label) in enumerate(marks):
        end = marks[index + 1][0] if index + 1 < len(marks) else len(sdd)
        body = sdd[start:end]
        if "#### Stage SLA" not in body:
            continue
        block = body.split("#### Stage SLA", 1)[1].split("\n#### ", 1)[0]
        title = _SLA_TITLE_RE.search(block)
        row = _SLA_ROW_RE.search(block)
        if title:
            titles[label] = title.group(1)
        if row:
            durations[label] = (int(row.group(1)), row.group(2))
    return durations, titles


_durations, _titles = _sdd_stage_slas(read_fixture())
if len(_durations) < 4:
    _fail(
        "fixture parse error: expected >=4 stages carrying a Stage SLA block with a "
        f"duration row; got {_durations}"
    )
STAGE_SLA.update(_durations)
STAGE_SLA_TITLE.update(_titles)

_TASK_LINE_RE = re.compile(r"^#{4,5} Task [\d.A-Z]+: (.+)$")
_TASK_TYPE_RE = re.compile(r"^\*\*Type:\*\*\s*(.+?)\s*$")


def _sdd_stage_tasks(sdd: str) -> dict:
    """Each stage's tasks as (display name, type, isRequired, shouldRunOnlyOnce).

    A task is only counted once its Task envelope row is reached, which is the row that
    carries Required and Run Only Once. That row is what closes the record, so a heading
    without an envelope contributes nothing instead of a half-filled tuple.
    """
    found: dict = {}
    marks = [(m.start(), m.group(1).strip()) for m in _STAGE_HEADING_RE.finditer(sdd)]
    for index, (start, label) in enumerate(marks):
        end = marks[index + 1][0] if index + 1 < len(marks) else len(sdd)
        rows, name, task_type = [], None, None
        for line in sdd[start:end].split("\n"):
            heading = _TASK_LINE_RE.match(line)
            if heading:
                name, task_type = heading.group(1).strip(), None
                continue
            if name and _TASK_TYPE_RE.match(line):
                task_type = _TASK_TYPE_RE.match(line).group(1)
                continue
            if not (name and task_type and line.startswith("|")):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) == 3 and cells[0] in ("Yes", "No") and cells[1] in ("Yes", "No"):
                rows.append((name, task_type, cells[0] == "Yes", cells[1] == "Yes"))
                name = None
        if rows:
            found[label] = rows
    return found


STAGE_TASKS.update(_sdd_stage_tasks(read_fixture()))
TOTAL_TASKS = sum(len(rows) for rows in STAGE_TASKS.values())
for _rows in STAGE_TASKS.values():
    for _n, _type, _r, _o in _rows:
        TASK_TYPE_COUNTS[_type] = TASK_TYPE_COUNTS.get(_type, 0) + 1
RUN_ONCE_TASKS.update(
    name for rows in STAGE_TASKS.values() for name, _t, _r, once in rows if once
)

_CONNECTION_ID_RE = re.compile(r"\*\*Connection ID:\*\*\s*([0-9a-f-]{36})")


def _task_field(body: str, label: str):
    """One `**Label:** value` line from a task block, with any trailing `· ...` dropped."""
    found = re.search(rf"^\*\*{re.escape(label)}:\*\*\s*(.+?)\s*(?:\u00b7.*)?$", body, re.M)
    return found.group(1).strip() if found else None


def _sdd_resource_keys(sdd: str) -> dict:
    """Every resource the tasks bind, keyed the way the caseplan binds it.

    Three shapes, because the SDD declares three: an action task names its Action App and
    its Deployment Folder, a child case names the case and its folder, and everything else
    names a Resolved Resource and a Folder Path. A connector binds its connection UUID
    instead of a folder-qualified name.
    """
    keys: dict = {}
    marks = [(m.start(), m.group(1).strip()) for m in _TASK_HEADING_RE.finditer(sdd)]
    for index, (start, _name) in enumerate(marks):
        end = marks[index + 1][0] if index + 1 < len(marks) else len(sdd)
        body = sdd[start:end]
        connection = _CONNECTION_ID_RE.search(body)
        if connection:
            keys[connection.group(1)] = ("Connection", None)
        app = _task_field(body, "HITL Implementation")
        child = _task_field(body, "Child Case")
        if app and app.startswith("Action App:"):
            name, folder, kind = app.split(":", 1)[1].strip(), _task_field(body, "Deployment Folder"), "app"
        elif child:
            name, folder, kind = child, _task_field(body, "Folder Path") or _task_field(body, "Deployment Folder"), None
        else:
            name, folder, kind = _task_field(body, "Resolved Resource"), _task_field(body, "Folder Path"), None
        if name and folder:
            keys[f"{folder}.{name}"] = (kind, None)
    return keys


RESOURCE_KEYS.update(_sdd_resource_keys(read_fixture()))
if len(RESOURCE_KEYS) < 10:
    _fail(
        "fixture parse error: expected >=10 bound resources across the task blocks; got "
        f"{sorted(RESOURCE_KEYS)}"
    )

_EXTRACT_ROW_RE = re.compile(r"^\|[^|]*\|\s*->\s*([A-Za-z]\w*)\s*\|", re.M)


def _sdd_output_targets(sdd: str) -> dict:
    """Every `-> <variable>` row in a task Outputs table, keyed by the variable.

    Asserted in this direction, "each declared target IS written by its task", so a
    dropped output row surfaces as a named task rather than as a silently smaller set.
    """
    targets: dict = {}
    marks = [(m.start(), m.group(1).strip()) for m in _TASK_HEADING_RE.finditer(sdd)]
    for index, (start, name) in enumerate(marks):
        end = marks[index + 1][0] if index + 1 < len(marks) else len(sdd)
        for match in _EXTRACT_ROW_RE.finditer(sdd, start, end):
            targets.setdefault(match.group(1), []).append(name)
    return targets


OUTPUT_TARGETS.update(_sdd_output_targets(read_fixture()))
if len(OUTPUT_TARGETS) < 15:
    _fail(
        "fixture parse error: expected >=15 distinct `->` output targets across the task "
        f"Outputs tables; got {sorted(OUTPUT_TARGETS)}"
    )
if TOTAL_TASKS < 20 or len(STAGE_TASKS) < 5:
    _fail(
        "fixture parse error: expected >=20 tasks across >=5 stages, each closed by its "
        f"Task envelope row; got {TOTAL_TASKS} across {len(STAGE_TASKS)}"
    )
def _bound_inputs(sdd: str) -> dict[str, set[str]]:
    """Which inputs each task binds to an expression, read off the fixture's own tables."""
    headings = [(m.start(), m.group(1).strip()) for m in _TASK_HEADING_RE.finditer(sdd)]
    bound: dict[str, set[str]] = {}
    for index, (start, name) in enumerate(headings):
        end = headings[index + 1][0] if index + 1 < len(headings) else len(sdd)
        block = sdd[start:end]
        # Two spellings, by task class: a process/agent/api-workflow block writes
        # `**Inputs:**`, an action block writes `**Input Schema:**`. The escalation task
        # is an action, and reading only the first spelling skipped it entirely.
        marker = -1
        for label in ("**Inputs:**", "**Input Schema:**"):
            found = block.find(label)
            if found >= 0 and (marker < 0 or found < marker):
                marker = found
        if marker < 0:
            continue
        # Only the run of table lines that follows the marker. Reading to the end of the
        # block swallows the next table — a persona roster and a connector roll-up both
        # follow — and every header cell then reads as a field name.
        fields: set[str] = set()
        seen_row = False
        for line in block[marker:].splitlines()[1:]:
            stripped = line.strip()
            if not stripped.startswith("|"):
                if seen_row:
                    break
                continue
            seen_row = True
            match = _INPUT_ROW_RE.match(stripped)
            if not match:
                continue
            field, binding = match.group(1), match.group(2)
            if field in {"Field", "Name"}:
                continue
            if binding.strip().strip("`").lower() in _NO_BINDING:
                continue
            fields.add(field)
        if fields:
            bound.setdefault(name, set()).update(fields)
    return bound


_RECIPIENT_RE = re.compile(r"^\*\*Recipient:\*\*\s*(.+?)\s*(?:·|$)", re.M)


def _sdd_recipients(sdd: str) -> dict[str, str]:
    """Task name -> the Recipient the SDD names for it.

    Only tasks the SDD actually routes somewhere. A task with no Recipient line is not
    in the result, so a plan is never asked to invent one.
    """
    headings = [(m.start(), m.group(1).strip()) for m in _TASK_HEADING_RE.finditer(sdd)]
    out: dict[str, str] = {}
    for index, (start, name) in enumerate(headings):
        end = headings[index + 1][0] if index + 1 < len(headings) else len(sdd)
        match = _RECIPIENT_RE.search(sdd, start, end)
        if match and match.group(1) not in _NO_BINDING:
            out[name] = match.group(1)
    return out


_CUSTOM_OUTPUT_RE = re.compile(
    r"^\|\s*(?:—|-|\s)*\s*\|\s*([A-Za-z][\w]*)\s*=\s*([^|]+?)\s*\|", re.M
)


def _sdd_custom_outputs(sdd: str) -> dict[str, list[str]]:
    """Task name -> the case variables its Outputs table assigns with `=`.

    An Outputs row shaped `| — | someVar = <expr> |` is a custom output: it writes a case
    variable rather than extracting a task field into one. `->` rows are the other kind and
    are covered elsewhere.
    """
    headings = [(m.start(), m.group(1).strip()) for m in _TASK_HEADING_RE.finditer(sdd)]
    out: dict[str, list[str]] = {}
    for index, (start, name) in enumerate(headings):
        end = headings[index + 1][0] if index + 1 < len(headings) else len(sdd)
        names = [m.group(1) for m in _CUSTOM_OUTPUT_RE.finditer(sdd, start, end)]
        if names:
            out.setdefault(name, []).extend(names)
    return out


_VAR_ROW_RE = re.compile(
    r"^\|\s*([A-Za-z][\w]*)\s*\|\s*(In|Out|Variable)\s*\|\s*(\w+)\s*\|"
    r"[^|]*\|[^|]*\|\s*([^|]*?)\s*\|",
    re.M,
)

# Category tells the build which of the three variable groups a row lands in, per
# `global-vars/impl-json.md` § Dispatcher. An `In` row is written twice: the formal
# slot under `inputs` and its companion under `inputOutputs`.
VAR_GROUP = {"In": "inputs", "Out": "outputs", "Variable": "inputOutputs"}


def _sdd_variables(sdd: str) -> dict[str, tuple[str, str, str]]:
    """Case Variables rows as name -> (category, type, default)."""
    body = sdd.split("### Case Variables", 1)[-1].split("\n## ", 1)[0]
    return {
        m.group(1): (m.group(2), m.group(3), m.group(4))
        for m in _VAR_ROW_RE.finditer(body)
    }


_RATIONALE_RE = re.compile(r"^\*\*Design Rationale:\*\*\s*(.+)$", re.M)
_ENVELOPE_RE = re.compile(r"^\|\s*(Yes|No)\s*\|\s*(Yes|No)\s*\|\s*([^|]*?)\s*\|", re.M)


def _sdd_task_envelopes(sdd: str) -> tuple[dict[str, str], dict[str, str]]:
    """Task name -> whether the SDD writes a Design Rationale, and its Skip Condition.

    The skill copies each task's Design Rationale into the element's `description`
    (`implementation.md` Completeness principle), so a task with a rationale and no
    description in the plan lost it.
    """
    rationale: dict[str, str] = {}
    skips: dict[str, str] = {}
    name = None
    for line in sdd.split("\n"):
        head = re.match(r"^#{4,5} Task [\d.A-Z]+: (.+)$", line)
        if head:
            name = head.group(1).strip()
            continue
        if not name:
            continue
        hit = _RATIONALE_RE.match(line)
        if hit:
            rationale[name] = hit.group(1).strip()
        row = _ENVELOPE_RE.match(line)
        if row and row.group(3) not in ("\u2014", "-", ""):
            skips[name] = row.group(3)
    return rationale, skips


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

    bound_inputs = _bound_inputs(sdd)
    recipients = _sdd_recipients(sdd)
    custom_outputs = _sdd_custom_outputs(sdd)
    if len(custom_outputs) < 4:
        raise SystemExit(
            f"expected.py: parsed only {len(custom_outputs)} task(s) with a custom `=` output "
            f"from sdd.md; the fixture declares more. Got {sorted(custom_outputs)}"
        )
    if len(recipients) < 10:
        raise SystemExit(
            f"expected.py: parsed only {len(recipients)} Recipient line(s) from sdd.md; the "
            f"fixture routes at least 10 tasks. Got {sorted(recipients)}"
        )
    # A floor, not a count. An agent shipped this case with all three of its agent task's
    # inputs emitted as "", the job faulted on `Field required [input_value={}]`, and every
    # grader stayed green — nothing was reading the input side at all.
    if len(bound_inputs) < 10:
        _fail(
            "fixture parse error: expected >=10 tasks with an `**Inputs:**` table binding an "
            f"expression; got {sorted(bound_inputs)}"
        )

    rationale_tasks, skip_conditions = _sdd_task_envelopes(sdd)
    if len(rationale_tasks) < 30 or not skip_conditions:
        _fail(
            "fixture parse error: expected >=30 tasks with a Design Rationale and at "
            f"least one Skip Condition; got {len(rationale_tasks)} and "
            f"{len(skip_conditions)}"
        )

    variables = _sdd_variables(sdd)
    if len(variables) < 40:
        _fail(
            "fixture parse error: expected >=40 Case Variables rows carrying a name, "
            f"category and type; got {len(variables)}"
        )

    return {
        "xrefs": xrefs,
        "guard_literals": literals,
        "connector_extracts": extracts,
        "var_reads": var_reads,
        "bound_inputs": bound_inputs,
        "recipients": recipients,
        "custom_outputs": custom_outputs,
        "variables": variables,
        "rationale_tasks": rationale_tasks,
        "skip_conditions": skip_conditions,
    }
