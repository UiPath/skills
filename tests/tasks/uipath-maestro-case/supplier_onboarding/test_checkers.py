#!/usr/bin/env python3
"""Offline behavioral tests for the SupplierOnboarding graders.

Takes a caseplan the graders accept, mutates ONE fact at a time, and asserts each
mutation is caught with the message that names it. An assertion that can never fail
is worth nothing and looks like coverage, so every finding a grader claims to make
gets a test that makes it happen.

Asserting on the message, not only the exit code, is deliberate: a mutation that
trips some *other* assertion would otherwise pass this suite while the assertion
under test stayed dead.

The plan comes from `build()` below — built in code, generated from a real
build, so the suite is self-contained and runs in CI. Committing a real caseplan.json
is not how this suite works: every grader unit test here builds its plan the same way.

Run: python3 -m unittest discover -s <this directory>
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
CHECKERS = {
    "topology": HERE / "check_topology.py",
    "guards": HERE / "check_guards.py",
    "sla": HERE / "check_sla.py",
    "tasks_io": HERE / "check_tasks_io.py",
    "fieldnames": HERE / "check_fieldnames.py",
    "variables": HERE / "check_variables.py",
    "metadata": HERE / "check_metadata.py",
}

sys.path.insert(0, str(HERE))
import expected as E  # noqa: E402


# ----------------------------------------------------------------------------
# The baseline plan, built in code.
#
#
# `test_checkers.py` needs a plan it can break one fact at a time. Committing a real
# `caseplan.json` is not how this suite works — every grader unit test here builds its
# plan in code (see `sla_from_sdd/test_check_sla_from_sdd.py`) — so this module is that
# plan for a case of this size.
#
# **The tables below were generated from a real build, not written from memory.** Every
# field name in them was read off a caseplan that passes `uip maestro case validate` and
# all five graders. That matters more here than usual: while writing the graders, the
# emitted shape turned out to differ from the obvious guess in eight places, and each
# wrong guess produced either a false failure on a correct build or an assertion that
# could never fire at all. The ones worth naming:
#
#   * `skipCondition` sits at the TASK's top level, not under `data`.
#   * A connector task's input expression is nested inside `inputs[].body`; a
#     non-connector task's is a plain `inputs[].value`.
#   * The plan carries no resource GUIDs. A non-connector task binds through a composite
#     `resourceKey` of `<folderPath>.<name>`.
#   * An output's reassign target is `var` alone. `target` and `originalVar` hold the
#     wire's own id and are deliberately outside the case's variable namespace.
#   * `selected-tasks-completed` names its tasks in `selectedTasksIds` — plural on BOTH
#     words.
#   * `sla-status-change` names the SLA in `slaId` and carries no stage reference.
#   * The case's own SLA lives at `metadata.slaRules`; its exits at
#     `metadata.caseExitRules`, keyed `marksCaseComplete`.
#   * A connector output's `displayName` may be PascalCase (`Response`) while its wire
#     path stays lowercase (`response.status`). The label is not part of the contract.
#
# Regenerate from a fresh build after any fixture change.
#
# Input expressions are shortened to the reads they carry: the graders assert which
# variables an expression touches, never its prose, so `"Dear " + vars.contactName + …`
# becomes `=js:(vars.contactName)`. Everything a grader reads is preserved exactly.
# ----------------------------------------------------------------------------

CASE_ID = "case_SupplierOnboarding"
CASE_NAME = "SupplierOnboarding"
CASE_VERSION = "30.0.0"


def T(
    task_id: str,
    task_type: str,
    display_name: str,
    *,
    req: bool = False,
    once: bool = False,
    entry: list | None = None,
    skip: str | None = None,
    recipient: dict | None = None,
    literals: dict | None = None,
    reads: list[str] | None = None,
    raw: dict | None = None,
    outputs: list[tuple] | None = None,
) -> dict:
    """One task, in the shape the graders read.

    `reads` becomes one `=js:(...)` input carrying exactly those references, plus a
    `body`-nested copy for connector tasks so both input placements are exercised.
    `literals` becomes plain-string inputs — that is how `stageName` is carried.
    `raw` carries a whole expression verbatim, for the one task whose real expression
    shape is itself under assertion (the guarded walk over the supporting documents).
    """
    inputs: list[dict] = []
    if literals:
        inputs.extend(
            {"name": name, "type": "string", "value": value}
            for name, value in literals.items()
        )
    if raw:
        inputs.extend(
            {"name": name, "type": "string", "value": value}
            for name, value in raw.items()
        )
    if reads:
        expression = "=js:(" + " + ".join(reads) + ")"
        if task_type in ("execute-connector-activity", "wait-for-connector"):
            inputs.append(
                {"name": "body", "type": "jsonSchema",
                 "body": {"message": {"body": {"content": expression}}}}
            )
        else:
            inputs.append({"name": "Content", "type": "string", "value": expression})

    data: dict = {"inputs": inputs, "outputs": [
        {
            "name": name,
            "id": out_id,
            "var": var,
            "source": source,
            **({"displayName": label} if label else {}),
        }
        for name, out_id, var, source, label in (outputs or [])
    ]}
    if recipient is not None:
        data["recipient"] = recipient
    if task_type in ("execute-connector-activity", "wait-for-connector"):
        # `task_is_skeleton` reads a non-empty `context` for this class, and the
        # activity type names which operation of the connector the task runs. A real
        # build nests that id inside a context entry's `body`.
        data["context"] = [
            {"name": "connectionId", "type": "string", "value": "conn"},
            {"name": "activity", "type": "jsonSchema", "body": {
                "activityMetadata": {"activity": {
                    "uiPathActivityTypeId": E.OUTLOOK_ACTIVITY_TYPE_ID}}}},
        ]
        data["serviceType"] = "Intsvc.ActivityExecution"
    else:
        data["name"] = "=bindings.b" + task_id[:6]
        data["folderPath"] = "=bindings.b" + task_id[:6] + "f"

    task: dict = {
        "id": task_id,
        "type": task_type,
        "displayName": display_name,
        # A real build copies the SDD's Design Rationale here verbatim, on every task.
        "description": E.sdd_facts()["rationale_tasks"].get(display_name, ""),
        "isRequired": req,
        "shouldRunOnlyOnce": once,
        "entryConditions": [
            {
                "id": f"c_{task_id}",
                # A real build gives each rule its own name, and the CLI requires it:
                # two rules sharing one inside a stage answer
                # CASE_MGMT_RULE_NAME_DUPLICATE. Observed on a real caseplan, where a
                # task whose SDD row said `Stage enters` was written
                # `Stage enters - category match`.
                "displayName": f"entry {task_id} {i}",
                "rules": [[{"id": f"r_{task_id}_{i}", "rule": rule, **(fields or {})}]],
            }
            for i, (rule, fields) in enumerate(entry or [])
        ],
        "data": data,
    }
    if skip:
        task["skipCondition"] = skip
    return task


def _cond(row: tuple) -> dict:
    cid, name, interrupting, cond_type, marks, exit_to, rules = row
    out: dict = {
        "id": cid,
        "displayName": name,
        "rules": [
            [{"id": f"{cid}_r{i}", "rule": rule, **(fields or {})}]
            for i, (rule, fields) in enumerate(rules)
        ],
    }
    if interrupting is not None:
        out["isInterrupting"] = interrupting
    if cond_type is not None:
        out["type"] = cond_type
    if marks is not None:
        out["marksStageComplete"] = marks
    if exit_to is not None:
        out["exitToStageId"] = exit_to
    return out


def _sla(row: tuple) -> dict:
    sla_id, count, unit, escalations = row
    return {
        "id": sla_id,
        "displayName": sla_id,
        "expression": "=js:true",
        "count": count,
        "unit": unit,
        "escalationRule": [
            {
                "id": esc_id,
                "displayName": esc_id,
                "action": {
                    "type": action,
                    "recipients": [
                        {"scope": scope, "target": target, "value": value}
                        for scope, target, value in recipients
                    ],
                },
                "triggerInfo": {
                    "type": trigger,
                    **({"atRiskPercentage": pct} if pct is not None else {}),
                },
            }
            for esc_id, trigger, pct, action, recipients in escalations
        ],
    }


def S(
    stage_id: str,
    label: str,
    stage_type: str | None,
    *,
    slas: list[tuple],
    entry: list[tuple],
    exits: list[tuple],
    lanes: list[list[str]],
) -> dict:
    data: dict = {
        "label": label,
        "entryConditions": [_cond(r) for r in entry],
        "exitConditions": [_cond(r) for r in exits],
        "tasks": lanes,          # task ids; build() swaps in the objects
    }
    if stage_type:
        data["stageType"] = stage_type
    if slas:
        data["slaRules"] = [_sla(r) for r in slas]
    return {"id": stage_id, "type": "case-management:Stage", "data": data}

# --- Tasks, generated from a real build -----------------------------------------
TASKS = [
    # --- Checking the application ---
    T('tVal01aXk', 'action', 'Validate application details',
      req=True, once=False, entry=[('runs-sequentially', None)],
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.contactName', 'vars.contactEmail', 'vars.countryOfRegistration', 'vars.offeringCategory', 'vars.expectedAnnualSpend', 'vars.spendCurrency', 'vars.submittedDate', 'vars.offeringDescription', 'vars.validationIssues'],
      outputs=[('Action', 'action', 'validationOutcome', '=Action', None), ('Comment', 'comment', 'validationIssues', '=Comment', None)]),
    T('tPul02bYm', 'api-workflow', 'Pull supplier records and screening',
      req=True, once=False, entry=[('runs-sequentially', None)],
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.countryOfRegistration', 'vars.offeringCategory'],
      outputs=[('duplicateSupplierIds', 'duplicateSupplierIds', 'duplicateSupplierIds', '=duplicateSupplierIds', None), ('sanctionsFindings', 'sanctionsFindings', 'sanctionsFindings', '=sanctionsFindings', None), ('assignedBuyerEmail', 'assignedBuyerEmail', 'assignedBuyerEmail', '=assignedBuyerEmail', None)]),
    T('tCat03cZn', 'agent', 'Confirm offering category match',
      req=False, once=False, entry=[('current-stage-entered', None)],
      reads=['vars.offeringDescription', 'vars.offeringCategory', 'vars.registrationCertificate', 'vars.insuranceDocument', 'vars.taxFormsDocument', 'vars.bankDetailsDocument'],
      raw={'submittedDocuments': '=js:([["Registration certificate", vars.registrationCertificate], ["Insurance", vars.insuranceDocument], ["Tax forms", vars.taxFormsDocument], ["Bank details", vars.bankDetailsDocument]].filter(function (p) { return p[1] && p[1].FullName; }).map(function (p) { return p[0] + ": " + p[1].FullName; }).join("; ") || "None attached")'},
      outputs=[('categoryMatches', 'categoryMatches', 'categoryMatches', '=categoryMatches', None), ('suggestedCategory', 'suggestedCategory', 'suggestedCategory', '=suggestedCategory', None), ('reviewNotes', 'reviewNotes', 'reviewNotes', '=reviewNotes', None)]),
    T('tDoc04dAp', 'action', 'Attach supporting documents',
      req=False, once=False, entry=[('adhoc', None)],
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.validationIssues'],
      outputs=[('documentType', 'documentType', 'addedDocumentType', '=documentType', None), ('documentFileName', 'documentFileName', 'addedDocumentName', '=documentFileName', None), ('documentContentBase64', 'documentContentBase64', 'addedDocumentContent', '=documentContentBase64', None), ('submittedOn', 'submittedOn', 'addedDocumentSubmittedOn', '=submittedOn', None)]),
    T('tEscChk01', 'action', 'Escalate delayed application check',
      req=False, once=False, entry=[('sla-status-change', {'slaId': 'sla_ChkStg01'})],
      literals={'stageName': 'Checking the application', 'daysOverdue': '0'},
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.offeringCategory', 'vars.assignedBuyerEmail', 'vars.submittedDate', 'vars.contactName', 'vars.contactEmail', 'vars.escalationNotes'],
      outputs=[('newExpectedDate', 'newExpectedDate', 'applicationCheckRevisedDate', '=newExpectedDate', None), ('Comment', 'comment8', 'escalationNotes', '=Comment', None)]),
    T('tNteChk02', 'execute-connector-activity', 'Send delay note for the application check',
      req=False, once=False, entry=[('selected-tasks-completed', {'selectedTasksIds': ['tEscChk01']})],
      reads=['vars.contactEmail', 'vars.companyName', 'vars.contactName', 'vars.applicationCheckRevisedDate', 'metadata.ExternalId'],
      outputs=[('response', 'response5', 'response5', '=response', 'Response'), ('Error', 'error5', 'error5', '=Error', 'Error'), ('Status', 'status5', 'lastEmailStatus', '=response.status', None)]),
    # --- Buyer review ---
    T('tNtf05eBq', 'execute-connector-activity', 'Notify buyer of application',
      req=True, once=False, entry=[('runs-sequentially', None)],
      reads=['vars.assignedBuyerEmail', 'metadata.ExternalId', 'vars.companyName', 'vars.countryOfRegistration', 'vars.offeringCategory', 'vars.expectedAnnualSpend', 'vars.spendCurrency', 'vars.offeringDescription', 'vars.categoryMatches', 'vars.suggestedCategory', 'vars.reviewNotes', 'vars.sanctionsFindings', 'vars.duplicateSupplierIds'],
      outputs=[('response', 'response', 'response', '=response', 'Response'), ('Error', 'error', 'error', '=Error', 'Error'), ('Status', 'status', 'lastEmailStatus', '=response.status', None)]),
    T('tByr06fCr', 'action', 'Record buyer review decision',
      req=True, once=False, entry=[('runs-sequentially', None)],
      recipient={'Type': 3, 'Value': '=vars.assignedBuyerEmail'},
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.contactName', 'vars.contactEmail', 'vars.countryOfRegistration', 'vars.offeringCategory', 'vars.expectedAnnualSpend', 'vars.spendCurrency', 'vars.offeringDescription', 'vars.validationOutcome', 'vars.validationIssues', 'vars.addedDocumentName', 'vars.duplicateSupplierIds', 'vars.sanctionsFindings', 'vars.categoryMatches', 'vars.suggestedCategory', 'vars.reviewNotes', 'vars.referenceCheckFindings', 'vars.buyerComments'],
      outputs=[('Action', 'action2', 'buyerDecision', '=Action', None), ('Comment', 'comment2', 'buyerComments', '=Comment', None)]),
    T('tInf07gDs', 'action', 'Request more information from supplier',
      req=False, once=False, entry=[('adhoc', None)],
      recipient={'Type': 3, 'Value': '=vars.assignedBuyerEmail'},
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.contactName', 'vars.contactEmail', 'vars.offeringDescription', 'vars.buyerComments'],
      outputs=[('Comment', 'comment3', 'buyerComments', '=Comment', None)]),
    T('tRef08hEt', 'action', 'Order reference check',
      req=False, once=False, entry=[('adhoc', None)],
      recipient={'Type': 3, 'Value': '=vars.assignedBuyerEmail'},
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.countryOfRegistration', 'vars.offeringCategory', 'vars.contactName', 'vars.referenceCheckFindings'],
      outputs=[('Comment', 'comment4', 'referenceCheckFindings', '=Comment', None)]),
    T('tEscByr01', 'action', 'Escalate delayed buyer review',
      req=False, once=False, entry=[('sla-status-change', {'slaId': 'sla_ByrStg01'})],
      literals={'stageName': 'Buyer review', 'daysOverdue': '0'},
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.offeringCategory', 'vars.assignedBuyerEmail', 'vars.submittedDate', 'vars.contactName', 'vars.contactEmail', 'vars.escalationNotes'],
      outputs=[('newExpectedDate', 'newExpectedDate2', 'buyerReviewRevisedDate', '=newExpectedDate', None), ('Comment', 'comment10', 'escalationNotes', '=Comment', None)]),
    T('tNteByr02', 'execute-connector-activity', 'Send delay note for the buyer review',
      req=False, once=False, entry=[('selected-tasks-completed', {'selectedTasksIds': ['tEscByr01']})],
      reads=['vars.contactEmail', 'vars.companyName', 'vars.contactName', 'vars.buyerReviewRevisedDate', 'metadata.ExternalId'],
      outputs=[('response', 'response6', 'response6', '=response', 'Response'), ('Error', 'error6', 'error6', '=Error', 'Error'), ('Status', 'status6', 'lastEmailStatus', '=response.status', None)]),
    # --- Compliance and risk review ---
    T('tCrc09jFu', 'api-workflow', 'Run compliance and risk check',
      req=True, once=False, entry=[('runs-sequentially', None)],
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.countryOfRegistration', 'vars.sanctionsFindings', 'vars.duplicateSupplierIds'],
      outputs=[('riskRating', 'riskRating', 'riskRating', '=riskRating', None), ('complianceFlags', 'complianceFlags', 'complianceFlags', '=complianceFlags', None)]),
    T('tTie10kGv', 'api-workflow', 'Determine sign-off tier',
      req=True, once=False, entry=[('runs-sequentially', None)],
      reads=['vars.expectedAnnualSpend', 'vars.spendCurrency'],
      outputs=[('signOffTier', 'signOffTier', 'signOffTier', '=signOffTier', None), ('directorSignOffRequired', 'directorSignOffRequired', 'directorSignOffRequired', '=directorSignOffRequired', None)]),
    T('tDir11mHw', 'action', 'Obtain procurement director sign-off',
      req=False, once=False, entry=[('selected-tasks-completed', {'selectedTasksIds': ['tTie10kGv'], 'conditionExpression': '=js:vars.directorSignOffRequired === true'})],
      skip='=js:vars.expectedAnnualSpend < 500000',
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.countryOfRegistration', 'vars.offeringCategory', 'vars.expectedAnnualSpend', 'vars.spendCurrency', 'vars.signOffTier', 'vars.riskRating', 'vars.complianceFlags', 'vars.financialHealthSummary', 'vars.fraudIndicators', 'vars.concernLevel', 'vars.buyerComments', 'vars.directorSignOffNotes'],
      outputs=[('Action', 'action3', 'directorSignOffDecision', '=Action', None), ('Comment', 'comment5', 'directorSignOffNotes', '=Comment', None)]),
    T('tCmp12nJx', 'action', 'Record compliance review decision',
      req=True, once=False, entry=[('selected-tasks-completed', {'selectedTasksIds': ['tDir11mHw']}), ('selected-tasks-completed', {'selectedTasksIds': ['tTie10kGv'], 'conditionExpression': '=js:vars.directorSignOffRequired === false'})],
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.contactName', 'vars.contactEmail', 'vars.countryOfRegistration', 'vars.offeringCategory', 'vars.expectedAnnualSpend', 'vars.spendCurrency', 'vars.riskRating', 'vars.complianceFlags', 'vars.sanctionsFindings', 'vars.duplicateSupplierIds', 'vars.financialHealthSummary', 'vars.fraudIndicators', 'vars.concernLevel', 'vars.signOffTier', 'vars.directorSignOffDecision', 'vars.directorSignOffNotes', 'vars.buyerComments', 'vars.referenceCheckFindings', 'vars.legalOpinion', 'vars.complianceComments'],
      outputs=[('Action', 'action4', 'complianceDecision', '=Action', None), ('Comment', 'comment6', 'complianceComments', '=Comment', None)]),
    T('tFin13pKy', 'agent', 'Analyze supplier financial health',
      req=False, once=False, entry=[('current-stage-entered', None)],
      reads=['vars.companyName', 'vars.countryOfRegistration', 'vars.expectedAnnualSpend', 'vars.spendCurrency', 'vars.offeringDescription'],
      outputs=[('financialHealthSummary', 'financialHealthSummary', 'financialHealthSummary', '=financialHealthSummary', None), ('fraudIndicators', 'fraudIndicators', 'fraudIndicators', '=fraudIndicators', None), ('concernLevel', 'concernLevel', 'concernLevel', '=concernLevel', None)]),
    T('tLgl14qLz', 'action', 'Obtain legal opinion',
      req=False, once=False, entry=[('adhoc', None)],
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.countryOfRegistration', 'vars.offeringCategory', 'vars.offeringDescription', 'vars.riskRating', 'vars.complianceFlags', 'vars.legalOpinion'],
      outputs=[('Comment', 'comment7', 'legalOpinion', '=Comment', None)]),
    T('tEscCmp01', 'action', 'Escalate delayed compliance review',
      req=False, once=False, entry=[('sla-status-change', {'slaId': 'sla_CmpStg01'})],
      literals={'stageName': 'Compliance and risk review', 'daysOverdue': '0'},
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.offeringCategory', 'vars.assignedBuyerEmail', 'vars.submittedDate', 'vars.contactName', 'vars.contactEmail', 'vars.escalationNotes'],
      outputs=[('newExpectedDate', 'newExpectedDate3', 'complianceReviewRevisedDate', '=newExpectedDate', None), ('Comment', 'comment11', 'escalationNotes', '=Comment', None)]),
    T('tNteCmp02', 'execute-connector-activity', 'Send delay note for the compliance review',
      req=False, once=False, entry=[('selected-tasks-completed', {'selectedTasksIds': ['tEscCmp01']})],
      reads=['vars.contactEmail', 'vars.companyName', 'vars.contactName', 'vars.complianceReviewRevisedDate', 'metadata.ExternalId'],
      outputs=[('response', 'response7', 'response7', '=response', 'Response'), ('Error', 'error7', 'error7', '=Error', 'Error'), ('Status', 'status7', 'lastEmailStatus', '=response.status', None)]),
    # --- Setting up the supplier ---
    T('tBnk14qLz', 'action', 'Provide bank details for payment setup',
      req=True, once=False, entry=[('runs-sequentially', None)],
      reads=['metadata.ExternalId', 'vars.companyName'],
      literals={'requestedDocuments': '=js:(["Bank details"])'},
      outputs=[('documentFileName', 'documentFileName', 'bankDetailsFileName', '=documentFileName', None),
               ('documentType', 'documentType', 'bankDetailsDocumentType', '=documentType', None),
               ('documentContentBase64', 'documentContentBase64', 'bankDetailsContent',
                '=documentContentBase64', None)]),
    T('tErp15rMa', 'api-workflow', 'Register supplier in ERP',
      req=True, once=True, entry=[('runs-sequentially', None)],
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.contactName', 'vars.contactEmail', 'vars.countryOfRegistration', 'vars.spendCurrency', 'vars.bankDetailsDocument'],
      outputs=[('supplierId', 'supplierId', 'supplierId', '=supplierId', None), ('bankVerificationStatus', 'bankVerificationStatus', 'bankVerificationStatus', '=bankVerificationStatus', None)]),
    T('tNeg16sNb', 'case-management', 'Open contract negotiation case',
      req=False, once=True, entry=[('runs-sequentially', {'conditionExpression': '=js:vars.bankVerificationStatus === "verified"'})],
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.expectedAnnualSpend', 'vars.spendCurrency'],
      outputs=[]),
    T('tPrt17tPc', 'action', 'Confirm supplier portal access',
      req=True, once=True, entry=[('runs-sequentially', {'conditionExpression': '=js:vars.bankVerificationStatus === "verified"'})],
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.supplierId', 'vars.portalAccessConfirmation'],
      outputs=[('Action', 'action5', 'portalAccessConfirmation', '=Action', None)]),
    T('tEscSet01', 'action', 'Escalate delayed supplier setup',
      req=False, once=False, entry=[('sla-status-change', {'slaId': 'sla_SetStg01'})],
      literals={'stageName': 'Setting up the supplier', 'daysOverdue': '0'},
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.offeringCategory', 'vars.assignedBuyerEmail', 'vars.submittedDate', 'vars.contactName', 'vars.contactEmail', 'vars.escalationNotes'],
      outputs=[('newExpectedDate', 'newExpectedDate4', 'supplierSetupRevisedDate', '=newExpectedDate', None), ('Comment', 'comment12', 'escalationNotes', '=Comment', None)]),
    T('tNteSet02', 'execute-connector-activity', 'Send delay note for the supplier setup',
      req=False, once=False, entry=[('selected-tasks-completed', {'selectedTasksIds': ['tEscSet01']})],
      reads=['vars.contactEmail', 'vars.companyName', 'vars.contactName', 'vars.supplierSetupRevisedDate', 'metadata.ExternalId'],
      outputs=[('response', 'response8', 'response8', '=response', 'Response'), ('Error', 'error8', 'error8', '=Error', 'Error'), ('Status', 'status8', 'lastEmailStatus', '=response.status', None)]),
    # --- Supplier onboarded ---
    T('tWlc18uQd', 'execute-connector-activity', 'Send supplier welcome message',
      req=True, once=True, entry=[('current-stage-entered', None)],
      reads=['vars.contactEmail', 'vars.companyName', 'vars.contactName', 'vars.supplierId', 'metadata.ExternalId'],
      outputs=[('response', 'response2', 'response2', '=response', 'Response'), ('Error', 'error2', 'error2', '=Error', 'Error'), ('Status', 'status2', 'lastEmailStatus', '=response.status', None), ('caseOutcome', None, 'caseOutcome', 'Onboarded', None)]),
    T('tReg19vRe', 'api-workflow', 'Record supplier in approved register',
      req=True, once=True, entry=[('current-stage-entered', None)],
      reads=['metadata.ExternalId', 'vars.supplierId', 'vars.companyName'],
      outputs=[('registeredAt', 'registeredAt', 'registeredAt', '=registeredAt', None), ('caseOutcome', None, 'caseOutcome', 'Onboarded', None)]),
    # --- Application rejected ---
    T('tRjn20wSf', 'execute-connector-activity', 'Send rejection notice to supplier',
      req=True, once=True, entry=[('current-stage-entered', None)],
      reads=['vars.contactEmail', 'vars.companyName', 'vars.contactName', 'vars.buyerDecision', 'vars.buyerComments', 'vars.complianceDecision', 'vars.complianceComments', 'metadata.ExternalId'],
      outputs=[('response', 'response3', 'response3', '=response', 'Response'), ('Error', 'error3', 'error3', '=Error', 'Error'), ('Status', 'status3', 'lastEmailStatus', '=response.status', None), ('caseOutcome', None, 'caseOutcome', 'Rejected', None)]),
    T('tAud21xTg', 'api-workflow', 'Log rejection for audit',
      req=True, once=True, entry=[('current-stage-entered', None)],
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.buyerDecision', 'vars.complianceDecision', 'vars.buyerComments', 'vars.complianceComments'],
      outputs=[('auditRecordId', 'auditRecordId', 'auditRecordId', '=auditRecordId', None), ('caseOutcome', None, 'caseOutcome', 'Rejected', None)]),
    # --- Application withdrawn ---
    T('tWdc22yUh', 'execute-connector-activity', 'Send withdrawal confirmation',
      req=True, once=True, entry=[('current-stage-entered', None)],
      reads=['vars.contactEmail', 'vars.companyName', 'vars.contactName', 'metadata.ExternalId'],
      outputs=[('response', 'response4', 'response4', '=response', 'Response'), ('Error', 'error4', 'error4', '=Error', 'Error'), ('Status', 'status4', 'lastEmailStatus', '=response.status', None), ('caseOutcome', None, 'caseOutcome', 'Withdrawn', None)]),
    T('tWcl23zVj', 'api-workflow', 'Close out withdrawn application',
      req=True, once=True, entry=[('current-stage-entered', None)],
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.contactEmail'],
      outputs=[('reviewsCancelled', 'reviewsCancelled', 'reviewsCancelled', '=reviewsCancelled', None), ('timersStopped', 'timersStopped', 'timersStopped', '=timersStopped', None), ('cleanupSummary', 'cleanupSummary', 'cleanupSummary', '=cleanupSummary', None), ('caseOutcome', None, 'caseOutcome', 'Withdrawn', None)]),
    # --- Overall SLA review ---
    T('tOvr26cYn', 'action', 'Review overall SLA breach',
      req=True, once=True, entry=[('current-stage-entered', None)],
      literals={'stageName': 'Overall case', 'daysOverdue': '0'},
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.submittedDate', 'vars.offeringCategory', 'vars.assignedBuyerEmail', 'vars.validationOutcome', 'vars.buyerDecision', 'vars.complianceDecision', 'vars.bankVerificationStatus', 'vars.escalationNotes'],
      outputs=[('Comment', 'comment9', 'escalationNotes', '=Comment', None)]),
]

# --- Stages, generated from a real build ----------------------------------------
STAGES = [
    S('Stage_Chk4kA', 'Checking the application', None,
      slas=[('sla_ChkStg01', *E.STAGE_SLA[E.CHECKING], [('esc_ck01ar', 'at-risk', E.STAGE_AT_RISK_PERCENT, 'notification', [('UserGroup', '93a89c1e-be35-410f-ae37-cc5a0e1bd4c2', 'Procurement Operations')]), ('esc_ck02br', 'sla-breached', None, 'notification', [('UserGroup', 'afa0eb1e-0874-47bc-9ce6-8e4c5869de39', 'Procurement Operations Lead')])])],
      entry=[('Condition_ck01en', 'Application submitted', False, None, None, None, [('case-entered', None)]), ('Condition_ck02en', 'Returned for corrections', False, None, None, None, [('selected-stage-exited', {'selectedStageIds': ['Stage_Byr7mC'], 'conditionExpression': '=js:vars.action2 === "sendback"'})])],
      exits=[('Condition_ck01ex', 'Checks complete', None, 'wait-for-user', True, None, [('required-tasks-completed', None)])],
      lanes=[['tVal01aXk'], ['tPul02bYm'], ['tCat03cZn'], ['tDoc04dAp'], ['tEscChk01'], ['tNteChk02']]),
    S('Stage_Byr7mC', 'Buyer review', None,
      slas=[('sla_ByrStg01', *E.STAGE_SLA[E.BUYER], [('esc_by01ar', 'at-risk', E.STAGE_AT_RISK_PERCENT, 'notification', [('UserGroup', '74c6d5cc-0684-4ff4-9537-1c80681ad9e8', 'Category Management')]), ('esc_by02br', 'sla-breached', None, 'notification', [('UserGroup', 'afa0eb1e-0874-47bc-9ce6-8e4c5869de39', 'Procurement Operations Lead')])])],
      entry=[('Condition_by01en', 'Checks passed', False, None, None, None, [('selected-stage-completed', {'selectedStageIds': ['Stage_Chk4kA']})])],
      exits=[('Condition_by01ex', 'Buyer declined', None, 'exit-only', False, 'Stage_Rej5rG', [('selected-tasks-completed', {'selectedTasksIds': ['tByr06fCr'], 'conditionExpression': '=js:vars.action2 === "reject"'})]), ('Condition_by02ex', 'Sent back for corrections', None, 'exit-only', False, 'Stage_Chk4kA', [('selected-tasks-completed', {'selectedTasksIds': ['tByr06fCr'], 'conditionExpression': '=js:vars.action2 === "sendback"'})]), ('Condition_by03ex', 'Buyer approved', None, 'wait-for-user', True, None, [('required-tasks-completed', {'conditionExpression': '=js:vars.buyerDecision === "approve"'})])],
      lanes=[['tNtf05eBq'], ['tByr06fCr'], ['tInf07gDs'], ['tRef08hEt'], ['tEscByr01'], ['tNteByr02']]),
    S('Stage_Cmp3nD', 'Compliance and risk review', None,
      slas=[('sla_CmpStg01', *E.STAGE_SLA[E.COMPLIANCE], [('esc_cm01ar', 'at-risk', E.STAGE_AT_RISK_PERCENT, 'notification', [('UserGroup', 'e158a23e-f553-4107-82d5-68b788134d33', 'Compliance')]), ('esc_cm02br', 'sla-breached', None, 'notification', [('UserGroup', 'afa0eb1e-0874-47bc-9ce6-8e4c5869de39', 'Procurement Operations Lead')])])],
      entry=[('Condition_cm01en', 'Buyer approved', False, None, None, None, [('selected-stage-completed', {'selectedStageIds': ['Stage_Byr7mC'], 'conditionExpression': '=js:vars.buyerDecision === "approve"'})])],
      exits=[('Condition_cm01ex', 'Compliance rejected', None, 'exit-only', False, 'Stage_Rej5rG', [('selected-tasks-completed', {'selectedTasksIds': ['tCmp12nJx'], 'conditionExpression': '=js:vars.action4 === "reject"'})]), ('Condition_cm02ex', 'Sent to setup', None, 'wait-for-user', True, None, [('required-tasks-completed', {'conditionExpression': '=js:vars.complianceDecision === "approve"'})])],
      lanes=[['tCrc09jFu'], ['tTie10kGv'], ['tDir11mHw'], ['tCmp12nJx'], ['tFin13pKy'], ['tLgl14qLz'], ['tEscCmp01'], ['tNteCmp02']]),
    S('Stage_Set8pE', 'Setting up the supplier', None,
      slas=[('sla_SetStg01', *E.STAGE_SLA[E.SETUP], [('esc_st01ar', 'at-risk', E.STAGE_AT_RISK_PERCENT, 'notification', [('UserGroup', '93a89c1e-be35-410f-ae37-cc5a0e1bd4c2', 'Procurement Operations')]), ('esc_st02br', 'sla-breached', None, 'notification', [('UserGroup', 'afa0eb1e-0874-47bc-9ce6-8e4c5869de39', 'Procurement Operations Lead')])])],
      entry=[('Condition_st01en', 'Compliance approved', False, None, None, None, [('selected-stage-completed', {'selectedStageIds': ['Stage_Cmp3nD'], 'conditionExpression': '=js:vars.complianceDecision === "approve"'})])],
      exits=[('Condition_st01ex', 'Bank verification failed', None, 'exit-only', False, 'Stage_Rej5rG', [('selected-tasks-completed', {'selectedTasksIds': ['tErp15rMa'], 'conditionExpression': '=js:vars.bankVerificationStatus !== "verified"'})]), ('Condition_st02ex', 'Setup complete', None, 'exit-only', True, None, [('required-tasks-completed', {'conditionExpression': '=js:vars.bankVerificationStatus === "verified"'})])],
      lanes=[['tBnk14qLz'], ['tErp15rMa'], ['tNeg16sNb', 'tPrt17tPc'], ['tEscSet01'], ['tNteSet02']]),
    S('Stage_Onb2qF', 'Supplier onboarded', None,
      slas=[('sla_OnbStg01', *E.STAGE_SLA[E.ONBOARDED], [('esc_on01ar', 'at-risk', E.STAGE_AT_RISK_PERCENT, 'notification', [('UserGroup', '93a89c1e-be35-410f-ae37-cc5a0e1bd4c2', 'Procurement Operations')]), ('esc_on02br', 'sla-breached', None, 'notification', [('UserGroup', 'afa0eb1e-0874-47bc-9ce6-8e4c5869de39', 'Procurement Operations Lead')])])],
      entry=[('Condition_on01en', 'Setup complete', False, None, None, None, [('selected-stage-completed', {'selectedStageIds': ['Stage_Set8pE']})])],
      exits=[('Condition_on01ex', 'Onboarding complete', None, 'exit-only', True, None, [('required-tasks-completed', None)])],
      lanes=[['tWlc18uQd', 'tReg19vRe']]),
    S('Stage_Rej5rG', 'Application rejected', 'secondary',
      slas=[('sla_RejStg01', *E.STAGE_SLA[E.REJECTED], [('esc_rj01ar', 'at-risk', E.STAGE_AT_RISK_PERCENT, 'notification', [('UserGroup', '93a89c1e-be35-410f-ae37-cc5a0e1bd4c2', 'Procurement Operations')]), ('esc_rj02br', 'sla-breached', None, 'notification', [('UserGroup', 'afa0eb1e-0874-47bc-9ce6-8e4c5869de39', 'Procurement Operations Lead')])])],
      entry=[('Condition_rj01en', 'Buyer declined', True, None, None, None, [('selected-stage-exited', {'selectedStageIds': ['Stage_Byr7mC'], 'conditionExpression': '=js:vars.action2 === "reject"'})]), ('Condition_rj02en', 'Compliance rejected', True, None, None, None, [('selected-stage-exited', {'selectedStageIds': ['Stage_Cmp3nD'], 'conditionExpression': '=js:vars.action4 === "reject"'})]), ('Condition_rj03en', 'Bank verification failed', True, None, None, None, [('selected-stage-exited', {'selectedStageIds': ['Stage_Set8pE'], 'conditionExpression': '=js:vars.bankVerificationStatus !== "verified"'})])],
      exits=[('Condition_rj01ex', 'Rejection complete', None, 'exit-only', True, None, [('required-tasks-completed', None)])],
      lanes=[['tRjn20wSf', 'tAud21xTg']]),
    S('Stage_Wdr9sH', 'Application withdrawn', 'secondary',
      slas=[('sla_WdrStg01', *E.STAGE_SLA[E.WITHDRAWN], [('esc_wd01ar', 'at-risk', E.STAGE_AT_RISK_PERCENT, 'notification', [('UserGroup', '93a89c1e-be35-410f-ae37-cc5a0e1bd4c2', 'Procurement Operations')]), ('esc_wd02br', 'sla-breached', None, 'notification', [('UserGroup', 'afa0eb1e-0874-47bc-9ce6-8e4c5869de39', 'Procurement Operations Lead')])])],
      entry=[('Condition_wd01en', 'Supplier withdrew', True, None, None, None, [('user-selected-stage', None)])],
      exits=[('Condition_wd01ex', 'Withdrawal complete', None, 'exit-only', True, None, [('required-tasks-completed', None)])],
      lanes=[['tWdc22yUh', 'tWcl23zVj']]),
    S('Stage_Ovr4uK', 'Overall SLA review', 'secondary',
      slas=[],
      entry=[('Condition_ov01en', 'Overall target missed', False, None, None, None, [('sla-status-change', {'slaId': 'sla_RootCse1'})])],
      exits=[('Condition_ov01ex', 'Overall review complete', None, 'exit-only', True, None, [('required-tasks-completed', None)])],
      lanes=[['tOvr26cYn']]),
]

# --- Variables and bindings, generated from a real build -------------------------
# The three variable groups, built from the fixture's own Case Variables table rather
# than listed here. A second fixture with different variables then needs no edit, and the
# ids stay stable across runs because they are derived from the name.
def _vid(name: str) -> str:
    return "v" + hashlib.sha1(name.encode()).hexdigest()[:8]


_VARS = E.sdd_facts()["variables"]
INPUTS = [
    (_vid(n), n, vtype, default)
    for n, (category, vtype, default) in _VARS.items()
    if category == "In"
]
OUTPUTS = [
    (_vid(n), n, vtype, n)
    for n, (category, vtype, _d) in _VARS.items()
    if category == "Out"
]
INPUT_OUTPUTS = [(n, vtype) for n, (_c, vtype, _d) in _VARS.items()]

# id != name 的:[]

BINDINGS = [   # (id, name, resource, resourceSubType, resourceKey, default, propertyAttribute)
    ('bApv01aaa', 'name', 'app', None, 'Shared/uipath-maestro-case/Supplier Application Validation.Supplier Application Validation', 'Supplier Application Validation', 'name'),
    ('bApv02bbb', 'folderPath', 'app', None, 'Shared/uipath-maestro-case/Supplier Application Validation.Supplier Application Validation', 'Shared/uipath-maestro-case/Supplier Application Validation', 'folderPath'),
    ('bMsl01aaa', 'name', 'process', 'Api', 'Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierMasterScreeningLookup', 'SupplierMasterScreeningLookup', 'name'),
    ('bMsl02bbb', 'folderPath', 'process', 'Api', 'Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierMasterScreeningLookup', 'Shared/uipath-maestro-case/SupplierOnboardingKit', 'folderPath'),
    ('bOcm01aaa', 'name', 'process', 'Agent', 'Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierOfferingCategoryMatch', 'SupplierOfferingCategoryMatch', 'name'),
    ('bOcm02bbb', 'folderPath', 'process', 'Agent', 'Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierOfferingCategoryMatch', 'Shared/uipath-maestro-case/SupplierOnboardingKit', 'folderPath'),
    ('bSdu01aaa', 'name', 'app', None, 'Shared/uipath-maestro-case.supplier-document-upload', 'supplier-document-upload', 'name'),
    ('bSdu02bbb', 'folderPath', 'app', None, 'Shared/uipath-maestro-case.supplier-document-upload', 'Shared/uipath-maestro-case', 'folderPath'),
    ('bBsr01aaa', 'name', 'app', None, 'Shared/uipath-maestro-case.buyer-supplier-review-v2', 'buyer-supplier-review-v2', 'name'),
    ('bBsr02bbb', 'folderPath', 'app', None, 'Shared/uipath-maestro-case.buyer-supplier-review-v2', 'Shared/uipath-maestro-case', 'folderPath'),
    ('bSir01aaa', 'name', 'app', None, 'Shared/uipath-maestro-case/Supplier Information Request.Supplier Information Request', 'Supplier Information Request', 'name'),
    ('bSir02bbb', 'folderPath', 'app', None, 'Shared/uipath-maestro-case/Supplier Information Request.Supplier Information Request', 'Shared/uipath-maestro-case/Supplier Information Request', 'folderPath'),
    ('bSrc01aaa', 'name', 'app', None, 'Shared/uipath-maestro-case/Supplier Reference Check.Supplier Reference Check', 'Supplier Reference Check', 'name'),
    ('bSrc02bbb', 'folderPath', 'app', None, 'Shared/uipath-maestro-case/Supplier Reference Check.Supplier Reference Check', 'Shared/uipath-maestro-case/Supplier Reference Check', 'folderPath'),
    ('bCrc01aaa', 'name', 'process', 'Api', 'Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierComplianceRiskCheck', 'SupplierComplianceRiskCheck', 'name'),
    ('bCrc02bbb', 'folderPath', 'process', 'Api', 'Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierComplianceRiskCheck', 'Shared/uipath-maestro-case/SupplierOnboardingKit', 'folderPath'),
    ('bFhc01aaa', 'name', 'process', 'Agent', 'Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierFinancialHealthCheck', 'SupplierFinancialHealthCheck', 'name'),
    ('bFhc02bbb', 'folderPath', 'process', 'Agent', 'Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierFinancialHealthCheck', 'Shared/uipath-maestro-case/SupplierOnboardingKit', 'folderPath'),
    ('bSot01aaa', 'name', 'process', 'Api', 'Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierSignOffTierRules', 'SupplierSignOffTierRules', 'name'),
    ('bSot02bbb', 'folderPath', 'process', 'Api', 'Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierSignOffTierRules', 'Shared/uipath-maestro-case/SupplierOnboardingKit', 'folderPath'),
    ('bPds01aaa', 'name', 'app', None, 'Shared/uipath-maestro-case/Procurement Director Sign-off.Procurement Director Sign-off', 'Procurement Director Sign-off', 'name'),
    ('bPds02bbb', 'folderPath', 'app', None, 'Shared/uipath-maestro-case/Procurement Director Sign-off.Procurement Director Sign-off', 'Shared/uipath-maestro-case/Procurement Director Sign-off', 'folderPath'),
    ('bScr01aaa', 'name', 'app', None, 'Shared/uipath-maestro-case/Supplier Compliance Review.Supplier Compliance Review', 'Supplier Compliance Review', 'name'),
    ('bScr02bbb', 'folderPath', 'app', None, 'Shared/uipath-maestro-case/Supplier Compliance Review.Supplier Compliance Review', 'Shared/uipath-maestro-case/Supplier Compliance Review', 'folderPath'),
    ('bSlo01aaa', 'name', 'app', None, 'Shared/uipath-maestro-case/Supplier Legal Opinion.Supplier Legal Opinion', 'Supplier Legal Opinion', 'name'),
    ('bSlo02bbb', 'folderPath', 'app', None, 'Shared/uipath-maestro-case/Supplier Legal Opinion.Supplier Legal Opinion', 'Shared/uipath-maestro-case/Supplier Legal Opinion', 'folderPath'),
    ('bSer01aaa', 'name', 'process', 'Api', 'Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierErpRegistration', 'SupplierErpRegistration', 'name'),
    ('bSer02bbb', 'folderPath', 'process', 'Api', 'Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierErpRegistration', 'Shared/uipath-maestro-case/SupplierOnboardingKit', 'folderPath'),
    ('bScn01aaa', 'name', 'process', 'CaseManagement', 'Shared/uipath-maestro-case/SupplierNegotiationKit.SupplierContractNegotiation', 'SupplierContractNegotiation', 'name'),
    ('bScn02bbb', 'folderPath', 'process', 'CaseManagement', 'Shared/uipath-maestro-case/SupplierNegotiationKit.SupplierContractNegotiation', 'Shared/uipath-maestro-case/SupplierNegotiationKit', 'folderPath'),
    ('bSpa01aaa', 'name', 'app', None, 'Shared/uipath-maestro-case/Supplier Portal Access Confirmation.Supplier Portal Access Confirmation', 'Supplier Portal Access Confirmation', 'name'),
    ('bSpa02bbb', 'folderPath', 'app', None, 'Shared/uipath-maestro-case/Supplier Portal Access Confirmation.Supplier Portal Access Confirmation', 'Shared/uipath-maestro-case/Supplier Portal Access Confirmation', 'folderPath'),
    ('bSar01aaa', 'name', 'process', 'Api', 'Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierApprovedRegisterUpdate', 'SupplierApprovedRegisterUpdate', 'name'),
    ('bSar02bbb', 'folderPath', 'process', 'Api', 'Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierApprovedRegisterUpdate', 'Shared/uipath-maestro-case/SupplierOnboardingKit', 'folderPath'),
    ('bSra01aaa', 'name', 'process', 'Api', 'Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierRejectionAuditLog', 'SupplierRejectionAuditLog', 'name'),
    ('bSra02bbb', 'folderPath', 'process', 'Api', 'Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierRejectionAuditLog', 'Shared/uipath-maestro-case/SupplierOnboardingKit', 'folderPath'),
    ('bSwc01aaa', 'name', 'process', 'Api', 'Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierWithdrawalCleanup', 'SupplierWithdrawalCleanup', 'name'),
    ('bSwc02bbb', 'folderPath', 'process', 'Api', 'Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierWithdrawalCleanup', 'Shared/uipath-maestro-case/SupplierOnboardingKit', 'folderPath'),
    ('bSde01aaa', 'name', 'app', None, 'Shared/uipath-maestro-case.supplier-delay-escalation', 'supplier-delay-escalation', 'name'),
    ('bSde02bbb', 'folderPath', 'app', None, 'Shared/uipath-maestro-case.supplier-delay-escalation', 'Shared/uipath-maestro-case', 'folderPath'),
    ('bConn01aa', 'uipath-microsoft-outlook365 connection', 'Connection', None, 'dd657127-91f5-4568-a3a3-c024bc03fb0f', 'dd657127-91f5-4568-a3a3-c024bc03fb0f', 'ConnectionId'),
    ('bConn02bb', 'FolderKey', 'Connection', None, 'dd657127-91f5-4568-a3a3-c024bc03fb0f', 'def71452-bad1-40fa-be08-da175e89bd1a', 'folderKey'),
]


METADATA = {
    "caseIdentifier": "SUP",
    "caseIdentifierType": "constant",
    # Both read off a real build. The case app is what the people this case routes to
    # open, and direct passing is what carries a task's result into the next input.
    "caseAppEnabled": True,
    "caseDirectlyPassTaskOutputs": True,
    "slaRules": [
        _sla(
            (
                "sla_RootCse1",
                *E.CASE_SLA,
                [
                    ("esc_rt01ar", "at-risk", E.CASE_AT_RISK_PERCENT, "notification",
                     [("UserGroup", "93a89c1e-be35-410f-ae37-cc5a0e1bd4c2",
                       "Procurement Operations")]),
                    ("esc_rt02br", "sla-breached", None, "notification",
                     [("UserGroup", "065f7f2b-7592-4d50-b4be-2ac21e2f22f0",
                       "Procurement Leadership")]),
                ],
            )
        )
    ],
    "caseExitRules": [
        {"id": "Condition_ce01aa", "displayName": "Supplier onboarded",
         "marksCaseComplete": True,
         "rules": [[{"id": "Rule_ce01aa", "rule": "required-stages-completed"}]]},
        {"id": "Condition_ce02bb", "displayName": "Application rejected",
         "marksCaseComplete": False,
         "rules": [[{"id": "Rule_ce02bb", "rule": "selected-stage-completed",
                     "selectedStageIds": ["Stage_Rej5rG"]}]]},
        {"id": "Condition_ce03cc", "displayName": "Application withdrawn",
         "marksCaseComplete": False,
         "rules": [[{"id": "Rule_ce03cc", "rule": "selected-stage-completed",
                     "selectedStageIds": ["Stage_Wdr9sH"]}]]},
    ],
}


def build() -> dict:
    """Assemble the plan. Every call returns a fresh object, safe to mutate."""
    tasks = {t["id"]: t for t in TASKS}
    missing = [
        tid
        for stage in STAGES
        for lane in stage["data"]["tasks"]
        for tid in lane
        if tid not in tasks
    ]
    if missing:
        raise AssertionError(f"STAGES reference task ids not in TASKS: {missing}")
    placed = {tid for s in STAGES for lane in s["data"]["tasks"] for tid in lane}
    orphans = sorted(set(tasks) - placed)
    if orphans:
        raise AssertionError(f"TASKS not placed in any stage: {orphans}")

    import copy

    nodes = []
    for stage in copy.deepcopy(STAGES):
        stage["data"]["tasks"] = [
            [copy.deepcopy(tasks[tid]) for tid in lane]
            for lane in stage["data"]["tasks"]
        ]
        nodes.append(stage)

    return {
        "id": CASE_ID,
        "version": CASE_VERSION,
        "name": CASE_NAME,
        "metadata": copy.deepcopy(METADATA),
        "variables": {
            "inputs": [
                {"id": vid, "name": name, "type": vtype, "default": default}
                for vid, name, vtype, default in INPUTS
            ],
            "outputs": [
                {"id": vid, "name": name, "type": vtype, "var": var}
                for vid, name, vtype, var in OUTPUTS
            ],
            "inputOutputs": [
                _companion(name, vtype)
                for name, vtype in INPUT_OUTPUTS
            ],
        },
        "bindings": [
            {
                "id": bid,
                "name": name,
                "type": "string",
                "resource": resource,
                **({"resourceSubType": subtype} if subtype else {}),
                "resourceKey": key,
                **({"default": default} if default is not None else {}),
                **({"propertyAttribute": attr} if attr else {}),
            }
            for bid, name, resource, subtype, key, default, attr in BINDINGS
        ],
        "nodes": nodes,
        "edges": [],
        "layout": {},
    }




# A companion's own fields come from its SDD Category, the way a real build writes
# them: case state is marked `custom` and carries its Default, an Out companion
# carries a default and no mark, and an In companion carries neither.
_TRIGGER_ID = "trigger_r2lbym"


def _companion(name: str, vtype: str) -> dict:
    category, _sdd_type, default = E.sdd_facts()["variables"].get(
        name, ("Variable", vtype, "")
    )
    if category == "In":
        return {"id": name, "name": name, "type": vtype, "elementId": _TRIGGER_ID}
    entry = {"id": name, "name": name, "type": vtype}
    if category == "Variable":
        entry["custom"] = True
    entry["elementId"] = "root"
    if category == "Out":
        entry["default"] = default
    elif default:
        entry["default"] = default
    return entry


def baseline_plan() -> dict:
    """A plan all five graders accept. Fresh object per call, safe to mutate."""
    return build()


def run_checker(name: str, plan: dict) -> subprocess.CompletedProcess:
    """Run one grader against `plan` in a scratch directory."""
    with tempfile.TemporaryDirectory() as tmp:
        nested = Path(tmp) / "Case" / "Case"
        nested.mkdir(parents=True)
        with open(nested / "caseplan.json", "w", encoding="utf-8") as stream:
            json.dump(plan, stream)
        return subprocess.run(
            [sys.executable, str(CHECKERS[name])],
            cwd=tmp,
            capture_output=True,
            text=True,
        )


def stage(plan: dict, label: str) -> dict:
    return next(
        node
        for node in plan["nodes"]
        if (node.get("data") or {}).get("label") == label
    )


def tasks_of(node: dict) -> list[dict]:
    out = []
    for row in (node.get("data") or {}).get("tasks") or []:
        out.extend(row if isinstance(row, list) else [row])
    return out


def guard_of(cond: dict) -> str:
    """Read a condition's guard the way the graders do: condition first, then rules.

    The two placements mean the same thing at runtime, and this plan puts the stage-exit
    guards on the rules. A test that only wrote `conditionExpression` would mutate
    nothing and pass while the assertion under test stayed dead.
    """
    direct = cond.get("conditionExpression")
    if direct:
        return str(direct)
    for group in cond.get("rules") or []:
        for rule in group if isinstance(group, list) else [group]:
            expr = rule.get("conditionExpression")
            if expr:
                return str(expr)
    return ""


def set_guard(cond: dict, expression: str) -> None:
    cond["conditionExpression"] = expression
    for group in cond.get("rules") or []:
        for rule in group if isinstance(group, list) else [group]:
            if "conditionExpression" in rule:
                rule["conditionExpression"] = expression


def task(plan: dict, name: str) -> dict:
    for node in plan["nodes"]:
        for item in tasks_of(node):
            if (item.get("data") or {}).get("displayName") == name or item.get(
                "displayName"
            ) == name:
                return item
    raise AssertionError(f"task {name!r} not in the baseline plan")


def _iter_dicts(node, path="$"):
    """Every dict in a plan, with a path, for tests that need to find one by content."""
    if isinstance(node, dict):
        yield path, node
        for key, value in node.items():
            yield from _iter_dicts(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _iter_dicts(value, f"{path}[{index}]")


class CheckerBase(unittest.TestCase):
    checker = ""

    def accepts(self, plan: dict):
        result = run_checker(self.checker, plan)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def rejects(self, plan: dict, needle: str):
        result = run_checker(self.checker, plan)
        blob = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, f"mutation was accepted:\n{blob}")
        self.assertIn(needle, blob, f"caught, but not by the assertion under test:\n{blob}")
        return result


class TopologyTests(CheckerBase):
    checker = "topology"

    def test_rejects_a_stage_the_sdd_does_not_declare(self):
        plan = baseline_plan()
        plan["nodes"].append({
            "id": "Stage_Extra1", "type": "case-management:Stage",
            "data": {"label": "Invented phase", "tasks": [],
                     "entryConditions": [], "exitConditions": []},
        })
        self.rejects(plan, "unexpected stage(s)")

    def test_rejects_a_primary_stage_turned_secondary(self):
        """A primary stage is what case completion waits on."""
        plan = baseline_plan()
        stage_node(plan, E.CHECKING)["data"]["stageType"] = "secondary"
        self.rejects(plan, "the SDD makes it primary")

    def test_rejects_an_oversight_lane_with_no_entry_condition(self):
        plan = baseline_plan()
        stage_node(plan, E.SLA_REVIEW)["data"]["entryConditions"] = []
        self.rejects(plan, "has no entry condition")

    def test_rejects_a_secondary_stage_whose_entry_does_not_interrupt(self):
        """Rejection and withdrawal take the application over, so they must interrupt."""
        plan = baseline_plan()
        label = sorted(E.INTERRUPTING_SECONDARY)[0]
        for cond in stage_node(plan, label)["data"]["entryConditions"]:
            cond["isInterrupting"] = False
        self.rejects(plan, "has no interrupting entry")

    def test_rejects_a_rejection_lane_reachable_from_too_few_phases(self):
        """Three phases produce one rejection; dropping an origin strands one of them."""
        plan = baseline_plan()
        node = stage_node(plan, E.REJECTED)
        node["data"]["entryConditions"] = node["data"]["entryConditions"][:1]
        self.rejects(plan, "entry origins are")

    def test_rejects_a_plan_with_no_corrections_loop(self):
        """Send-back has to return the application to the checks."""
        plan = baseline_plan()
        buyer_id = stage_node(plan, E.BUYER)["id"]
        node = stage_node(plan, E.CHECKING)
        node["data"]["entryConditions"] = [
            c for c in node["data"]["entryConditions"]
            if buyer_id not in json.dumps(c)
        ]
        self.rejects(plan, f"has no entry from {E.BUYER!r}")

    def test_rejects_an_unguarded_corrections_loop(self):
        """Without a guard on the loop entry, every buyer decision sends the application
        back to the checks, approvals included."""
        plan = baseline_plan()
        buyer_id = stage_node(plan, E.BUYER)["id"]
        stripped = 0
        for cond in stage_node(plan, E.CHECKING)["data"]["entryConditions"]:
            if buyer_id not in json.dumps(cond):
                continue
            for _path, rule in _iter_dicts(cond):
                if isinstance(rule.get("conditionExpression"), str):
                    rule.pop("conditionExpression")
                    stripped += 1
        self.assertTrue(stripped, "the baseline corrections loop carries no guard")
        self.rejects(plan, "corrections-loop entry carries no guard")

    def test_rejects_a_first_phase_with_no_case_entered_rule(self):
        plan = baseline_plan()
        for _path, node in _iter_dicts(stage_node(plan, E.CHECKING)["data"]["entryConditions"]):
            if node.get("rule") == "case-entered":
                node["rule"] = "selected-stage-completed"
        self.rejects(plan, "has no `case-entered` entry")

    def test_rejects_a_withdrawal_lane_not_reached_from_the_stage_picker(self):
        """Nothing in the source signals a withdrawal, so a person has to pick it."""
        plan = baseline_plan()
        for _path, node in _iter_dicts(stage_node(plan, E.WITHDRAWN)["data"]["entryConditions"]):
            if node.get("rule") == "user-selected-stage":
                node["rule"] = "case-entered"
        self.rejects(plan, "is not entered by `user-selected-stage`")

    def test_rejects_a_plan_missing_a_case_exit(self):
        plan = baseline_plan()
        plan["metadata"]["caseExitRules"] = plan["metadata"]["caseExitRules"][:-1]
        self.rejects(plan, "case exit condition(s); the SDD declares")

    def test_rejects_two_case_exits_marking_the_case_complete(self):
        """Rejection and withdrawal close the case without completing it."""
        plan = baseline_plan()
        for rule in plan["metadata"]["caseExitRules"]:
            rule["marksCaseComplete"] = True
        self.rejects(plan, "mark the case complete; exactly one should")

    def test_rejects_a_completing_exit_keyed_on_a_single_stage(self):
        """Completion waits on every required stage, not on one of them."""
        plan = baseline_plan()
        for rule in plan["metadata"]["caseExitRules"]:
            if not rule.get("marksCaseComplete"):
                continue
            for group in rule.get("rules") or []:
                for inner in group:
                    inner["rule"] = "selected-stage-completed"
                    inner["selectedStageIds"] = [stage_node(plan, E.ONBOARDED)["id"]]
        self.rejects(plan, "the completing case exit is keyed on")

    def test_rejects_a_stage_entered_from_a_terminal_stage(self):
        """A closed application must not move anywhere."""
        plan = baseline_plan()
        terminal = sorted(E.TERMINAL_STAGES)[0]
        stage_node(plan, E.BUYER)["data"]["entryConditions"].append({
            "id": "Condition_fromTerminal", "displayName": "Reopened",
            "rules": [[{"id": "Condition_fromTerminal_r0",
                        "rule": "selected-stage-completed",
                        "selectedStageIds": [stage_node(plan, terminal)["id"]]}]],
            "isInterrupting": False,
        })
        self.rejects(plan, "are entered from the terminal stage")

    def test_rejects_a_terminal_stage_whose_exit_is_not_exit_only(self):
        plan = baseline_plan()
        terminal = sorted(E.TERMINAL_STAGES)[0]
        node = stage_node(plan, terminal)
        node["data"].setdefault("exitConditions", []).append({
            "id": "Condition_leak", "displayName": "Leaks onward",
            "rules": [[{"id": "Condition_leak_r0", "rule": "selected-tasks-completed",
                        "selectedTasksIds": []}]],
            "type": "diverting", "marksStageComplete": False,
        })
        self.rejects(plan, "is not `exit-only`")

    def test_accepts_baseline(self):
        self.accepts(baseline_plan())

    def test_rejects_missing_stage(self):
        plan = baseline_plan()
        plan["nodes"] = [
            n for n in plan["nodes"] if (n.get("data") or {}).get("label") != E.WITHDRAWN
        ]
        self.rejects(plan, "missing stage")

    def test_rejects_secondary_lane_promoted_to_primary(self):
        plan = baseline_plan()
        stage(plan, E.REJECTED)["data"].pop("stageType", None)
        self.rejects(plan, "the SDD makes it secondary")

    def test_rejects_interrupting_oversight_lane(self):
        plan = baseline_plan()
        for cond in stage(plan, E.SLA_REVIEW)["data"]["entryConditions"]:
            cond["isInterrupting"] = True
        self.rejects(plan, "entry is interrupting")

    def test_rejects_unguarded_rejection_entry(self):
        plan = baseline_plan()
        conds = stage(plan, E.REJECTED)["data"]["entryConditions"]
        conds[0].pop("conditionExpression", None)
        for group in conds[0].get("rules") or []:
            for rule in group if isinstance(group, list) else [group]:
                rule.pop("conditionExpression", None)
        self.rejects(plan, "carries no guard")

    def test_rejects_dropped_corrections_loop(self):
        plan = baseline_plan()
        node = stage(plan, E.CHECKING)
        buyer_id = stage(plan, E.BUYER)["id"]
        node["data"]["entryConditions"] = [
            c
            for c in node["data"]["entryConditions"]
            if buyer_id not in json.dumps(c)
        ]
        self.rejects(plan, "send-back for corrections")

    def test_rejects_withdrawal_offered_during_setup(self):
        plan = baseline_plan()
        for cond in stage(plan, E.SETUP)["data"]["exitConditions"]:
            if cond.get("marksStageComplete"):
                cond["type"] = "wait-for-user"
        self.rejects(plan, "withdrawal picker")

    def test_rejects_withdrawal_missing_from_a_review_phase(self):
        plan = baseline_plan()
        for cond in stage(plan, E.BUYER)["data"]["exitConditions"]:
            if cond.get("type") == "wait-for-user":
                cond["type"] = "exit-only"
        self.rejects(plan, "withdrawal picker")

    def test_rejects_withdrawal_marked_case_complete(self):
        plan = baseline_plan()
        wid = stage(plan, E.WITHDRAWN)["id"]
        touched = False
        for cond in (plan.get("metadata") or {}).get("caseExitRules") or []:
            if wid in json.dumps(cond):
                cond["marksCaseComplete"] = True
                touched = True
        self.assertTrue(touched, "the mutation found no case exit fed by the withdrawal lane")
        self.rejects(plan, "marks the case complete")


    def test_rejects_a_surviving_xref_marker(self):
        # A build-time placeholder the resolver missed. The runtime reads it as a function call
        # and the case faults on its first rules evaluation, while validate reports Valid.
        plan = baseline_plan()
        for node in plan["nodes"]:
            if node.get("type") != "case-management:Stage":
                continue
            for cond in (node["data"].get("exitConditions") or []):
                for group in cond.get("rules") or []:
                    for rule in group:
                        if rule.get("conditionExpression"):
                            rule["conditionExpression"] = (
                                "=js:vars.$xref('Buyer review','Record buyer review decision','Action')"
                                " === \"approve\"")
                            self.rejects(plan, "unresolved $xref marker")
                            return
        self.fail("no guarded exit condition to mutate")

    def test_rejects_a_plan_built_to_the_superseded_schema(self):
        # The version is checked before the selector spelling, because the spelling follows
        # from it. Eight of the 28 runs measured are v27 builds, and each collected seven
        # selector findings for what is one wrong number.
        plan = baseline_plan()
        plan["version"] = "27.0.0"
        self.rejects(plan, "declares schema version")

    def test_a_superseded_schema_does_not_also_report_its_selectors(self):
        plan = baseline_plan()
        plan["version"] = "27.0.0"
        for cond in plan["metadata"]["caseExitRules"]:
            for group in cond["rules"]:
                for rule in group:
                    if "selectedStageIds" in rule:
                        ids = rule.pop("selectedStageIds")
                        rule["selectedStageId"] = ids[0] if ids else ""
        blob = self.rejects(plan, "declares schema version").stdout
        self.assertNotIn("stage selector(s) use", blob,
                         f"a v27 plan spells the selector singular correctly:\n{blob}")

    def test_rejects_a_plural_stage_selector(self):
        # validate accepts the plural array; the case then faults on CaseRulesEvaluatorNode
        # before any task opens, so no other assertion here ever gets to run.
        plan = baseline_plan()
        for cond in plan["metadata"]["caseExitRules"]:
            for group in cond["rules"]:
                for rule in group:
                    if "selectedStageIds" in rule:
                        ids = rule.pop("selectedStageIds")
                        rule["selectedStageId"] = ids[0] if ids else ""
        self.rejects(plan, "selectedStageId")

class GuardTests(CheckerBase):
    checker = "guards"

    def test_rejects_a_guarded_equal_name_extract_whose_id_was_suffixed(self):
        """An extract is readable by its id, so suffixing the id hides it from the guard.

        34670963139 and 34694676530 did this to two names each and lost three routes apiece
        to a gate that never opened. 34686998522 suffixed the same two names and routed
        correctly, because its guards read the suffixed spelling.
        """
        plan = baseline_plan()
        guarded = set()
        for _path, node in _iter_dicts(plan):
            expr = node.get("conditionExpression")
            if isinstance(expr, str):
                guarded.update(re.findall(r"vars\.([A-Za-z_]\w*)", expr))
        for _path, node in _iter_dicts(plan):
            name = node.get("name")
            if (name and name in guarded and node.get("var") == name
                    and node.get("id") == name):
                node["id"] = name + "1"
                node["originalVar"] = name + "1"
                node["target"] = "=" + name + "1"
                self.rejects(plan, "An extract is readable by its id")
                return
        self.fail("the baseline has no guarded equal-name extract to suffix")

    def test_accepts_a_guard_reading_the_suffixed_spelling(self):
        """The suffix alone is not the defect. 34686998522 carries it on
        `directorSignOffRequired` and `bankVerificationStatus` and completed six routes,
        because every guard reading them reads the suffixed name."""
        plan = baseline_plan()
        guarded = set()
        for _path, node in _iter_dicts(plan):
            expr = node.get("conditionExpression")
            if isinstance(expr, str):
                guarded.update(re.findall(r"vars\.([A-Za-z_]\w*)", expr))
        renamed = None
        for _path, node in _iter_dicts(plan):
            name = node.get("name")
            if (name and name in guarded and node.get("var") == name
                    and node.get("id") == name):
                renamed = name
                node["id"] = name + "1"
                node["originalVar"] = name + "1"
                node["target"] = "=" + name + "1"
                break
        self.assertIsNotNone(renamed, "the baseline has no guarded equal-name extract")
        for _path, node in _iter_dicts(plan):
            expr = node.get("conditionExpression")
            if isinstance(expr, str) and f"vars.{renamed}" in expr:
                node["conditionExpression"] = expr.replace(
                    f"vars.{renamed}", f"vars.{renamed}1")
        self.accepts(plan)

    def test_accepts_a_reassign_whose_id_names_the_source_field(self):
        """`Action -> buyerDecision` is not an equal-name row: its id names the field the
        value came from, and every run that routes correctly carries it that way."""
        self.accepts(baseline_plan())


    def test_accepts_single_quoted_guard_literals(self):
        """Run 34613299132 wrote every guard with single quotes and carried all seven
        routes to completion. A double-quote-only reader saw 19 guards and no literals."""
        plan = baseline_plan()
        swapped = 0

        def swap(node):
            nonlocal swapped
            if isinstance(node, dict):
                expr = node.get("conditionExpression")
                if isinstance(expr, str) and '"' in expr:
                    node["conditionExpression"] = expr.replace('"', "'")
                    swapped += 1
                for value in node.values():
                    swap(value)
            elif isinstance(node, list):
                for value in node:
                    swap(value)

        swap(plan)
        self.assertGreater(swapped, 0, "the baseline has no double-quoted guard to swap")
        self.accepts(plan)

    def test_accepts_baseline(self):
        self.accepts(baseline_plan())

    def test_rejects_an_unparseable_js_expression(self):
        # One missing close paren, 300 characters from its partner. `uip maestro case validate`
        # reports Valid; the case throws on the expression's first evaluation.
        plan = baseline_plan()
        plan["nodes"].append({
            "id": "tzbanXpNg",
            "name": "Confirm offering category match",
            "inputs": {
                "documents": '=js:([["Bank details", vars.bankDetailsDocument]]'
                             '.map(function (p) { return p[0]; }).join("; ")',
            },
        })
        self.rejects(plan, "does not parse")

    def test_rejects_business_label_instead_of_form_enum(self):
        plan = baseline_plan()
        blob = json.dumps(plan).replace('=== \\"sendback\\"', '=== \\"SendBack\\"')
        self.rejects(json.loads(blob), "which none of the deployed forms can emit")

    def test_rejects_dropped_signoff_threshold(self):
        plan = baseline_plan()
        for node in plan["nodes"]:
            for item in tasks_of(node):
                if "500000" in str(item.get("skipCondition") or ""):
                    item.pop("skipCondition")
        self.rejects(plan, "appears in no guard")

    def test_rejects_overlapping_buyer_exits(self):
        plan = baseline_plan()
        conds = stage(plan, E.BUYER)["data"]["exitConditions"]
        completing = next(c for c in conds if c.get("marksStageComplete"))
        diverting = next(c for c in conds if not c.get("marksStageComplete"))
        set_guard(diverting, guard_of(completing))
        self.rejects(plan, "would fire into two destinations")

    def test_rejects_guard_over_unknown_variable(self):
        plan = baseline_plan()
        cond = stage(plan, E.COMPLIANCE)["data"]["entryConditions"][0]
        cond["conditionExpression"] = '=js:vars.notAThing === "approve"'
        self.rejects(plan, "never routes")


    def test_rejects_a_plan_with_no_guarded_condition_at_all(self):
        """Every routing decision in this case is guarded, so none is a dropped build."""
        plan = baseline_plan()
        for _path, node in _iter_dicts(plan):
            for key in ("conditionExpression", "skipCondition"):
                if isinstance(node.get(key), str):
                    node.pop(key)
        self.rejects(plan, "carries no guarded conditions at all")

    def test_rejects_a_plan_that_routes_on_no_buyer_outcome(self):
        """`approve`, `reject` and `sendback` each have their own destination."""
        plan = baseline_plan()
        for _path, node in _iter_dicts(plan):
            expr = node.get("conditionExpression")
            if isinstance(expr, str) and "sendback" in expr:
                node["conditionExpression"] = expr.replace("sendback", "approve")
        self.rejects(plan, "routes on the buyer outcome")

    def test_rejects_a_plan_where_nothing_compares_against_verified(self):
        """Bank verification is what decides whether setup can continue."""
        plan = baseline_plan()
        for _path, node in _iter_dicts(plan):
            expr = node.get("conditionExpression")
            if isinstance(expr, str) and "verified" in expr:
                node["conditionExpression"] = expr.replace("verified", "confirmed")
        self.rejects(plan, "no guard compares against")

    def test_rejects_a_buyer_stage_whose_completing_exit_carries_no_guard(self):
        """Approval must be the only route that completes the buyer phase."""
        plan = baseline_plan()
        stripped = 0
        for _path, node in _iter_dicts(stage_node(plan, E.BUYER)):
            if node.get("marksStageComplete") is True:
                for _p2, rule in _iter_dicts(node):
                    if isinstance(rule.get("conditionExpression"), str):
                        rule.pop("conditionExpression")
                        stripped += 1
        self.assertTrue(stripped, "the baseline buyer stage has no guarded completing exit")
        self.rejects(plan, "has no completing exit carrying a guard")

    def test_rejects_a_buyer_completing_exit_that_routes_on_more_than_approve(self):
        """Only `approve` completes the phase; anything else forks the decision."""
        plan = baseline_plan()
        changed = 0
        for _path, node in _iter_dicts(stage_node(plan, E.BUYER)):
            if node.get("marksStageComplete") is not True:
                continue
            for _p2, rule in _iter_dicts(node):
                expr = rule.get("conditionExpression")
                if isinstance(expr, str) and '"approve"' in expr:
                    rule["conditionExpression"] = expr.replace(
                        '=== "approve"', '=== "approve" || vars.buyerDecision === "reject"')
                    changed += 1
        self.assertTrue(changed, "the baseline buyer stage has no approving completing exit")
        self.rejects(plan, "completing exit routes on")

    def test_rejects_an_unguarded_compliance_exit(self):
        """Compliance advances only on a decision, so no exit may be unguarded."""
        plan = baseline_plan()
        stripped = 0
        for _path, node in _iter_dicts(stage_node(plan, E.COMPLIANCE)):
            if "marksStageComplete" not in node:
                continue
            for _p2, rule in _iter_dicts(node):
                if isinstance(rule.get("conditionExpression"), str):
                    rule.pop("conditionExpression")
                    stripped += 1
        self.assertTrue(stripped, "the baseline compliance stage has no guarded exit")
        self.rejects(plan, "has unguarded exit(s)")


def stage_node(plan: dict, label: str) -> dict:
    """The stage node the SDD calls `label`, for a test that mutates one stage."""
    for node in plan.get("nodes", []):
        if (node.get("data") or {}).get("label") == label:
            return node
    raise AssertionError(f"the baseline has no stage labelled {label!r}")


class SlaTests(CheckerBase):
    checker = "sla"

    def test_rejects_a_plan_whose_root_carries_no_sla(self):
        """The overall target is dropped, and with it every overall-target response."""
        plan = baseline_plan()
        plan["metadata"]["slaRules"] = []
        self.rejects(plan, "carries no slaRules")

    def test_rejects_a_phase_sla_of_the_wrong_length(self):
        plan = baseline_plan()
        phase = sorted(E.STAGE_SLA)[0]
        for rule in stage_node(plan, phase)["data"].get("slaRules") or []:
            rule["count"] = 999
        self.rejects(plan, "SLA is")

    def test_rejects_an_sla_on_a_stage_the_sdd_gives_none(self):
        """A wrap-up lane is the response to a breach, not a thing that can breach."""
        plan = baseline_plan()
        label = sorted(E.NO_SLA_STAGES)[0]
        donor = sorted(E.STAGE_SLA)[0]
        rules = stage_node(plan, donor)["data"].get("slaRules") or []
        self.assertTrue(rules, f"stage {donor!r} declares no SLA to copy")
        stage_node(plan, label)["data"]["slaRules"] = copy.deepcopy(rules)
        self.rejects(plan, "declares an SLA; the SDD gives it none")

    def test_rejects_an_escalation_living_outside_its_own_phase(self):
        """The SDD owns each phase's escalation in the phase that can breach."""
        plan = baseline_plan()
        name, (home, _title) = sorted(E.START_TASK_ON_BREACH.items())[0]
        other = sorted(set(E.STAGE_SLA) - {home})[0]
        moved = None
        for lane in stage_node(plan, home)["data"]["tasks"]:
            for item in list(lane):
                if item.get("displayName") == name:
                    moved = item
                    lane.remove(item)
        self.assertIsNotNone(moved, f"stage {home!r} does not hold {name!r}")
        stage_node(plan, other)["data"]["tasks"][0].append(moved)
        self.rejects(plan, "is not inside")

    def test_rejects_an_sla_rule_that_names_no_sla(self):
        """Without a `slaId` it does not say which deadline it listens to."""
        plan = baseline_plan()
        name = sorted(E.START_TASK_ON_BREACH)[0]
        for _path, node in _iter_dicts(task(plan, name)):
            if node.get("slaId"):
                node.pop("slaId")
        self.rejects(plan, "with no `slaId`")

    def test_rejects_an_oversight_lane_keyed_on_two_sla_rules(self):
        """The SDD keys the lane on exactly one, against the root SLA."""
        plan = baseline_plan()
        conds = stage_node(plan, E.SLA_REVIEW)["data"]["entryConditions"]
        self.assertTrue(conds, "the oversight lane has no entry condition")
        conds.append(copy.deepcopy(conds[0]))
        self.rejects(plan, "`sla-status-change` entry rule(s)")

    def test_rejects_a_wrap_up_breach_that_acts_rather_than_notifies(self):
        """A delay apology promising a new expected date is wrong for an application
        that is already closed."""
        plan = baseline_plan()
        label = sorted(E.NOTIFY_ONLY_BREACH_STAGES)[0]
        touched = 0
        for _path, node in _iter_dicts(stage_node(plan, label)):
            action = node.get("action")
            if isinstance(action, dict) and action.get("type"):
                action["type"] = "start-task"
                touched += 1
        self.assertTrue(touched, f"stage {label!r} carries no breach escalation action")
        self.rejects(plan, "breach escalation acts by")

    def test_rejects_an_escalation_writing_its_date_nowhere(self):
        plan = baseline_plan()
        phase, escalation, slot = self._phase()
        item = task(plan, escalation)
        item["data"]["outputs"] = [
            o for o in (item["data"].get("outputs") or []) if o.get("var") != slot
        ]
        self.rejects(plan, "writes its new")

    def _phase(self):
        """One phase with an SLA, its escalation task and its revised-date slot."""
        phase = sorted(E.PHASE_REVISED_DATE)[0]
        return phase, E.ESCALATION_OF_PHASE[phase], E.PHASE_REVISED_DATE[phase]

    def test_rejects_a_root_sla_of_the_wrong_length(self):
        plan = baseline_plan()
        for rule in plan["metadata"]["slaRules"]:
            rule["count"] = 999
        self.rejects(plan, "no root SLA of")

    def test_rejects_a_case_sla_with_no_at_risk_escalation(self):
        """Without it the overall target passes with no warning before the breach."""
        plan = baseline_plan()
        for rule in plan["metadata"]["slaRules"]:
            # The trigger lives in `triggerInfo.type`, beside the percentage it fires at.
            rule["escalationRule"] = [
                e for e in (rule.get("escalationRule") or [])
                if (e.get("triggerInfo") or {}).get("type") != "at-risk"
            ]
        self.rejects(plan, "no at-risk escalation")

    def test_rejects_a_stage_at_risk_band_at_the_case_percentage(self):
        """70% for a phase and 75% for the overall target are not interchangeable."""
        plan = baseline_plan()
        phase = sorted(E.STAGE_SLA)[0]
        changed = 0
        for _path, node in _iter_dicts(stage_node(plan, phase)):
            if node.get("atRiskPercentage") == E.STAGE_AT_RISK_PERCENT:
                node["atRiskPercentage"] = E.CASE_AT_RISK_PERCENT
                changed += 1
        self.assertTrue(changed, "the baseline phase carries no at-risk band")
        self.rejects(plan, "at-risk band is")

    def test_rejects_an_escalation_with_no_sla_status_change_rule(self):
        """It never activates when the phase misses its deadline."""
        plan = baseline_plan()
        name = sorted(E.START_TASK_ON_BREACH)[0]
        task(plan, name)["entryConditions"] = []
        self.rejects(plan, "has no `sla-status-change` entry rule")

    def test_rejects_an_escalation_listening_to_another_phases_sla(self):
        """A phase's escalation must fire on its own breach, or the note names a phase
        that did not run late."""
        plan = baseline_plan()
        name, (own_phase, _title) = sorted(E.START_TASK_ON_BREACH.items())[0]
        other = sorted(set(E.STAGE_SLA) - {own_phase})[0]
        foreign = None
        for _path, node in _iter_dicts(stage_node(plan, other)):
            if node.get("id") and "sla" in str(node.get("id")).lower():
                foreign = node["id"]
                break
        self.assertIsNotNone(foreign, f"stage {other!r} declares no SLA id")
        for _path, node in _iter_dicts(task(plan, name)):
            if node.get("slaId"):
                node["slaId"] = foreign
        self.rejects(plan, "listens to SLA(s)")

    def test_rejects_an_oversight_lane_that_interrupts(self):
        """The review runs alongside the application, which must still reach its own
        disposition."""
        plan = baseline_plan()
        for cond in stage_node(plan, E.SLA_REVIEW)["data"]["entryConditions"]:
            cond["isInterrupting"] = True
        self.rejects(plan, "entry interrupts")

    def test_rejects_a_wrap_up_phase_holding_a_phase_escalation(self):
        plan = baseline_plan()
        label = sorted(E.NOTIFY_ONLY_BREACH_STAGES)[0]
        name = sorted(E.START_TASK_ON_BREACH)[0]
        stage_node(plan, label)["data"].setdefault("tasks", [[]])[0].append(
            {"id": "tEscDup01", "displayName": name, "type": "action", "data": {}})
        self.rejects(plan, "appears in wrap-up stage")

    def test_rejects_a_buyer_at_risk_warning_that_skips_category_management(self):
        """The SDD bumps a stalled review up before the deadline passes."""
        plan = baseline_plan()
        for _path, node in _iter_dicts(stage_node(plan, E.BUYER)):
            for key in ("value", "target"):
                if E.BUYER_AT_RISK_GROUP.lower() in str(node.get(key, "")).lower():
                    node[key] = "Somebody Else"
        self.rejects(plan, "at-risk notifies")

    def test_rejects_a_missing_revised_date_slot(self):
        """The delay note has nowhere to read the new expected date from."""
        plan = baseline_plan()
        _phase, _escalation, slot = self._phase()
        for group in ("inputs", "outputs", "inputOutputs"):
            plan["variables"][group] = [
                v for v in plan["variables"][group]
                if v.get("id") != slot and v.get("name") != slot
            ]
        self.rejects(plan, "has no revised-date slot named")

    def test_rejects_an_escalation_writing_to_another_phases_slot(self):
        plan = baseline_plan()
        phase, escalation, slot = self._phase()
        other = sorted(set(E.PHASE_REVISED_DATE.values()) - {slot})[0]
        for o in task(plan, escalation)["data"].get("outputs") or []:
            if o.get("var") == slot:
                o["var"] = other
        self.rejects(plan, "escalation writes into another phase's slot(s)")

    def test_rejects_a_phase_with_no_delay_note_task(self):
        plan = baseline_plan()
        phase, _escalation, _slot = self._phase()
        name = E.DELAY_NOTE_OF_PHASE[phase]
        for node in plan["nodes"]:
            for lane in (node.get("data") or {}).get("tasks") or []:
                for item in list(lane):
                    if item.get("displayName") == name:
                        lane.remove(item)
        self.rejects(plan, "has no delay note task")

    def test_accepts_baseline(self):
        self.accepts(baseline_plan())

    def test_rejects_stage_at_risk_band_on_the_case(self):
        plan = baseline_plan()
        for rule in (plan.get("metadata") or {}).get("slaRules") or []:
            for esc in rule.get("escalationRule") or []:
                info = esc.get("triggerInfo") or {}
                if info.get("type") == "at-risk":
                    info["atRiskPercentage"] = E.STAGE_AT_RISK_PERCENT
        self.rejects(plan, "case at-risk band")

    def test_rejects_dropped_stage_sla(self):
        plan = baseline_plan()
        stage(plan, E.BUYER)["data"].pop("slaRules", None)
        self.rejects(plan, "carries no slaRules")

    def test_rejects_breach_moved_to_a_stage_entry_rule(self):
        plan = baseline_plan()
        node = stage(plan, E.CHECKING)
        escalation = task(plan, "Escalate delayed application check")
        moved = copy.deepcopy(escalation["entryConditions"])
        escalation["entryConditions"] = [
            {"displayName": "adhoc", "rules": [[{"rule": "adhoc"}]]}
        ]
        node["data"]["entryConditions"].extend(moved)
        self.rejects(plan, "re-enters the stage")

    def test_rejects_shared_revised_date_slot(self):
        plan = baseline_plan()
        blob = json.dumps(plan).replace(
            E.PHASE_REVISED_DATE[E.BUYER], E.PHASE_REVISED_DATE[E.CHECKING]
        )
        self.rejects(json.loads(blob), "belongs to another phase")

    def test_rejects_delay_note_reading_nothing(self):
        plan = baseline_plan()
        note = task(plan, E.DELAY_NOTE_OF_PHASE[E.CHECKING])
        blob = json.dumps(note).replace(
            "vars." + E.PHASE_REVISED_DATE[E.CHECKING], "vars.escalationNotes"
        )
        note.clear()
        note.update(json.loads(blob))
        self.rejects(plan, "the new expected date blank")

    def test_rejects_wrap_up_starting_remediation(self):
        plan = baseline_plan()
        node = stage(plan, E.REJECTED)
        escalation = copy.deepcopy(task(plan, "Escalate delayed application check"))
        node["data"]["tasks"].append([escalation])
        self.rejects(plan, "starts task(s)")


class TasksIoTests(CheckerBase):
    checker = "tasks_io"

    def _first_stage_task(self, plan):
        """The first task the SDD declares, with the stage it lives in."""
        label, rows = sorted(E.STAGE_TASKS.items())[0]
        return stage_node(plan, label), rows[0][0]

    def test_rejects_a_stage_missing_a_task_the_sdd_declares(self):
        plan = baseline_plan()
        node, name = self._first_stage_task(plan)
        for lane in node["data"]["tasks"]:
            for item in list(lane):
                if item.get("displayName") == name:
                    lane.remove(item)
        self.rejects(plan, f"is missing task {name!r}")

    def test_rejects_a_task_whose_required_flag_is_flipped(self):
        """A required escalation stops the stage completing unless the phase breached."""
        plan = baseline_plan()
        node, name = self._first_stage_task(plan)
        item = task(plan, name)
        item["isRequired"] = not bool(item.get("isRequired"))
        self.rejects(plan, "isRequired=")

    def test_rejects_a_task_whose_run_once_flag_is_flipped(self):
        """A re-entered stage runs a task that is not run-once a second time."""
        plan = baseline_plan()
        _node, name = self._first_stage_task(plan)
        item = task(plan, name)
        item["shouldRunOnlyOnce"] = not bool(item.get("shouldRunOnlyOnce"))
        self.rejects(plan, "shouldRunOnlyOnce=")

    def test_rejects_a_plan_with_the_wrong_task_count(self):
        plan = baseline_plan()
        node, _name = self._first_stage_task(plan)
        node["data"]["tasks"][0].append({
            "id": "tExtra001", "displayName": "An extra task",
            "type": "action", "data": {},
        })
        self.rejects(plan, f"tasks in the plan; the SDD declares {E.TOTAL_TASKS}")

    def test_rejects_a_plan_whose_task_type_mix_is_wrong(self):
        """A different class runs on a different runtime, so the mix is counted as well
        as checked task by task."""
        plan = baseline_plan()
        _node, name = self._first_stage_task(plan)
        item = task(plan, name)
        item["type"] = "api-workflow" if item.get("type") != "api-workflow" else "action"
        self.rejects(plan, "task-type counts are")

    def test_rejects_a_plan_that_binds_a_resource_the_sdd_does_not_name(self):
        """A task binds through `<folderPath>.<name>` on its binding, not on the task."""
        plan = baseline_plan()
        for _path, node in _iter_dicts(plan):
            if node.get("resourceKey"):
                node["resourceKey"] = "Shared/invented/Nothing.Nothing"
                break
        else:
            self.fail("the baseline carries no binding to repoint")
        self.rejects(plan, "binds resource(s) the SDD does not name")

    def test_rejects_a_skeleton_task(self):
        """Every resource in this SDD is deployed, so none should be left unresolved."""
        plan = baseline_plan()
        _node, name = self._first_stage_task(plan)
        task(plan, name)["data"] = {}
        self.rejects(plan, "task(s) are skeletons")

    def test_rejects_an_output_target_no_task_writes(self):
        plan = baseline_plan()
        target, writers = sorted(E.OUTPUT_TARGETS.items())[0]
        for writer in writers:
            item = task(plan, writer)
            item["data"]["outputs"] = [
                o for o in (item["data"].get("outputs") or [])
                if o.get("var") != target
            ]
        self.rejects(plan, f"nothing in the plan writes {target!r}")

    def test_rejects_an_output_target_the_plan_never_declares(self):
        """A route that reads an undeclared variable gets nothing."""
        plan = baseline_plan()
        target = sorted(E.OUTPUT_TARGETS)[0]
        for group in ("inputs", "outputs", "inputOutputs"):
            plan["variables"][group] = [
                v for v in plan["variables"][group]
                if v.get("id") != target and v.get("name") != target
            ]
        self.rejects(plan, f"variable {target!r} is not declared in the plan")

    def test_rejects_one_writer_dropping_a_shared_output_target(self):
        """Where the SDD gives two tasks the same reassign, one dropping it is the
        failure the whole-target check cannot see."""
        plan = baseline_plan()
        target, writers = next(
            ((k, v) for k, v in sorted(E.OUTPUT_TARGETS.items()) if len(v) > 1), (None, None))
        if target is None:
            self.skipTest("this SDD gives no target more than one writer")
        item = task(plan, writers[0])
        item["data"]["outputs"] = [
            o for o in (item["data"].get("outputs") or []) if o.get("var") != target
        ]
        self.rejects(plan, f"do not write {target!r}")

    def test_rejects_an_on_demand_task_with_no_adhoc_rule(self):
        """A manually launched task needs its own `adhoc` rule, or nothing can start it."""
        plan = baseline_plan()
        name = sorted(E.ADHOC_TASKS)[0]
        for _path, node in _iter_dicts(task(plan, name)):
            if node.get("rule") == "adhoc":
                node["rule"] = "case-entered"
        self.rejects(plan, "entry rules are")

    def test_rejects_an_expression_recipient_with_the_wrong_type(self):
        """An expression recipient is Type 3; another type sends it to nobody."""
        plan = baseline_plan()
        name = sorted(E.EXPRESSION_RECIPIENT_TASKS)[0]
        task(plan, name)["data"]["recipient"] = {
            "Type": 2, "Value": E.EXPRESSION_RECIPIENT_VALUE}
        self.rejects(plan, "recipient Type is")

    def test_rejects_an_expression_recipient_with_the_wrong_value(self):
        plan = baseline_plan()
        name = sorted(E.EXPRESSION_RECIPIENT_TASKS)[0]
        task(plan, name)["data"]["recipient"] = {
            "Type": E.EXPRESSION_RECIPIENT_TYPE, "Value": "someone@example.com"}
        self.rejects(plan, "recipient Value is")

    def test_rejects_a_missing_child_case_task(self):
        plan = baseline_plan()
        for node in plan["nodes"]:
            for lane in (node.get("data") or {}).get("tasks") or []:
                for item in list(lane):
                    if item.get("displayName") == E.CHILD_CASE_TASK:
                        lane.remove(item)
        self.rejects(plan, f"task {E.CHILD_CASE_TASK!r} is missing")

    def test_rejects_a_child_case_the_parent_waits_on(self):
        """The negotiation runs on its own; waiting holds the setup phase open."""
        plan = baseline_plan()
        task(plan, E.CHILD_CASE_TASK)["data"]["waitForCompletion"] = True
        self.rejects(plan, "waitForCompletion=")

    def test_rejects_a_task_carrying_only_part_of_its_design_rationale(self):
        """A fragment drops the reason the task is shaped the way it is."""
        plan = baseline_plan()
        # `description` sits on the task node, beside `displayName`, not inside `data`.
        cut = 0
        for _stage, rows in sorted(E.STAGE_TASKS.items()):
            for row in rows:
                item = task(plan, row[0])
                desc = item.get("description")
                if isinstance(desc, str) and len(desc) > 30:
                    item["description"] = desc[:20]
                    cut += 1
        self.assertTrue(cut, "the baseline carries no task description to truncate")
        self.rejects(plan, "is not their whole")

    def test_accepts_baseline(self):
        self.accepts(baseline_plan())

    def test_rejects_wrong_task_class(self):
        plan = baseline_plan()
        task(plan, "Confirm offering category match")["type"] = "api-workflow"
        self.rejects(plan, "runs on a different runtime")

    def test_rejects_extra_task(self):
        plan = baseline_plan()
        node = stage(plan, E.ONBOARDED)
        extra = copy.deepcopy(tasks_of(node)[0])
        extra["id"] = "extraTask01"
        extra["data"]["displayName"] = "Unexpected extra task"
        extra["displayName"] = "Unexpected extra task"
        node["data"]["tasks"].append([extra])
        self.rejects(plan, "extra task(s)")

    def test_rejects_dropped_run_once(self):
        plan = baseline_plan()
        task(plan, "Register supplier in ERP")["shouldRunOnlyOnce"] = False
        self.rejects(plan, "would run it twice")

    def test_rejects_recipient_as_bare_string(self):
        plan = baseline_plan()
        item = task(plan, "Record buyer review decision")
        item["data"]["recipient"] = E.EXPRESSION_RECIPIENT_VALUE
        self.rejects(plan, "must be the object")

    def test_rejects_dropped_recipient(self):
        plan = baseline_plan()
        task(plan, "Record buyer review decision")["data"].pop("recipient", None)
        self.rejects(plan, "reaches nobody")

    def test_rejects_a_role_recipient_emitted_as_a_single_user(self):
        # The shape that shipped 69 times: `Role:` written as Type 0 or 2, so the engine
        # picks SingleUser and one person holds the task instead of the role.
        plan = baseline_plan()
        task(plan, "Validate application details")["data"]["recipient"] = {
            "Type": 2, "Value": "someone@example.com"
        }
        self.rejects(plan, "is Type 2")

    def test_accepts_a_role_recipient_as_a_group(self):
        plan = baseline_plan()
        task(plan, "Validate application details")["data"]["recipient"] = {
            "Type": 1, "Value": "Procurement Operations Lead"
        }
        self.accepts(plan)

    def test_rejects_a_dropped_custom_output(self):
        # A run completed this gate by hand and BuyerDecision stayed None, while the
        # agent task in the same instance returned its outputs in full.
        plan = baseline_plan()
        item = task(plan, "Record buyer review decision")
        item["data"]["outputs"] = [
            o for o in item["data"]["outputs"]
            if (o.get("var") or o.get("name")) != "buyerDecision"
        ]
        self.rejects(plan, "emits no output for")

    def test_accepts_the_custom_output_when_present(self):
        self.accepts(baseline_plan())

    def test_rejects_a_placeholder_recipient(self):
        # The engine logged `ConfiguredAssignee=---` and `Recipient=---`, called the
        # assignment a success, and the task sat in nobody's queue for the whole run.
        plan = baseline_plan()
        task(plan, "Validate application details")["data"]["recipient"] = {
            "Type": 1, "Value": "---"
        }
        self.rejects(plan, "recipient is")

    def test_rejects_an_em_dash_recipient(self):
        plan = baseline_plan()
        task(plan, "Validate application details")["data"]["recipient"] = {
            "Type": 1, "Value": "\u2014"
        }
        self.rejects(plan, "assigns the task to nobody")

    def test_rejects_a_task_with_no_entry_rule(self):
        # A run that reached one stage, opened no task, raised no incident and timed out.
        # `validate` only warns on this, so nothing before the run reports it.
        plan = baseline_plan()
        task(plan, "Validate application details")["entryConditions"] = []
        self.rejects(plan, "carry no entry rule")

    def test_accepts_a_task_whose_entry_rule_is_present(self):
        self.accepts(baseline_plan())

    def test_accepts_an_empty_string_file_input(self):
        """Neither shape of an unused optional `file` reaches the request.

        The engine keeps a file entry only when its value parses as a file reference
        (`IntSvcSendTaskArgs.cs:187`), so `""` is filtered out exactly as an absent key
        is. Run 34049629743 shipped eight of them and delivered mail on four routes;
        34632354461 shipped eight and carried all seven. An assertion here fired on 9 of
        32 runs and docked three that worked.
        """
        plan = baseline_plan()
        item = task(plan, "Notify buyer of application")
        item["data"].setdefault("inputs", []).append(
            {"name": "file", "type": "string", "id": "vFile01", "var": "vFile01", "value": ""}
        )
        self.accepts(plan)

    def test_accepts_a_file_input_left_null(self):
        plan = baseline_plan()
        item = task(plan, "Notify buyer of application")
        item["data"].setdefault("inputs", []).append(
            {"name": "file", "type": "string", "id": "vFile01", "var": "vFile01", "value": None}
        )
        self.accepts(plan)

    def test_rejects_an_action_type_written_into_the_catalog_field(self):
        # The SDD names an action type inside an app. That is not a catalog, and a task
        # carrying it faults on first open with `No task catalog exists with name ...`.
        # validate never resolves the name against the tenant.
        plan = baseline_plan()
        task(plan, "Escalate delayed buyer review")["data"]["actionCatalogName"] = "phase-escalation"
        self.rejects(plan, "actionCatalogName to a name no bound resource declares")

    def test_accepts_a_catalog_field_that_names_a_bound_resource(self):
        plan = baseline_plan()
        names = [str(b.get("default") or "") for b in (plan.get("bindings") or []) if b.get("default")]
        if not names:
            self.skipTest("the baseline declares no bound resource name to point at")
        task(plan, "Escalate delayed buyer review")["data"]["actionCatalogName"] = names[0]
        self.accepts(plan)

    def test_rejects_an_input_the_sdd_binds_but_the_plan_leaves_empty(self):
        # The shape an agent shipped: the fields are declared, every binding dropped. The
        # runtime reads that as a missing field, not as an empty string, and the agent job
        # for one of these faulted on `Field required [type=missing, input_value={}]`.
        plan = baseline_plan()
        item = task(plan, "Pull supplier records and screening")
        item["data"]["inputs"] = [
            {"name": field, "type": "string", "value": ""}
            for field in sorted(
                E.sdd_facts()["bound_inputs"]["Pull supplier records and screening"]
            )
        ]
        self.rejects(plan, "with no binding")

    def test_accepts_the_same_inputs_once_they_carry_their_expressions(self):
        plan = baseline_plan()
        item = task(plan, "Pull supplier records and screening")
        item["data"]["inputs"] = [
            {"name": field, "type": "string", "value": f"=vars.{field}"}
            for field in sorted(
                E.sdd_facts()["bound_inputs"]["Pull supplier records and screening"]
            )
        ]
        self.accepts(plan)

    def test_rejects_a_restated_required_flag_on_a_task_input(self):
        # The flag compiles into the dispatch's own required array, so a bound value that
        # resolves empty fails the job before it starts. validate reports Valid.
        plan = baseline_plan()
        task(plan, "Pull supplier records and screening")["data"]["inputs"][0]["required"] = True
        self.rejects(plan, "restate the resource's own contract")

    def test_rejects_a_role_name_in_the_email_recipient_type(self):
        # Type 2 is the email type, so a role name there is read as a literal mailbox and the
        # task reaches nobody. Whether a role is omitted or carried as a group id is left open;
        # this is the shape neither reading allows.
        plan = baseline_plan()
        task(plan, "Obtain legal opinion")["data"]["recipient"] = {
            "Type": E.EMAIL_RECIPIENT_TYPE, "Value": "Legal Counsel"}
        self.rejects(plan, "never as a mailbox")

    def test_rejects_dropped_output(self):
        plan = baseline_plan()
        item = task(plan, "Determine sign-off tier")
        item["data"]["outputs"] = [
            o for o in item["data"]["outputs"] if o.get("var") != "signOffTier"
        ]
        self.rejects(plan, "nothing in the plan writes 'signOffTier'")

    def test_rejects_adhoc_task_in_the_wrong_stage(self):
        plan = baseline_plan()
        moved = copy.deepcopy(task(plan, "Obtain legal opinion"))
        stage(plan, E.BUYER)["data"]["tasks"].append([moved])
        self.rejects(plan, "the source restricts it to")

    def test_rejects_unbound_resource(self):
        plan = baseline_plan()
        target = "Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierErpRegistration"
        plan["bindings"] = [
            b for b in plan["bindings"] if b.get("resourceKey") != target
        ]
        self.rejects(plan, "bound nowhere in the plan")


class SlaLaneTargetTests(CheckerBase):
    checker = "sla"

    def test_rejects_the_lane_opening_on_a_stage_sla(self):
        # Pointed at a phase's SLA, the oversight lane opens the first time any single
        # phase runs late, while the case is still inside its overall target.
        plan = baseline_plan()
        stage_sla_id = None
        for node in plan["nodes"]:
            rules = (node.get("data") or {}).get("slaRules") or []
            if rules and (node.get("data") or {}).get("label") != E.SLA_REVIEW:
                stage_sla_id = rules[0]["id"]
                break
        self.assertIsNotNone(stage_sla_id, "the baseline carries no stage SLA to point at")
        lane = next(
            n for n in plan["nodes"] if (n.get("data") or {}).get("label") == E.SLA_REVIEW
        )
        for cond in (lane.get("data") or {}).get("entryConditions") or []:
            for row in cond.get("rules") or []:
                for rule in row:
                    if rule.get("slaId"):
                        rule["slaId"] = stage_sla_id
        self.rejects(plan, "not on a single phase running late")


class FieldNameTests(CheckerBase):
    checker = "fieldnames"

    def _connector(self, plan):
        """The first connector task in the plan, for a mutation that breaks one wire."""
        for _path, node in _iter_dicts(plan):
            if node.get("type") == "execute-connector-activity":
                return node
        raise AssertionError("the baseline has no connector task")

    def _escalation(self, plan):
        """One escalation task and the phase literal its `stageName` must carry."""
        name, literal = sorted(E.STAGE_NAME_LITERAL.items())[0]
        return task(plan, name), literal

    def test_rejects_a_plan_with_the_wrong_connector_count(self):
        plan = baseline_plan()
        node = self._connector(plan)
        node["type"] = "process"
        self.rejects(plan, "connector task(s) in the plan")

    def test_rejects_a_connector_that_reads_no_delivery_status(self):
        """Without the status extract nothing knows whether the mail went out."""
        plan = baseline_plan()
        node = self._connector(plan)
        node["data"]["outputs"] = [
            o for o in (node["data"].get("outputs") or [])
            if "status" not in json.dumps(o).lower()
        ]
        self.rejects(plan, "no output reads a delivery status")

    def test_rejects_a_re_cased_status_wire(self):
        """`Status not found, did you mean status` is a runtime death `validate` cannot
        see, so the casing is checked here."""
        plan = baseline_plan()
        for o in self._connector(plan)["data"].get("outputs") or []:
            if str(o.get("source") or "").endswith(E.CONNECTOR_OUTPUT_PATH):
                o["source"] = "=response.Status"
        self.rejects(plan, "the status wire path is")

    def test_rejects_an_escalation_with_no_stage_name_input(self):
        """The escalation form has to be told which phase missed its deadline."""
        plan = baseline_plan()
        node, _literal = self._escalation(plan)
        node["data"]["inputs"] = [
            i for i in (node["data"].get("inputs") or [])
            if i.get("name") != E.STAGE_NAME_INPUT
        ]
        self.rejects(plan, f"has no {E.STAGE_NAME_INPUT!r} input")

    def test_rejects_an_escalation_naming_the_wrong_phase(self):
        plan = baseline_plan()
        node, _literal = self._escalation(plan)
        for i in node["data"].get("inputs") or []:
            if i.get("name") == E.STAGE_NAME_INPUT:
                i["value"] = "Some other phase"
        self.rejects(plan, f"sets {E.STAGE_NAME_INPUT}=")

    def test_rejects_an_escalation_carrying_a_sibling_phase_name(self):
        """One phase's escalation must never carry another's name; the supplier would be
        told the wrong phase ran late."""
        plan = baseline_plan()
        node, _literal = self._escalation(plan)
        other = sorted(set(E.STAGE_NAME_LITERAL.values()) - {_literal})[0]
        for i in node["data"].get("inputs") or []:
            if i.get("name") == E.STAGE_NAME_INPUT:
                i["value"] = other
        self.rejects(plan, "name another phase")

    def test_rejects_a_plan_missing_an_escalation_task(self):
        plan = baseline_plan()
        name = sorted(E.STAGE_NAME_LITERAL)[0]
        for node in plan["nodes"]:
            lanes = (node.get("data") or {}).get("tasks") or []
            for lane in lanes:
                for item in list(lane):
                    if item.get("displayName") == name:
                        lane.remove(item)
        self.rejects(plan, f"task {name!r} is missing")

    def test_rejects_a_plan_missing_the_document_reader(self):
        plan = baseline_plan()
        for node in plan["nodes"]:
            for lane in (node.get("data") or {}).get("tasks") or []:
                for item in list(lane):
                    if item.get("displayName") == E.DOCUMENT_READER_TASK:
                        lane.remove(item)
        self.rejects(plan, f"task {E.DOCUMENT_READER_TASK!r} is missing")

    def test_accepts_baseline(self):
        self.accepts(baseline_plan())

    def _task_with_outputs(self, plan):
        for node in plan["nodes"]:
            for item in tasks_of(node):
                outs = (item.get("data") or {}).get("outputs")
                if outs:
                    return item, outs
        self.fail("the baseline has no task carrying outputs")

    def test_accepts_a_row_reading_an_earlier_output_on_its_own_task(self):
        """A task output publishes its own slot, so a later row on the same task can read
        it. Run 33981915823 ships eight connector tasks shaped this way, and checking
        against the declared variables alone called all sixteen reads undefined."""
        plan = baseline_plan()
        item, outs = self._task_with_outputs(plan)
        outs.append({
            "name": "Response", "type": "jsonSchema", "id": "response9",
            "var": "response9", "value": "response9", "source": "=response",
            "target": "=response9", "elementId": item.get("elementId", "root"),
        })
        outs.append({
            "name": "derived", "type": "string", "custom": True,
            "var": "derivedStatus", "value": "=js:vars.response9.status",
            "source": "=js:vars.response9.status", "target": "", "body": "",
            "elementId": "root",
        })
        self.accepts(plan)

    def test_rejects_a_dotted_read_of_a_name_nothing_writes(self):
        plan = baseline_plan()
        _item, outs = self._task_with_outputs(plan)
        outs.append({
            "name": "derived", "type": "string", "custom": True,
            "var": "derivedStatus", "value": "=js:vars.noSuchSlot.status",
            "source": "=js:vars.noSuchSlot.status", "target": "", "body": "",
            "elementId": "root",
        })
        self.rejects(plan, "not a variable the plan holds")

    def _connector_task(self, plan):
        """The same selector the checker uses, so a mutation lands where it looks."""
        for node in plan["nodes"]:
            for item in tasks_of(node):
                if item.get("type") == "execute-connector-activity":
                    return item, item.setdefault("data", {})
        self.fail("the baseline has no connector task")

    def test_rejects_a_container_whose_field_names_are_dotted(self):
        """Run 34558832471 shipped four dotted sibling keys on all eight sends, and
        Integration Services answered `The missing parameters are: Message.`"""
        plan = baseline_plan()
        _item, data = self._connector_task(plan)
        for entry in data.get("inputs") or []:
            if entry.get("name") == "body":
                entry["body"] = {
                    "message.toRecipients": "=js:(vars.contactEmail)",
                    "message.subject": "subject",
                }
                break
        else:
            self.fail("the baseline connector task has no `body` container")
        self.rejects(plan, "dotted field names")

    def test_rejects_an_extract_output_named_by_its_whole_path(self):
        """`io-binding/impl-json.md` gives `name` the leaf for a nested path. The row
        still writes its variable through `var`, so nothing at runtime reports it."""
        plan = baseline_plan()
        _item, data = self._connector_task(plan)
        (data.setdefault("outputs", [])).append({
            "name": "response.status", "type": "string", "id": "status",
            "var": "lastEmailStatus", "value": "lastEmailStatus",
            "source": "=response.status", "target": "=status", "originalVar": "status",
        })
        self.rejects(plan, "the whole path")

    def test_rejects_a_probe_value_left_in_a_container(self):
        """Run 34613296008 shipped `message.body.content: "test"` on one of eight sends,
        left over from asking the validator what shape it wanted."""
        plan = baseline_plan()
        _item, data = self._connector_task(plan)
        for entry in data.get("inputs") or []:
            if entry.get("name") == "body":
                entry.setdefault("body", {})["message"] = {"body": {"content": "test"}}
                break
        else:
            self.fail("the baseline connector task has no `body` container")
        self.rejects(plan, "probe value")

    def test_accepts_pascal_case_output_labels(self):
        """A PascalCase `displayName` is a label, not the wire path."""
        plan = baseline_plan()
        for node in plan["nodes"]:
            for item in tasks_of(node):
                for out in (item.get("data") or {}).get("outputs") or []:
                    if out.get("displayName"):
                        out["displayName"] = out["displayName"].title()
        self.accepts(plan)

    def test_rejects_pascal_cased_wire_path(self):
        plan = baseline_plan()
        for node in plan["nodes"]:
            for item in tasks_of(node):
                for out in (item.get("data") or {}).get("outputs") or []:
                    if out.get("source") == "=" + E.CONNECTOR_OUTPUT_PATH:
                        out["source"] = "=Response.Status"
        self.rejects(plan, "re-cased variant")

    def test_rejects_a_status_wire_read_through_vars(self):
        # The `=` custom-output shape on a row the SDD writes with `->`: the wire
        # dereferences the output slot's own name, and the read yields undefined.
        plan = baseline_plan()
        for node in plan["nodes"]:
            for row in (node.get("data") or {}).get("tasks") or []:
                for task in row:
                    for out in (task.get("data") or {}).get("outputs") or []:
                        if out.get("source") == "=" + E.CONNECTOR_OUTPUT_PATH:
                            out["source"] = "=js:vars.response2.status"
        self.rejects(plan, "as if it were a case variable")

    def test_rejects_status_landing_in_the_wrong_slot(self):
        plan = baseline_plan()
        for node in plan["nodes"]:
            for item in tasks_of(node):
                for out in (item.get("data") or {}).get("outputs") or []:
                    if out.get("source") == "=" + E.CONNECTOR_OUTPUT_PATH:
                        out["var"] = "escalationNotes"
        self.rejects(plan, "lands in")

    def test_rejects_dotted_read_of_an_unknown_root(self):
        """A dereference off a variable the plan does not hold yields undefined."""
        plan = baseline_plan()
        item = task(plan, "Confirm offering category match")
        item["data"]["inputs"].append(
            {"name": "injected", "type": "string",
             "value": "=js:(vars.noSuchDocument.FullName)"}
        )

        self.rejects(plan, "the read yields undefined")

    def test_rejects_dropped_document_read(self):
        """The category-match agent must still read all four supporting documents."""
        plan = baseline_plan()
        item = task(plan, E.DOCUMENT_READER_TASK)
        item["data"]["inputs"] = [
            {"name": "submittedDocuments", "type": "string",
             "value": "=js:(vars.registrationCertificate)"}
        ]

        self.rejects(plan, "does not read")

    def test_accepts_guarded_document_walk(self):
        """The build's guarded array walk reads the same four variables and must pass.

        An assertion that pinned the SDD's literal `vars.X.FullName` spelling would fail
        this — and this shape is strictly better, since it survives a missing document.
        """
        self.accepts(baseline_plan())




class VariableTests(CheckerBase):
    checker = "variables"

    def _row(self, plan, group, category):
        """One variable of this SDD category, in this plan group, for a mutation."""
        # The formal `inputs` and `outputs` slots carry a minted id and the SDD name in
        # `name`; only the `inputOutputs` companion is keyed by the name in both.
        facts = E.sdd_facts()["variables"]
        for entry in (plan.get("variables") or {}).get(group) or []:
            declared = facts.get(entry.get("name"))
            if declared and declared[0] == category:
                return entry
        raise AssertionError(f"the baseline has no Category {category} row in {group!r}")

    def test_rejects_an_input_slot_whose_default_was_dropped(self):
        """An `In` row's `inputs` slot carries the SDD's default; the case starts without
        it otherwise."""
        plan = baseline_plan()
        self._row(plan, "inputs", "In").pop("default", None)
        self.rejects(plan, "carries no `default`")

    def test_rejects_an_input_companion_that_carries_a_default(self):
        """The `In` companion in `inputOutputs` holds no default; the formal slot does."""
        plan = baseline_plan()
        self._row(plan, "inputOutputs", "In")["default"] = "anything"
        self.rejects(plan, "carries a `default`")

    def test_rejects_a_non_string_default(self):
        """A non-string default is dropped silently on the way to BPMN, so the case
        starts with the slot empty and nothing reports it."""
        plan = baseline_plan()
        self._row(plan, "inputs", "In")["default"] = 750000
        self.rejects(plan, "and a non-string one is dropped")

    def test_rejects_a_trigger_argument_marked_as_case_state(self):
        """`custom: true` on an `In` row reads it as case state, so the trigger's value
        never arrives."""
        plan = baseline_plan()
        self._row(plan, "inputOutputs", "In")["custom"] = True
        self.rejects(plan, "is a trigger argument and is marked")

    def test_accepts_baseline(self):
        self.accepts(baseline_plan())

    def test_rejects_a_dropped_case_variable(self):
        plan = baseline_plan()
        plan["variables"]["inputOutputs"] = [
            e for e in plan["variables"]["inputOutputs"] if e["name"] != "riskRating"
        ]
        self.rejects(plan, "'riskRating'")

    def test_rejects_a_retyped_variable(self):
        # `expectedAnnualSpend` written as a string compares as text, so 90000 sorts
        # above 500000 and the sign-off tier inverts.
        plan = baseline_plan()
        for entry in plan["variables"]["inputs"]:
            if entry["name"] == "expectedAnnualSpend":
                entry["type"] = "string"
        self.rejects(plan, "the SDD declares 'double'")

    def test_rejects_a_non_string_default(self):
        plan = baseline_plan()
        for entry in plan["variables"]["inputs"]:
            if entry["name"] == "expectedAnnualSpend":
                entry["default"] = 120000
        self.rejects(plan, "dropped\n    silently" .replace("\n    ", " "))

    def test_rejects_a_file_variable_with_a_default(self):
        plan = baseline_plan()
        for entry in plan["variables"]["inputs"]:
            if entry["name"] == "registrationCertificate":
                entry["default"] = "certificate.pdf"
        self.rejects(plan, "a file default must be the empty string")

    def test_rejects_a_default_the_sdd_does_not_give(self):
        plan = baseline_plan()
        for entry in plan["variables"]["inputs"]:
            if entry["name"] == "contactEmail":
                entry["default"] = "someone.else@example.com"
        self.rejects(plan, "the SDD gives it")

    def test_rejects_case_state_left_unmarked(self):
        plan = baseline_plan()
        for entry in plan["variables"]["inputOutputs"]:
            if entry["name"] == "riskRating":
                entry.pop("custom", None)
        self.rejects(plan, "not marked `custom: true`")


class MetadataTests(CheckerBase):
    checker = "metadata"

    def test_rejects_a_case_named_something_else(self):
        """The case name is what the tenant lists it under."""
        plan = baseline_plan()
        plan["name"] = "Not The Supplier Case"
        self.rejects(plan, "the case is named")

    def test_accepts_baseline(self):
        self.accepts(baseline_plan())

    def test_rejects_a_generated_case_identifier(self):
        plan = baseline_plan()
        plan["metadata"]["caseIdentifierType"] = "generated"
        self.rejects(plan, "the SDD asks for 'constant'")

    def test_rejects_a_different_identifier_prefix(self):
        plan = baseline_plan()
        plan["metadata"]["caseIdentifier"] = "SO"
        self.rejects(plan, "reference numbers")

    def test_rejects_a_disabled_case_app(self):
        plan = baseline_plan()
        plan["metadata"]["caseAppEnabled"] = False
        self.rejects(plan, "nobody this case routes to can open it")

    def test_rejects_task_outputs_not_passed_directly(self):
        # Off, a task's result never reaches the next task's input, and every
        # downstream expression reads an empty slot while the plan stays Valid.
        plan = baseline_plan()
        plan["metadata"]["caseDirectlyPassTaskOutputs"] = False
        self.rejects(plan, "never reaches the next input")

    def test_rejects_a_rejection_that_marks_the_case_complete(self):
        plan = baseline_plan()
        for condition in plan["metadata"]["caseExitRules"]:
            if condition.get("displayName") == "Application rejected":
                condition["marksCaseComplete"] = True
        self.rejects(plan, "must not report the case complete")

    def test_rejects_an_exit_pointed_at_the_wrong_stage(self):
        plan = baseline_plan()
        for condition in plan["metadata"]["caseExitRules"]:
            if condition.get("displayName") == "Application withdrawn":
                for row in condition["rules"]:
                    for rule in row:
                        if rule.get("selectedStageIds"):
                            rule["selectedStageIds"] = [P_stage_id(plan, E.REJECTED)]
        self.rejects(plan, "no case exit condition runs")

    def test_rejects_a_dropped_exit_condition(self):
        plan = baseline_plan()
        plan["metadata"]["caseExitRules"] = plan["metadata"]["caseExitRules"][:2]
        self.rejects(plan, "exit condition(s); the SDD writes")


def P_stage_id(plan: dict, wanted: str) -> str:
    for node in plan["nodes"]:
        if (node.get("data") or {}).get("label") == wanted:
            return node["id"]
    raise AssertionError(f"no stage {wanted!r} in the baseline")


class ConnectorActivityTypeTests(CheckerBase):
    checker = "tasks_io"

    def test_rejects_a_connector_task_running_another_operation(self):
        # A different activity type calls a different Outlook endpoint with this
        # task's payload, and the plan still validates.
        plan = baseline_plan()
        for _stage, task in P_all_tasks(plan):
            if task.get("type") == "execute-connector-activity":
                task["data"]["context"][1]["body"]["activityMetadata"]["activity"][
                    "uiPathActivityTypeId"] = "00000000-0000-0000-0000-000000000000"
                break
        self.rejects(plan, "every send in this case runs")

    def test_rejects_a_connector_task_naming_no_operation(self):
        plan = baseline_plan()
        for _stage, task in P_all_tasks(plan):
            if task.get("type") == "execute-connector-activity":
                task["data"]["context"] = task["data"]["context"][:1]
                break
        self.rejects(plan, "names no activity type")


def P_all_tasks(plan: dict):
    for node in plan["nodes"]:
        for row in (node.get("data") or {}).get("tasks") or []:
            for task in row:
                yield node, task


class TaskEnvelopeTests(CheckerBase):
    checker = "tasks_io"

    def test_rejects_descriptions_dropped_case_wide(self):
        plan = baseline_plan()
        for _stage, task in P_all_tasks(plan):
            task.pop("description", None)
        self.rejects(plan, "carry no `description`")

    def test_rejects_a_dropped_skip_condition(self):
        # Without it the director sign-off runs on every application, including the
        # ones below the threshold that need no signature.
        plan = baseline_plan()
        for _stage, task in P_all_tasks(plan):
            if task.get("displayName") == "Obtain procurement director sign-off":
                task.pop("skipCondition", None)
        self.rejects(plan, "runs on every case that reaches it")

    def test_rejects_a_computed_output_reading_its_own_target(self):
        # `$xref` resolved to the row's own target instead of the producing output's
        # slot, so nothing produces the name and the value never lands. The row below
        # is the shape a real build emits, with `vars.buyerDecision` where the working
        # build writes `vars.action`.
        plan = baseline_plan()
        for _stage, task in P_all_tasks(plan):
            if task.get("displayName") == "Record buyer review decision":
                task["data"]["outputs"].append({
                    "name": "buyerDecision", "type": "string", "custom": True,
                    "var": "buyerDecision", "value": "=js:vars.buyerDecision",
                    "source": "=js:vars.buyerDecision", "target": "", "body": "",
                    "elementId": "root",
                })
        self.rejects(plan, "reads the slot it writes")


class RuleNameUniquenessTests(CheckerBase):
    checker = "topology"

    def test_rejects_two_rules_sharing_a_name_in_one_stage(self):
        # The CLI answers CASE_MGMT_RULE_NAME_DUPLICATE with the stage node in its Path,
        # so the scope is per-stage. Two tasks in one stage reusing a name is the shape
        # the second fixture shipped with, four times over.
        plan = baseline_plan()
        stage = next(n for n in plan["nodes"] if (n.get("data") or {}).get("label") == E.SETUP)
        renamed = 0
        for row in (stage.get("data") or {}).get("tasks") or []:
            for task in row:
                for condition in task.get("entryConditions") or []:
                    condition["displayName"] = "After ERP registration"
                    renamed += 1
        self.assertGreater(renamed, 1, "the baseline's setup stage needs two task entry rules")
        self.rejects(plan, "unique inside a stage")


if __name__ == "__main__":
    unittest.main()
