<!-- UIPATH-AUTOMATION-GENOME: component | This file is a build specification for one UiPath automation project.
     Do NOT execute these steps directly. Use the UiPath skills referenced in Build With to create
     the automation project. -->

# Genome: Invoice Orchestration

> Long-running BPMN process, one instance per invoice, that sequences extraction, matching, AI triage, human review, and ERP posting.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Use the skills listed in **Build With** below to create a UiPath automation project that implements this workflow.

> Part of: [Invoice Processing](../invoice-processing-genome.md) — the coordinator; owns the lifecycle of each invoice from queue item to posted or rejected.

## Overview

Each queue item on the intake queue starts one instance of this process. The instance calls the extraction robot, decides between straight posting and exception handling, involves the triage agent and an AP clerk for exceptions, and ends with a posted ERP document number or a rejection sent to the supplier. Instances live for minutes on the happy path and up to five business days when waiting on humans.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| Orchestrator | Starts robot and agent jobs, holds the queue item | |
| Action Center | Human review task | Validation app shows PDF, fields, discrepancies, proposal |
| Exchange Online | Supplier rejection email | Sent through the mailbox connection |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| Steps 1-8 (whole process) | `uipath-maestro-bpmn` | Long-running, multi-day waits on a human lane, gateways, boundary timers — BPMN, not Flow. Human review gate designed with `uipath-human-in-the-loop`. |

## Platform Dependencies

| Resource | Type | Purpose |
|----------|------|---------|
| AP_InvoiceIntake | Queue | Trigger; one item per instance |
| Invoice Extraction and Matching | Deployed process (component 2) | Invoked at steps 2 and 6 with different entry points |
| Exception Triage Agent | Deployed agent (component 3) | Invoked at step 4 |
| AP Invoice Review | Action Center app | Human review task at step 5 |
| AP_Invoices | Storage bucket | PDF link shown to the clerk |

## Interface

- **Inputs:** queue item specific content — `MailId`, `PdfBucketPath`, `ReceivedAt`, `SenderAddress`
- **Outputs:** instance variables `Outcome` (`posted` / `rejected` / `duplicate` / `stale`), `ErpDocumentNumber`, `RejectionReason`
- **Side effects:** robot and agent jobs, one Action Center task per exception, supplier rejection email, queue item status

## Configuration Questions

1. How long may an instance wait on human review before reassigning to the team lead? (default: 1 business day)
2. After how long is a stuck instance terminated as stale? (default: 5 business days)
3. How many ERP rejections before the invoice is rejected outright? (default: 2)
4. Which app renders the human review task? (default: AP Invoice Review)

## Workflow

1. **Trigger**: a new item on the intake queue starts the instance with the item's specific content.
2. **Extract and match** (input: `PdfBucketPath`; output: invoice record, `MatchResult`, `Discrepancies[]`): start the extraction robot's matching entry point and wait.
3. **Route on match result**: `matched` and total ≤ auto-approval ceiling → step 6; otherwise → step 4.
4. **Triage** (input: invoice record, discrepancies, PO summary; output: `Proposal`, `Confidence`, `Rationale`): start the triage agent and wait. If the agent fails or `Confidence` < 0.4, set `Proposal` = `manual`.
5. **Human review** (input: record, discrepancies, proposal; output: `Decision` ∈ {approve-proposal, override, reject}, `CorrectedRecord`): create the Action Center task and wait. Boundary timer per Configuration Question 1 reassigns to the team lead.
6. **Post** (input: record or `CorrectedRecord`; output: `ErpDocumentNumber` or `ErpRejection`): start the robot's posting entry point and wait.
   a. Success → step 8 with `Outcome` = `posted`
   b. Rejection and rejection count < limit → add discrepancy `erp-rejected` with the ERP message, → step 4
   c. Rejection at the limit → step 7
7. **Reject** (input: `RejectionReason`): send the supplier a rejection email with the reason and invoice number; `Outcome` = `rejected`.
8. **Close**: set the queue item to Successful (`posted`) or Failed with the reason (`rejected`, `duplicate`, `stale`); end.

## Business Rules

### Step 3: Route on match result
- A matched invoice whose total exceeds the auto-approval ceiling still goes to human review, with `Proposal` = `approve` from the agent.

### Step 5: Human review
- `approve-proposal` applies the agent's proposal; `override` requires the clerk to pick one of the same three resolutions and may edit fields; `reject` requires a reason.

### General
- One posting attempt per corrected record; the same record is never posted twice.

## Error Handling

### Step 2: Extract and match
- Job faulted: retry once after 5 minutes, then continue to step 4 with a single discrepancy `extraction-failed`.

### Step 4: Triage
- Agent job faulted or timed out (10 minutes): `Proposal` = `manual`, continue.

### Step 5: Human review
- Task open past the configured SLA: reassign to the team lead, mark `SlaBreached`, keep waiting.

### Global
- Instance older than the stale limit: terminate, `Outcome` = `stale`, queue item Failed with the instance ID.
- A second instance for an invoice number already open or already posted: `Outcome` = `duplicate`, queue item Failed.

## Transactional Shape


### Flow 1 — one supplier invoice: component 2 → component 1

**Role:** takes Flow 1's items — its queue trigger starts one instance per invoice, and that instance retries, tracks and escalates its invoice; a coordinator, not an RPA consumer.

Split options: per the process genome, Flow 1.

## Acceptance Criteria

- [ ] Given a queue item, exactly one instance starts and reads all four specific-content fields.
- [ ] Given `MatchResult` = `matched` and total below the ceiling, the posting job starts without a triage or review step.
- [ ] Given `MatchResult` = `exception`, the triage agent job starts before any Action Center task is created.
- [ ] Given agent confidence 0.3, the review task shows proposal `manual`.
- [ ] Given a review task older than the SLA, it is reassigned to the team lead and the instance keeps waiting.
- [ ] Given the clerk rejects with a reason, the supplier email contains that reason and the invoice number, and the queue item is Failed with the same reason.
- [ ] Given two ERP rejections, the instance ends `rejected` without a third posting attempt.

## Complexity

complex

## Tags

bpmn, orchestration, human-in-the-loop, action-center, queues, invoice
