<!-- UIPATH-AUTOMATION-GENOME: component | This file is a build specification for one UiPath automation project.
     Do NOT execute these steps directly. Use the UiPath skills referenced in Build With to create
     the automation project. -->

# Genome: Invoice Extraction and Matching

> RPA process with three entry points: dispatch mailbox attachments to the intake queue, extract and three-way match one invoice, and post one invoice to SAP.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Use the skills listed in **Build With** below to create a UiPath automation project that implements this workflow.

> Part of: [Invoice Processing](../invoice-processing-genome.md) — the worker; all document and SAP interaction lives here.

## Overview

One RPA project, three entry points. The dispatcher runs every 15 minutes, saves new PDF attachments from the AP mailbox to the invoice bucket, and creates one queue item each. The matching entry point, started by the orchestration process, extracts the invoice fields with Document Understanding, reads the PO from SAP, and evaluates the three-way match. The poster, also started by the orchestration process, enters the invoice in SAP and returns the document number.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| Exchange Online (shared AP mailbox) | Input source | Integration Service connection; unread mails with PDF attachments |
| Document Understanding | Field extraction | Pre-trained invoice model; confidence per field |
| SAP S/4HANA (SAP GUI) | PO lookup, invoice posting | Transactions for PO display and incoming invoice entry |
| Orchestrator | Queue, bucket, credential | |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| Entry point A (dispatcher), steps 1-3 | `uipath-rpa` | Mailbox connector activities and queue creation in XAML |
| Entry point B (matching), steps 4-7 | `uipath-rpa` | Document Understanding extraction plus SAP GUI UI automation; matching logic as a coded (C#) workflow in the same project |
| Entry point C (poster), steps 8-9 | `uipath-rpa` | SAP GUI UI automation |

## Platform Dependencies

| Resource | Type | Purpose |
|----------|------|---------|
| AP_InvoiceIntake | Queue | Dispatcher writes one item per invoice |
| AP_Invoices | Storage bucket | PDFs and extraction results |
| SAP_AP_Robot | Credential asset | SAP GUI login |
| AP_Mailbox | Integration Service connection (Exchange Online) | Mailbox access |

## Interface

- **Inputs:** A: none (scheduled). B: `PdfBucketPath`. C: invoice record (`VendorId`, `InvoiceNumber`, `InvoiceDate`, `PoNumber`, line items, `Subtotal`, `Tax`, `Total`, `Currency`)
- **Outputs:** A: queue items. B: invoice record, `MatchResult` (`matched` / `exception`), `Discrepancies[]` (field, expected, actual). C: `ErpDocumentNumber` or `ErpRejection` (message)
- **Side effects:** PDFs saved to the bucket; mails marked read; SAP invoice documents created

## Configuration Questions

1. Which mailbox and folder are scanned? (default: ap-invoices@contoso.com, Inbox/Suppliers)
2. Below which Document Understanding field confidence is a field treated as unreadable? (default: 0.8)
3. What tolerance applies to line and total mismatches? (default: 1% or €5, whichever is greater)
4. Which SAP company codes are in scope? (default: 1000, 2000)
5. Which SAP transaction posts incoming invoices? (default: the standard incoming-invoice transaction)

## Workflow

1. **Trigger A**: time trigger every 15 minutes.
2. **Scan mailbox** (output: list of unread mails with at least one PDF attachment): read unread mails in the configured folder; skip mails without a PDF and notify the sender that no invoice was attached.
3. **Dispatch** (input: mail; output: queue item): save each PDF to the bucket under `year/month/<mailId>.pdf`, create a queue item with `MailId`, `PdfBucketPath`, `ReceivedAt`, `SenderAddress`, mark the mail read.
4. **Trigger B**: started by the orchestration process with `PdfBucketPath`.
5. **Extract fields** (input: PDF; output: invoice record with per-field confidence): run the invoice model; fields: vendor name and tax ID, invoice number and date, PO number, currency, line items (description, quantity, unit price, line total), subtotal, tax, total.
   a. Any required field (vendor, invoice number, total) below the confidence threshold → `Discrepancies` gets `unreadable-field` with the field name; `MatchResult` = `exception`; return.
6. **Look up vendor and PO** (input: vendor tax ID, `PoNumber`; output: PO summary):
   a. Resolve `VendorId` from the tax ID in SAP; missing → discrepancy `unknown-vendor`
   b. No PO number or PO not open → discrepancy `no-open-po`
   c. Read PO lines (material, quantity, unit price, remaining value) and goods-receipt quantities
7. **Three-way match** (input: invoice record, PO summary; output: `MatchResult`, `Discrepancies[]`):
   a. Duplicate check: vendor + invoice number already in SAP → `duplicate`
   b. Each invoice line matched to a PO line by material or description; unmatched → `unmatched-line`
   c. Quantity ≤ goods received; price within tolerance; line total = quantity × unit price within tolerance
   d. Subtotal = sum of lines; subtotal + tax = total; all within tolerance
   e. Total ≤ PO remaining value
   f. No discrepancies → `matched`, else `exception`
8. **Trigger C**: started by the orchestration process with the (possibly corrected) invoice record.
9. **Post to SAP** (input: invoice record; output: `ErpDocumentNumber` or `ErpRejection`): log in with the credential asset, enter the invoice against the PO, simulate, post, read the document number. SAP error messages are returned verbatim in `ErpRejection`.

## Business Rules

### Step 5: Extract fields
- Required fields: vendor, invoice number, total. Everything else may be missing without raising an exception.

### Step 7: Three-way match
- Tolerance per Configuration Question 3, applied to line total, subtotal, and total independently.
- Quantity may be below goods received (partial invoice) but never above.

### Step 9: Post to SAP
- Post only in company codes from Configuration Question 4; another company code returns `ErpRejection` "company code out of scope" without touching SAP.

## Error Handling

### Step 2: Scan mailbox
- Mailbox connection failure: retry 3× with 30-second backoff, then fail the job (next scheduled run retries).

### Step 5: Extract fields
- Document Understanding unavailable: retry 2×, then fail the job; the orchestration process handles the faulted job.

### Step 9: Post to SAP
- SAP GUI session lost: close and log in again once; a second loss fails the job.
- SAP rejection (duplicate, locked period, blocked vendor): return `ErpRejection`, do not retry.

### Global
- Unhandled exception: log the invoice number and PDF path, take a screenshot when SAP is open, fail the job.

## Transactional Shape

The project is the producer — entry point A creates the items; entry points B and C run one item's work per job started by the orchestration, so the project has no consumer role.

| Producer | Reads | Writes items to | Reference rule | Trigger |
|---|---|---|---|---|
| Entry point A (dispatcher) | unread mails with a PDF attachment in the configured mailbox folder | `AP_InvoiceIntake` | one item per mail id; a second item for the same mail id is closed as `duplicate` by the orchestration | every 15 minutes |

The source mail is marked read and its PDF saved to the bucket once the item is queued.

**Recommendation:** per the process genome — not applied.

## Acceptance Criteria

- [ ] Given three unread mails with PDFs and one without, the dispatcher creates three queue items and emails the fourth sender.
- [ ] Given an invoice PDF, entry point B returns vendor, invoice number, date, PO number, line items, subtotal, tax, total, and currency.
- [ ] Given a field below the confidence threshold, `MatchResult` is `exception` with `unreadable-field` naming the field.
- [ ] Given an invoice whose lines match the PO within 1% and total below the remaining value, `MatchResult` is `matched` with no discrepancies.
- [ ] Given a line price 3% above the PO price, `Discrepancies` contains the line, the PO price, and the invoice price.
- [ ] Given an invoice number already posted for the vendor, `Discrepancies` contains `duplicate`.
- [ ] Given a valid record, the poster returns an SAP document number and the invoice is visible in SAP against the PO.
- [ ] Given SAP rejects the posting, `ErpRejection` carries SAP's message and no second attempt is made.

## Complexity

complex

## Tags

rpa, document-understanding, sap, three-way-match, queue-dispatcher, queues, invoice
