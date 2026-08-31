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
import json
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
CASE_VERSION = "27.0.0"


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
        # `task_is_skeleton` reads a non-empty `context` for this class.
        data["context"] = [{"name": "connectionId", "type": "string", "value": "conn"}]
        data["serviceType"] = "Intsvc.ActivityExecution"
    else:
        data["name"] = "=bindings.b" + task_id[:6]
        data["folderPath"] = "=bindings.b" + task_id[:6] + "f"

    task: dict = {
        "id": task_id,
        "type": task_type,
        "displayName": display_name,
        "isRequired": req,
        "shouldRunOnlyOnce": once,
        "entryConditions": [
            {
                "id": f"c_{task_id}",
                "displayName": "entry",
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
    # --- Compliance and risk review ---
    T('tCrc09jFu', 'api-workflow', 'Run compliance and risk check',
      req=True, once=False, entry=[('runs-sequentially', None)],
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.countryOfRegistration', 'vars.sanctionsFindings', 'vars.duplicateSupplierIds'],
      outputs=[('riskRating', 'riskRating', 'riskRating', '=riskRating', None), ('complianceFlags', 'complianceFlags', 'complianceFlags', '=complianceFlags', None)]),
    T('tCmp12nJx', 'action', 'Record compliance review decision',
      req=True, once=False, entry=[('runs-sequentially', None)],
      reads=['metadata.ExternalId', 'vars.companyName', 'vars.contactName', 'vars.contactEmail', 'vars.countryOfRegistration', 'vars.offeringCategory', 'vars.expectedAnnualSpend', 'vars.spendCurrency', 'vars.riskRating', 'vars.complianceFlags', 'vars.sanctionsFindings', 'vars.duplicateSupplierIds', 'vars.financialHealthSummary', 'vars.fraudIndicators', 'vars.concernLevel', 'vars.signOffTier', 'vars.directorSignOffDecision', 'vars.directorSignOffNotes', 'vars.buyerComments', 'vars.referenceCheckFindings', 'vars.legalOpinion', 'vars.complianceComments'],
      outputs=[('Action', 'action4', 'complianceDecision', '=Action', None), ('Comment', 'comment6', 'complianceComments', '=Comment', None)]),
    # --- Setting up the supplier ---
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
]

# --- Stages, generated from a real build ----------------------------------------
STAGES = [
    S('Stage_Chk4kA', 'Checking the application', None,
      slas=[('sla_ChkStg01', *E.STAGE_SLA[E.CHECKING], [('esc_ck01ar', 'at-risk', E.STAGE_AT_RISK_PERCENT, 'notification', [('UserGroup', '93a89c1e-be35-410f-ae37-cc5a0e1bd4c2', 'Procurement Operations')]), ('esc_ck02br', 'sla-breached', None, 'notification', [('UserGroup', 'afa0eb1e-0874-47bc-9ce6-8e4c5869de39', 'Procurement Operations Lead')])])],
      entry=[('Condition_ck01en', 'Application submitted', False, None, None, None, [('case-entered', None)]), ('Condition_ck02en', 'Returned for corrections', False, None, None, None, [('selected-stage-exited', {'selectedStageId': 'Stage_Byr7mC', 'conditionExpression': '=js:vars.action2 === "sendback"'})])],
      exits=[('Condition_ck01ex', 'Checks complete', None, 'wait-for-user', True, None, [('required-tasks-completed', None)])],
      lanes=[['tVal01aXk'], ['tPul02bYm'], ['tCat03cZn'], ['tDoc04dAp'], ['tEscChk01'], ['tNteChk02']]),
    S('Stage_Byr7mC', 'Buyer review', None,
      slas=[('sla_ByrStg01', *E.STAGE_SLA[E.BUYER], [('esc_by01ar', 'at-risk', E.STAGE_AT_RISK_PERCENT, 'notification', [('UserGroup', '74c6d5cc-0684-4ff4-9537-1c80681ad9e8', 'Category Management')]), ('esc_by02br', 'sla-breached', None, 'notification', [('UserGroup', 'afa0eb1e-0874-47bc-9ce6-8e4c5869de39', 'Procurement Operations Lead')])])],
      entry=[('Condition_by01en', 'Checks passed', False, None, None, None, [('selected-stage-completed', {'selectedStageId': 'Stage_Chk4kA'})])],
      exits=[('Condition_by01ex', 'Buyer declined', None, 'exit-only', False, 'Stage_Rej5rG', [('selected-tasks-completed', {'selectedTasksIds': ['tByr06fCr'], 'conditionExpression': '=js:vars.action2 === "reject"'})]), ('Condition_by02ex', 'Sent back for corrections', None, 'exit-only', False, 'Stage_Chk4kA', [('selected-tasks-completed', {'selectedTasksIds': ['tByr06fCr'], 'conditionExpression': '=js:vars.action2 === "sendback"'})]), ('Condition_by03ex', 'Buyer approved', None, 'wait-for-user', True, None, [('required-tasks-completed', {'conditionExpression': '=js:vars.buyerDecision === "approve"'})])],
      lanes=[['tNtf05eBq'], ['tByr06fCr']]),
    S('Stage_Cmp3nD', 'Compliance and risk review', None,
      slas=[('sla_CmpStg01', *E.STAGE_SLA[E.COMPLIANCE], [('esc_cm01ar', 'at-risk', E.STAGE_AT_RISK_PERCENT, 'notification', [('UserGroup', 'e158a23e-f553-4107-82d5-68b788134d33', 'Compliance')]), ('esc_cm02br', 'sla-breached', None, 'notification', [('UserGroup', 'afa0eb1e-0874-47bc-9ce6-8e4c5869de39', 'Procurement Operations Lead')])])],
      entry=[('Condition_cm01en', 'Buyer approved', False, None, None, None, [('selected-stage-completed', {'selectedStageId': 'Stage_Byr7mC', 'conditionExpression': '=js:vars.buyerDecision === "approve"'})])],
      exits=[('Condition_cm01ex', 'Compliance rejected', None, 'exit-only', False, 'Stage_Rej5rG', [('selected-tasks-completed', {'selectedTasksIds': ['tCmp12nJx'], 'conditionExpression': '=js:vars.action4 === "reject"'})]), ('Condition_cm02ex', 'Sent to setup', None, 'wait-for-user', True, None, [('required-tasks-completed', {'conditionExpression': '=js:vars.complianceDecision === "approve"'})])],
      lanes=[['tCrc09jFu'], ['tCmp12nJx']]),
    S('Stage_Set8pE', 'Setting up the supplier', None,
      slas=[('sla_SetStg01', *E.STAGE_SLA[E.SETUP], [('esc_st01ar', 'at-risk', E.STAGE_AT_RISK_PERCENT, 'notification', [('UserGroup', '93a89c1e-be35-410f-ae37-cc5a0e1bd4c2', 'Procurement Operations')]), ('esc_st02br', 'sla-breached', None, 'notification', [('UserGroup', 'afa0eb1e-0874-47bc-9ce6-8e4c5869de39', 'Procurement Operations Lead')])])],
      entry=[('Condition_st01en', 'Compliance approved', False, None, None, None, [('selected-stage-completed', {'selectedStageId': 'Stage_Cmp3nD', 'conditionExpression': '=js:vars.complianceDecision === "approve"'})])],
      exits=[('Condition_st01ex', 'Bank verification failed', None, 'exit-only', False, 'Stage_Rej5rG', [('selected-tasks-completed', {'selectedTasksIds': ['tErp15rMa'], 'conditionExpression': '=js:vars.bankVerificationStatus !== "verified"'})]), ('Condition_st02ex', 'Setup complete', None, 'exit-only', True, None, [('required-tasks-completed', {'conditionExpression': '=js:vars.bankVerificationStatus === "verified"'})])],
      lanes=[['tErp15rMa'], ['tNeg16sNb', 'tPrt17tPc']]),
    S('Stage_Onb2qF', 'Supplier onboarded', None,
      slas=[('sla_OnbStg01', *E.STAGE_SLA[E.ONBOARDED], [('esc_on01ar', 'at-risk', E.STAGE_AT_RISK_PERCENT, 'notification', [('UserGroup', '93a89c1e-be35-410f-ae37-cc5a0e1bd4c2', 'Procurement Operations')]), ('esc_on02br', 'sla-breached', None, 'notification', [('UserGroup', 'afa0eb1e-0874-47bc-9ce6-8e4c5869de39', 'Procurement Operations Lead')])])],
      entry=[('Condition_on01en', 'Setup complete', False, None, None, None, [('selected-stage-completed', {'selectedStageId': 'Stage_Set8pE'})])],
      exits=[('Condition_on01ex', 'Onboarding complete', None, 'exit-only', True, None, [('required-tasks-completed', None)])],
      lanes=[['tWlc18uQd', 'tReg19vRe']]),
    S('Stage_Rej5rG', 'Application rejected', 'secondary',
      slas=[],
      entry=[('Condition_rj01en', 'Buyer declined', True, None, None, None, [('selected-stage-exited', {'selectedStageId': 'Stage_Byr7mC', 'conditionExpression': '=js:vars.action2 === "reject"'})]), ('Condition_rj02en', 'Compliance rejected', True, None, None, None, [('selected-stage-exited', {'selectedStageId': 'Stage_Cmp3nD', 'conditionExpression': '=js:vars.action4 === "reject"'})]), ('Condition_rj03en', 'Bank verification failed', True, None, None, None, [('selected-stage-exited', {'selectedStageId': 'Stage_Set8pE', 'conditionExpression': '=js:vars.bankVerificationStatus !== "verified"'})])],
      exits=[('Condition_rj01ex', 'Rejection complete', None, 'exit-only', True, None, [('required-tasks-completed', None)])],
      lanes=[['tRjn20wSf', 'tAud21xTg']]),
    S('Stage_Wdr9sH', 'Application withdrawn', 'secondary',
      slas=[],
      entry=[('Condition_wd01en', 'Supplier withdrew', True, None, None, None, [('user-selected-stage', None)])],
      exits=[('Condition_wd01ex', 'Withdrawal complete', None, 'exit-only', True, None, [('required-tasks-completed', None)])],
      lanes=[['tWdc22yUh', 'tWcl23zVj']]),
]

# --- Variables and bindings, generated from a real build -------------------------
INPUTS = [   # (id, name, type, default)
    ('vCmp1aXk2', 'companyName', 'string', 'Northwind Components Ltd'),
    ('vCon2bYm3', 'contactName', 'string', 'Alex Fisher'),
    ('vCem3cZn4', 'contactEmail', 'string', 'yiqi.hu@uipath.com'),
    ('vCtr4dAp5', 'countryOfRegistration', 'string', 'United Kingdom'),
    ('vOfc5eBq6', 'offeringCategory', 'string', 'Components'),
    ('vExs6fCr7', 'expectedAnnualSpend', 'double', '120000'),
    ('vSpc7gDs8', 'spendCurrency', 'string', 'USD'),
    ('vOfd8hEt9', 'offeringDescription', 'string', 'Precision machined components for industrial pumps'),
    ('vSbd9jFu1', 'submittedDate', 'date', '2026-08-26'),
    ('vRgc1kGv2', 'registrationCertificate', 'file', ''),
    ('vIns2mHw3', 'insuranceDocument', 'file', ''),
    ('vTax3nJx4', 'taxFormsDocument', 'file', ''),
    ('vBnk4pKy5', 'bankDetailsDocument', 'file', ''),
]

OUTPUTS = [   # (id, name, type, var)
    ('vSup5qLz6', 'supplierId', 'string', 'supplierId'),
    ('vCso6rMa7', 'caseOutcome', 'string', 'caseOutcome'),
]

INPUT_OUTPUTS = [   # (name, type) — id equals name for every one
    ('companyName', 'string'),
    ('contactName', 'string'),
    ('contactEmail', 'string'),
    ('countryOfRegistration', 'string'),
    ('offeringCategory', 'string'),
    ('expectedAnnualSpend', 'double'),
    ('spendCurrency', 'string'),
    ('offeringDescription', 'string'),
    ('submittedDate', 'date'),
    ('registrationCertificate', 'file'),
    ('insuranceDocument', 'file'),
    ('taxFormsDocument', 'file'),
    ('bankDetailsDocument', 'file'),
    ('validationOutcome', 'string'),
    ('validationIssues', 'string'),
    ('addedDocumentName', 'string'),
    ('duplicateSupplierIds', 'string'),
    ('sanctionsFindings', 'string'),
    ('assignedBuyerEmail', 'string'),
    ('categoryMatches', 'boolean'),
    ('suggestedCategory', 'string'),
    ('reviewNotes', 'string'),
    ('buyerDecision', 'string'),
    ('buyerComments', 'string'),
    ('referenceCheckFindings', 'string'),
    ('riskRating', 'string'),
    ('complianceFlags', 'string'),
    ('financialHealthSummary', 'string'),
    ('fraudIndicators', 'string'),
    ('concernLevel', 'string'),
    ('signOffTier', 'string'),
    ('directorSignOffRequired', 'boolean'),
    ('directorSignOffDecision', 'string'),
    ('directorSignOffNotes', 'string'),
    ('legalOpinion', 'string'),
    ('complianceDecision', 'string'),
    ('complianceComments', 'string'),
    ('bankVerificationStatus', 'string'),
    ('portalAccessConfirmation', 'string'),
    ('registeredAt', 'string'),
    ('applicationCheckRevisedDate', 'string'),
    ('buyerReviewRevisedDate', 'string'),
    ('complianceReviewRevisedDate', 'string'),
    ('supplierSetupRevisedDate', 'string'),
    ('escalationNotes', 'string'),
    ('lastEmailStatus', 'string'),
    ('auditRecordId', 'string'),
    ('cleanupSummary', 'string'),
    ('reviewsCancelled', 'boolean'),
    ('timersStopped', 'boolean'),
    ('addedDocumentType', 'string'),
    ('addedDocumentContent', 'string'),
    ('addedDocumentSubmittedOn', 'string'),
    ('supplierId', 'string'),
    ('caseOutcome', 'string'),
]
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
    ('bCrc01aaa', 'name', 'process', 'Api', 'Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierComplianceRiskCheck', 'SupplierComplianceRiskCheck', 'name'),
    ('bCrc02bbb', 'folderPath', 'process', 'Api', 'Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierComplianceRiskCheck', 'Shared/uipath-maestro-case/SupplierOnboardingKit', 'folderPath'),
    ('bScr01aaa', 'name', 'app', None, 'Shared/uipath-maestro-case/Supplier Compliance Review.Supplier Compliance Review', 'Supplier Compliance Review', 'name'),
    ('bScr02bbb', 'folderPath', 'app', None, 'Shared/uipath-maestro-case/Supplier Compliance Review.Supplier Compliance Review', 'Shared/uipath-maestro-case/Supplier Compliance Review', 'folderPath'),
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
                     "selectedStageId": "Stage_Rej5rG"}]]},
        {"id": "Condition_ce03cc", "displayName": "Application withdrawn",
         "marksCaseComplete": False,
         "rules": [[{"id": "Rule_ce03cc", "rule": "selected-stage-completed",
                     "selectedStageId": "Stage_Wdr9sH"}]]},
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
                {"id": name, "name": name, "type": vtype}
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

    def test_rejects_a_plural_stage_selector(self):
        # validate accepts the plural array; the case then faults on CaseRulesEvaluatorNode
        # before any task opens, so no other assertion here ever gets to run.
        plan = baseline_plan()
        for cond in plan["metadata"]["caseExitRules"]:
            for group in cond["rules"]:
                for rule in group:
                    if "selectedStageId" in rule:
                        rule["selectedStageIds"] = [rule.pop("selectedStageId")]
        self.rejects(plan, "selectedStageIds")

class GuardTests(CheckerBase):
    checker = "guards"

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


class SlaTests(CheckerBase):
    checker = "sla"

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
        # Retargeted to the one wrap-up that still carries an SLA of its own: the two terminal
        # lanes no longer have one, so a task added there answers no breach.
        node = stage(plan, E.ONBOARDED)
        escalation = copy.deepcopy(task(plan, "Escalate delayed application check"))
        node["data"]["tasks"].append([escalation])
        self.rejects(plan, "starts task(s)")


class TasksIoTests(CheckerBase):
    checker = "tasks_io"

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
        task(plan, "Attach supporting documents")["data"]["recipient"] = {
            "Type": E.EMAIL_RECIPIENT_TYPE, "Value": "Legal Counsel"}
        self.rejects(plan, "never as a mailbox")

    def test_accepts_a_real_address_in_the_email_recipient_type(self):
        # The same slot with an actual address is exactly what Type 2 is for.
        plan = baseline_plan()
        task(plan, "Attach supporting documents")["data"]["recipient"] = {
            "Type": E.EMAIL_RECIPIENT_TYPE, "Value": "legal@uipath.com"}
        self.accepts(plan)

    def test_rejects_a_required_flag_on_a_task_input(self):
        # Compiles into the dispatch's input schema and fails the job before it starts; validate
        # reports Valid either way. Found by running the case, not by reading it.
        plan = baseline_plan()
        task(plan, "Pull supplier records and screening")["data"]["inputs"][0]["required"] = True
        self.rejects(plan, "`required: true`")

    def test_rejects_dropped_output(self):
        plan = baseline_plan()
        item = task(plan, "Run compliance and risk check")
        item["data"]["outputs"] = [
            o for o in item["data"]["outputs"] if o.get("var") != "riskRating"
        ]
        self.rejects(plan, "nothing in the plan writes 'riskRating'")

    def test_rejects_adhoc_task_in_the_wrong_stage(self):
        plan = baseline_plan()
        moved = copy.deepcopy(task(plan, "Attach supporting documents"))
        stage(plan, E.BUYER)["data"]["tasks"].append([moved])
        self.rejects(plan, "the source restricts it to")

    def test_rejects_unbound_resource(self):
        plan = baseline_plan()
        target = "Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierErpRegistration"
        plan["bindings"] = [
            b for b in plan["bindings"] if b.get("resourceKey") != target
        ]
        self.rejects(plan, "bound nowhere in the plan")


class FieldNameTests(CheckerBase):
    checker = "fieldnames"

    def test_accepts_baseline(self):
        self.accepts(baseline_plan())

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


if __name__ == "__main__":
    unittest.main()
