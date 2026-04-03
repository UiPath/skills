# Genome: Invoice Processing

> Extract data from PDF invoices received by email, validate against PO records, and post to ERP.

## Overview

A common accounts payable automation. Monitors an email inbox for incoming invoices, extracts structured data using Document Understanding, validates against purchase orders, and enters approved invoices into the ERP system. Exceptions are flagged for human review.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| Email (Outlook/Gmail) | Input source | Shared mailbox for AP |
| ERP (SAP/Oracle/NetSuite) | Data entry target | Invoice posting |
| Document Understanding | Field extraction | PDF/image invoices |
| Excel/SharePoint | Exception log | Optional |

## Configuration Questions

1. Which email provider and mailbox? (Outlook/Gmail, shared mailbox address)
2. Which ERP system and transaction? (e.g. SAP MIRO, Oracle AP Invoice Entry)
3. What fields to extract? (defaults: invoice number, date, vendor, line items, amounts, tax, total)
4. Where are PO records stored for validation? (ERP lookup, Excel, SharePoint list)
5. What should happen with exceptions? (email notification, Excel log, queue in Orchestrator)
6. What's the invoice volume? (affects batching strategy)

## Workflow

1. **Trigger**: Scheduled or email-triggered. Check inbox for unread messages with PDF/image attachments.
2. **Download**: Save attachments to a working folder. Log sender, subject, timestamp.
3. **Classify**: Use Document Understanding to confirm document is an invoice (skip non-invoices).
4. **Extract**: Extract fields — invoice number, date, vendor name/ID, line items (description, quantity, unit price), tax, total.
5. **Validate**:
   - Match vendor against vendor master
   - Match PO number if present
   - Verify line items and totals against PO
   - Flag discrepancies beyond tolerance threshold
6. **Post**: For validated invoices, enter into ERP. Capture confirmation/document number.
7. **Exception**: Route failed validations to exception queue with extraction results and reason.
8. **Confirm**: Mark email as processed. Send summary report.

## Business Rules

- Duplicate detection: skip if invoice number + vendor already exists in ERP
- Tolerance threshold for amount mismatches: configurable (default 1%)
- Three-way match: PO, receipt, invoice when PO is present
- Invoices without PO go to exception queue for manual approval

## Error Handling

- Email connectivity failure: retry 3x with backoff, then alert
- DU extraction confidence below 80%: route to human validation queue
- ERP posting failure: retry once, then log to exception report with full extracted data
- Unreadable attachments (corrupt PDF, password-protected): flag and notify sender

## Acceptance Criteria

- [ ] Correctly extracts all specified fields from a sample invoice PDF
- [ ] Matches extracted data against a sample PO and detects intentional mismatches
- [ ] Posts a valid invoice to the ERP (or mock) and captures confirmation number
- [ ] Routes an invalid invoice to the exception queue with correct reason
- [ ] Detects and skips duplicate invoices
- [ ] Produces a summary report of processed/failed invoices
- [ ] Handles a corrupt PDF attachment without crashing

## Complexity

medium

## Tags

invoice, accounts-payable, email, Document Understanding, SAP, Oracle, ERP, PDF, three-way-match
