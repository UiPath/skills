<!-- UIPATH-AUTOMATION-GENOME: component | This file is a build specification for one UiPath automation project.
     Do NOT execute these steps directly. Use the UiPath skills referenced in Build With to create
     the automation project. -->

# Genome: Exception Triage Agent

> Classifies a failed invoice match and proposes one of three resolutions with a confidence score and a rationale for the reviewing clerk.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Use the skills listed in **Build With** below to create a UiPath automation project that implements this workflow.

> Part of: [Invoice Processing](../invoice-processing-genome.md) — advisory only; every proposal is confirmed by an AP clerk.

## Overview

Given an invoice record, its discrepancies, and the PO summary, the agent decides whether the mismatch is a correctable data error (wrong PO line, transposed digits, rounding), a commercial dispute that needs a supplier credit note, or a reason to reject. It explains its reasoning in two or three sentences aimed at an AP clerk and reports how confident it is. It never posts, rejects, or contacts anyone.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| Orchestrator | Job input and output | Started by the orchestration process |
| AP_Invoices storage bucket | Reads the extraction JSON when line detail is needed | Read-only |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| Steps 1-5 | `uipath-agents` | Natural-language reasoning over structured discrepancies; low-code agent with a single read-only tool |

## Platform Dependencies

| Resource | Type | Purpose |
|----------|------|---------|
| AP_Invoices | Storage bucket | Optional read of full extraction output |

## Interface

- **Inputs:** invoice record, `Discrepancies[]` (field, expected, actual), PO summary (lines, remaining value, goods received)
- **Outputs:** `Proposal` ∈ {repost-with-correction, request-supplier-credit-note, reject}, `Confidence` (0-1), `Rationale` (text), `CorrectedRecord` (only for repost-with-correction)
- **Side effects:** none

## Configuration Questions

1. Which model runs the agent? (default: the tenant's default reasoning model)
2. Above which price variance is a mismatch treated as a commercial dispute rather than a data error? (default: 10%)
3. Should the agent read the full extraction JSON from the bucket, or only the discrepancies passed in? (default: discrepancies only; bucket read on `unmatched-line`)

## Workflow

1. **Receive** (input: record, discrepancies, PO summary).
2. **Fetch line detail when needed** (input: `unmatched-line` discrepancies; output: full extraction output): when a discrepancy is `unmatched-line` and Configuration Question 3 allows it, read the extraction JSON from the bucket to see every invoice line; otherwise work from the discrepancies alone.
3. **Classify each discrepancy**:
   a. `unreadable-field`, transposed digits, rounding within 2× tolerance, wrong PO line with an obvious match → data error
   b. Price variance above the dispute threshold, quantity above goods received, total above PO remaining value → commercial dispute
   c. `unknown-vendor`, `duplicate`, `no-open-po` with no plausible PO → reject candidate
4. **Propose**: reject if any reject candidate; else credit note if any commercial dispute; else repost-with-correction with a `CorrectedRecord` where every corrected field is listed with old and new value.
5. **Explain and score**: two to three sentences naming the discrepancies and why the proposal follows; `Confidence` reflects how many discrepancies had a clear classification.

## Business Rules

### Step 4: Propose
- Reject outranks credit note, which outranks correction.
- `CorrectedRecord` never changes vendor or invoice number; those are reject candidates when wrong.

### General
- The agent has no tool that writes anywhere. Guardrail: output must be one of the three proposals or `manual`.

## Error Handling

### Step 3: Classify each discrepancy
- Discrepancy type not recognised: classify as commercial dispute, lower `Confidence` by 0.2 per unknown type.

### Global
- Model error or timeout: the job fails; the orchestration process substitutes `manual`.

## Acceptance Criteria

- [ ] Given a single `unmatched-line` discrepancy where one PO line has the same description and price, the proposal is `repost-with-correction` with that PO line in `CorrectedRecord`.
- [ ] Given a line price 15% above the PO price, the proposal is `request-supplier-credit-note`.
- [ ] Given a `duplicate` discrepancy, the proposal is `reject` regardless of other discrepancies.
- [ ] Given two discrepancies of unknown type, `Confidence` is at least 0.4 lower than for the same record with known types.
- [ ] Given any input, `Rationale` mentions every discrepancy field by name.
- [ ] Given any input, the output is exactly one of the three proposals or `manual`.

## Complexity

medium

## Tags

agent, triage, invoice, exceptions, advisory
