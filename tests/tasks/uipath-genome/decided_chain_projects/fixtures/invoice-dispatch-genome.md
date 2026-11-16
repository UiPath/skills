<!-- UIPATH-AUTOMATION-GENOME: component | This file is a build specification for one UiPath automation project.
     To build it, invoke the uipath-genome skill: it asks the configuration questions,
     then invokes the skills referenced in Build With. Do NOT execute these steps directly, and do NOT
     start from a Build With skill. -->

# Genome: Invoice Dispatch

> Every weekday morning, turns the day's invoice export into one approval file per invoice and a register of what was filed.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Build it with the **uipath-genome** skill, which hands each part to the skill listed in **Build With** below.

## Overview

Finance drops one CSV export of the day's supplier invoices into a shared input folder each morning, about 400 invoices. The automation queues one item per invoice, checks each invoice and writes its approval file into the output folder, then records every filed or rejected invoice as one row of the Excel invoice register. Each invoice succeeds, fails and is retried on its own.

It runs unattended on Orchestrator triggers and needs no application with a user interface.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| Shared file folders | Source and destination | Input, output and register folders on the finance share |
| CSV file | Source data | One export per day, header row: InvoiceNumber, Supplier, Amount, Currency, DueDate |
| Excel workbook | Output | The invoice register, written as a file; no Excel installation is needed on the robot |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| Steps 1-7: read the export, check and file each invoice, register it | `uipath-rpa` | File and table work with no user interface — RPA processes over Orchestrator queues, unattended |

## Platform Dependencies

| Resource | Type | Purpose |
|----------|------|---------|
| Invoice_Items | Queue | Hand-off 1, InvoiceDispatcher → InvoicePerformer: one item per invoice of the export |
| Invoice_Register | Queue | Hand-off 2, InvoicePerformer → InvoiceReporter: one item per invoice filed or rejected |
| Invoice_InputFolder | Text asset | Folder the daily export arrives in |
| Invoice_OutputFolder | Text asset | Folder the approval files are written to |
| Invoice_RegisterPath | Text asset | Path of the invoice register workbook |

## Interface

Runs unattended with no arguments; outputs are the side effects listed in Workflow.

## Configuration Questions

1. Which folder does the daily invoice export arrive in? (setting; default: the finance share's `Invoices\Inbox` folder)
2. Which folder receives the approval files? (setting; default: the finance share's `Invoices\Approval` folder)
3. Where is the invoice register workbook? (setting; default: the finance share's `Invoices\Register.xlsx`)
4. Above which amount does an invoice need a second approver? (constant; default: 5000.00)
5. How many times is a failed invoice retried? (constant; default: 2)
6. After how many consecutive failures does a run stop? (constant; default: 3)

## Workflow

1. **Read the day's export** (input: input folder; output: invoice rows): read the newest file ending in `.csv` in the input folder as a table with its header row. If there is none, write a message to the job log and end the run.
2. **Queue the invoices** (input: invoice rows; output: one Invoice_Items item per invoice): add one item per row with the invoice number as its reference; an invoice number already on the queue is skipped and counted in the job log.
3. **Take the next invoice** (input: Invoice_Items; output: one invoice): take the next item in queue order.
4. **Check the invoice** (input: one invoice; output: approval route): reject it when Supplier is empty, Amount is not a positive number, or DueDate is not a date; otherwise route it to one approver, or two when Amount is above the second-approver amount.
5. **Write the approval file** (input: invoice, approval route, output folder; output: the approval file): write `<InvoiceNumber>.json` into the output folder with the invoice fields and the approval route, replacing a file of the same name.
6. **Hand the invoice to the register** (input: invoice, outcome; output: one Invoice_Register item): add one item with the invoice number, the outcome (Filed or Rejected) and the reason.
7. **Register the invoice** (input: Invoice_Register, register path; output: one register row): append one row — InvoiceNumber, Supplier, Amount, Outcome, Reason, the date and time — to the register workbook.

## Business Rules

### Step 4: Check the invoice
- If Amount is above the second-approver amount, the approval route names two approvers; otherwise one.
- An invoice with an empty Supplier, a non-positive Amount or an unreadable DueDate is rejected with the reason.

### Step 7: Register the invoice
- Every invoice taken in step 3 gets exactly one register row, filed or rejected.

## Error Handling

### Step 5: Write the approval file
- If the output folder cannot be written, the invoice is a system exception and is retried.

### Step 7: Register the invoice
- If the register workbook is locked, the item is a system exception and is retried.

### Global
- Any other failure on an invoice is a system exception for that invoice only.

## Transactional Shape

**Flows:** Flow 1 — invoice: steps 1–2 → steps 3–6 → step 7.

### Flow 1 — one invoice: steps 1–2 → steps 3–6 → step 7

**Unit of work:** one invoice; reference the invoice number, unique per invoice; fields InvoiceNumber, Supplier, Amount, Currency, DueDate; about 400 a day, queued once every weekday morning.

**As-is** — how the work is described:

| Aspect | As-is |
|---|---|
| Produced by | Steps 1–2, once every weekday at 07:00: one item per invoice of the export |
| Consumed by | Steps 3–6 per invoice, then step 7 per filed or rejected invoice |
| Item store | One Orchestrator queue per hand-off, in chain order: `Invoice_Items` (steps 1–2 → steps 3–6), then `Invoice_Register` (steps 3–6 → step 7) |
| Coordination | The invoice number as queue reference keeps an invoice from being queued twice |
| Item kinds | One kind |
| Step groups | per item: steps 3–6; per register item: step 7 (steps 1–2 are the producer's own) |

| Outcome | When | Effect |
|---|---|---|
| Success | the approval file is written and the invoice handed to the register | item recorded as done; register row Filed |
| Business exception | Step 4 rules: empty Supplier, non-positive Amount, unreadable DueDate | no retry; item recorded with the reason; register row Rejected; run continues |
| System exception | every other failure — Step 5 and Step 7 handlers | item retried 2× (Configuration Question 5), then recorded as failed with the reason; run stops after 3 consecutive (Configuration Question 6) |

**Split options** — the decided option:

| Unit of work | Option | Requires | Changes against as-is |
|---|---|---|---|
| one invoice | B | a time trigger for the dispatcher and queue triggers for the performer and the reporter | three processes to publish and operate instead of one; each invoice is retried and visible on its own queue item |

**Evidence:** about 400 invoices a day; each invoice is checked and filed independently; finance needs per-invoice status; the register is one workbook written by one process at a time.
**Decided:** B, one invoice — the SDD §10: InvoiceDispatcher → InvoicePerformer → InvoiceReporter
**Configuration:** settings — questions 1-3 (input folder, output folder, register path); constants — questions 4-6 (second-approver amount, item retries, consecutive-failure threshold); assets — every Text asset row of Platform Dependencies.
**Traceability:** each queue item's status and history per invoice number; one register row per invoice.

## Acceptance Criteria

1. Given an export of three valid invoices, three approval files are written and the register gains three Filed rows.
2. Given an invoice above the second-approver amount, its approval file names two approvers.
3. Given an invoice with an empty Supplier, no approval file is written for it and its register row is Rejected with the reason.
4. Given an export listing one invoice number twice, only one item is queued for it.
5. When the input folder holds no CSV file, the job log says so and nothing is queued.
6. When the register workbook is locked, the register item is retried and the row is appended once the workbook is free.

## Complexity

medium

## Tags

finance, invoices, queues, file-processing, scheduled
