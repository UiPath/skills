#!/usr/bin/env python3
"""A caseplan the SupplierOnboarding graders accept, built in code.

`test_checkers.py` needs a plan it can break one fact at a time. Committing a real
`caseplan.json` is not how this suite works — every grader unit test here builds its
plan in code (see `sla_from_sdd/test_check_sla_from_sdd.py`) — so this module is that
plan for a case of this size.

**The tables below were generated from a real build, not written from memory.** Every
field name in them was read off a caseplan that passes `uip maestro case validate` and
all five graders. That matters more here than usual: while writing the graders, the
emitted shape turned out to differ from the obvious guess in eight places, and each
wrong guess produced either a false failure on a correct build or an assertion that
could never fire at all. The ones worth naming:

  * `skipCondition` sits at the TASK's top level, not under `data`.
  * A connector task's input expression is nested inside `inputs[].body`; a
    non-connector task's is a plain `inputs[].value`.
  * The plan carries no resource GUIDs. A non-connector task binds through a composite
    `resourceKey` of `<folderPath>.<name>`.
  * An output's reassign target is `var` alone. `target` and `originalVar` hold the
    wire's own id and are deliberately outside the case's variable namespace.
  * `selected-tasks-completed` names its tasks in `selectedTasksIds` — plural on BOTH
    words.
  * `sla-status-change` names the SLA in `slaId` and carries no stage reference.
  * The case's own SLA lives at `metadata.slaRules`; its exits at
    `metadata.caseExitRules`, keyed `marksCaseComplete`.
  * A connector output's `displayName` may be PascalCase (`Response`) while its wire
    path stays lowercase (`response.status`). The label is not part of the contract.

Regenerate from a fresh build after any fixture change.

Input expressions are shortened to the reads they carry: the graders assert which
variables an expression touches, never its prose, so `"Dear " + vars.contactName + …`
becomes `=js:(vars.contactName)`. Everything a grader reads is preserved exactly.
"""

from __future__ import annotations

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
      slas=[('sla_ChkStg01', 2, 'd', [('esc_ck01ar', 'at-risk', 70, 'notification', [('UserGroup', '93a89c1e-be35-410f-ae37-cc5a0e1bd4c2', 'Procurement Operations')]), ('esc_ck02br', 'sla-breached', None, 'notification', [('UserGroup', 'afa0eb1e-0874-47bc-9ce6-8e4c5869de39', 'Procurement Operations Lead')])])],
      entry=[('Condition_ck01en', 'Application submitted', False, None, None, None, [('case-entered', None)]), ('Condition_ck02en', 'Returned for corrections', False, None, None, None, [('selected-stage-exited', {'selectedStageId': 'Stage_Byr7mC', 'conditionExpression': '=js:vars.action2 === "sendback"'})])],
      exits=[('Condition_ck01ex', 'Checks complete', None, 'wait-for-user', True, None, [('required-tasks-completed', None)])],
      lanes=[['tVal01aXk'], ['tPul02bYm'], ['tCat03cZn'], ['tDoc04dAp'], ['tEscChk01'], ['tNteChk02']]),
    S('Stage_Byr7mC', 'Buyer review', None,
      slas=[('sla_ByrStg01', 4, 'd', [('esc_by01ar', 'at-risk', 70, 'notification', [('UserGroup', '74c6d5cc-0684-4ff4-9537-1c80681ad9e8', 'Category Management')]), ('esc_by02br', 'sla-breached', None, 'notification', [('UserGroup', 'afa0eb1e-0874-47bc-9ce6-8e4c5869de39', 'Procurement Operations Lead')])])],
      entry=[('Condition_by01en', 'Checks passed', False, None, None, None, [('selected-stage-completed', {'selectedStageId': 'Stage_Chk4kA'})])],
      exits=[('Condition_by01ex', 'Buyer declined', None, 'exit-only', False, 'Stage_Rej5rG', [('selected-tasks-completed', {'selectedTasksIds': ['tByr06fCr'], 'conditionExpression': '=js:vars.action2 === "reject"'})]), ('Condition_by02ex', 'Sent back for corrections', None, 'exit-only', False, 'Stage_Chk4kA', [('selected-tasks-completed', {'selectedTasksIds': ['tByr06fCr'], 'conditionExpression': '=js:vars.action2 === "sendback"'})]), ('Condition_by03ex', 'Buyer approved', None, 'wait-for-user', True, None, [('required-tasks-completed', {'conditionExpression': '=js:vars.buyerDecision === "approve"'})])],
      lanes=[['tNtf05eBq'], ['tByr06fCr'], ['tInf07gDs'], ['tRef08hEt'], ['tEscByr01'], ['tNteByr02']]),
    S('Stage_Cmp3nD', 'Compliance and risk review', None,
      slas=[('sla_CmpStg01', 4, 'd', [('esc_cm01ar', 'at-risk', 70, 'notification', [('UserGroup', 'e158a23e-f553-4107-82d5-68b788134d33', 'Compliance')]), ('esc_cm02br', 'sla-breached', None, 'notification', [('UserGroup', 'afa0eb1e-0874-47bc-9ce6-8e4c5869de39', 'Procurement Operations Lead')])])],
      entry=[('Condition_cm01en', 'Buyer approved', False, None, None, None, [('selected-stage-completed', {'selectedStageId': 'Stage_Byr7mC', 'conditionExpression': '=js:vars.buyerDecision === "approve"'})])],
      exits=[('Condition_cm01ex', 'Compliance rejected', None, 'exit-only', False, 'Stage_Rej5rG', [('selected-tasks-completed', {'selectedTasksIds': ['tCmp12nJx'], 'conditionExpression': '=js:vars.action4 === "reject"'})]), ('Condition_cm02ex', 'Sent to setup', None, 'wait-for-user', True, None, [('required-tasks-completed', {'conditionExpression': '=js:vars.complianceDecision === "approve"'})])],
      lanes=[['tCrc09jFu'], ['tTie10kGv'], ['tDir11mHw'], ['tCmp12nJx'], ['tFin13pKy'], ['tLgl14qLz'], ['tEscCmp01'], ['tNteCmp02']]),
    S('Stage_Set8pE', 'Setting up the supplier', None,
      slas=[('sla_SetStg01', 3, 'd', [('esc_st01ar', 'at-risk', 70, 'notification', [('UserGroup', '93a89c1e-be35-410f-ae37-cc5a0e1bd4c2', 'Procurement Operations')]), ('esc_st02br', 'sla-breached', None, 'notification', [('UserGroup', 'afa0eb1e-0874-47bc-9ce6-8e4c5869de39', 'Procurement Operations Lead')])])],
      entry=[('Condition_st01en', 'Compliance approved', False, None, None, None, [('selected-stage-completed', {'selectedStageId': 'Stage_Cmp3nD', 'conditionExpression': '=js:vars.complianceDecision === "approve"'})])],
      exits=[('Condition_st01ex', 'Bank verification failed', None, 'exit-only', False, 'Stage_Rej5rG', [('selected-tasks-completed', {'selectedTasksIds': ['tErp15rMa'], 'conditionExpression': '=js:vars.bankVerificationStatus !== "verified"'})]), ('Condition_st02ex', 'Setup complete', None, 'exit-only', True, None, [('required-tasks-completed', {'conditionExpression': '=js:vars.bankVerificationStatus === "verified"'})])],
      lanes=[['tErp15rMa'], ['tNeg16sNb', 'tPrt17tPc'], ['tEscSet01'], ['tNteSet02']]),
    S('Stage_Onb2qF', 'Supplier onboarded', None,
      slas=[('sla_OnbStg01', 2, 'd', [('esc_on01ar', 'at-risk', 70, 'notification', [('UserGroup', '93a89c1e-be35-410f-ae37-cc5a0e1bd4c2', 'Procurement Operations')]), ('esc_on02br', 'sla-breached', None, 'notification', [('UserGroup', 'afa0eb1e-0874-47bc-9ce6-8e4c5869de39', 'Procurement Operations Lead')])])],
      entry=[('Condition_on01en', 'Setup complete', False, None, None, None, [('selected-stage-completed', {'selectedStageId': 'Stage_Set8pE'})])],
      exits=[('Condition_on01ex', 'Onboarding complete', None, 'exit-only', True, None, [('required-tasks-completed', None)])],
      lanes=[['tWlc18uQd', 'tReg19vRe']]),
    S('Stage_Rej5rG', 'Application rejected', 'secondary',
      slas=[('sla_RejStg01', 2, 'd', [('esc_rj01ar', 'at-risk', 70, 'notification', [('UserGroup', '93a89c1e-be35-410f-ae37-cc5a0e1bd4c2', 'Procurement Operations')]), ('esc_rj02br', 'sla-breached', None, 'notification', [('UserGroup', 'afa0eb1e-0874-47bc-9ce6-8e4c5869de39', 'Procurement Operations Lead')])])],
      entry=[('Condition_rj01en', 'Buyer declined', True, None, None, None, [('selected-stage-exited', {'selectedStageId': 'Stage_Byr7mC', 'conditionExpression': '=js:vars.action2 === "reject"'})]), ('Condition_rj02en', 'Compliance rejected', True, None, None, None, [('selected-stage-exited', {'selectedStageId': 'Stage_Cmp3nD', 'conditionExpression': '=js:vars.action4 === "reject"'})]), ('Condition_rj03en', 'Bank verification failed', True, None, None, None, [('selected-stage-exited', {'selectedStageId': 'Stage_Set8pE', 'conditionExpression': '=js:vars.bankVerificationStatus !== "verified"'})])],
      exits=[('Condition_rj01ex', 'Rejection complete', None, 'exit-only', True, None, [('required-tasks-completed', None)])],
      lanes=[['tRjn20wSf', 'tAud21xTg']]),
    S('Stage_Wdr9sH', 'Application withdrawn', 'secondary',
      slas=[('sla_WdrStg01', 2, 'd', [('esc_wd01ar', 'at-risk', 70, 'notification', [('UserGroup', '93a89c1e-be35-410f-ae37-cc5a0e1bd4c2', 'Procurement Operations')]), ('esc_wd02br', 'sla-breached', None, 'notification', [('UserGroup', 'afa0eb1e-0874-47bc-9ce6-8e4c5869de39', 'Procurement Operations Lead')])])],
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
    "slaRules": [
        _sla(
            (
                "sla_RootCse1",
                15,
                "d",
                [
                    ("esc_rt01ar", "at-risk", 80, "notification",
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
