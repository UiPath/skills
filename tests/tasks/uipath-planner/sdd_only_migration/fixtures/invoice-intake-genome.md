<!-- UIPATH-AUTOMATION-GENOME: component | This file is a build specification for one UiPath automation project.
     To build it, invoke the uipath-planner skill's `build` verb: it asks the configuration questions,
     then invokes the skills referenced in Build With. Do NOT execute these steps directly, and do NOT
     start from a Build With skill. -->

# Genome: Invoice Intake

> Reads supplier invoices from the AP mailbox, validates them against the approved vendor list and credit limits, and queues approved ones for ERP posting.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Build it with the **uipath-planner** skill's `build` verb, which hands each part to the skill listed in **Build With** below.

> Map binding: SNAP-INVOICE-INTAKE-001

## Overview

Accounts payable receives supplier invoices as PDF attachments in a shared mailbox. Each weekday the automation reads every unread invoice mail, reads the vendor, invoice number and total from the PDF, and checks the vendor against the approved vendor list and its credit limit. Approved invoices are queued for ERP posting; rejected ones are reported to the AP lead, and a mail without an attachment is answered to its sender.

The accountable process owner is not recorded in the source. *[Inferred]* [MAP-INVOICE-INTAKE]

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| AP mailbox | Input source | IMAP server imap.contoso.com |
| Approved vendor list | Input source | Excel workbook with vendor names and credit limits |
| Invoice PDFs | Input source | Text PDFs; no OCR |
| ERP posting queue | Output target | Orchestrator queue ERP_InvoicePosting, worked by another process |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| Steps 1-6 | `uipath-rpa` | Mailbox, Excel, PDF and queue work on one robot in one run; no coordination needed, so no orchestrator |

## Platform Dependencies

| Resource | Type | Purpose |
|----------|------|---------|
| ERP_InvoicePosting | Queue | Approved invoices handed on for ERP posting |
| AP_Mailbox_Login | Credential | Sign-in to the AP mailbox |

## Interface

- **Inputs:** none — the automation runs unattended with no arguments and reads the AP mailbox and the approved vendor list.
- **Outputs:** one ERP_InvoicePosting queue item per approved invoice.
- **Side effects:** rejection mails to the AP lead, answers to senders of mails without an attachment, unreadable PDFs moved to the failed folder.

## Configuration Questions

1. Which IMAP server holds the AP mailbox? (setting; default: imap.contoso.com)
2. Who receives rejection notices? (setting; default: ap-lead@contoso.com)
3. Where is the approved vendor list workbook? (setting; default: not in the export)

## Workflow

1. **Start the run** (input: none; output: approved vendor list): log the start and read the approved vendor list with each vendor's credit limit.
2. **Fetch invoice mails** (input: AP mailbox; output: unread invoice mails): read every unread mail; a mail without an attachment is answered to its sender with "Invoice not processed - attachment missing" and skipped. [EXC-001]
3. **Read the invoice** (input: PDF attachment; output: vendor, invoice number, total):
   a. Save the PDF attachment and read its text
   b. The vendor is the first line, the invoice number follows "Invoice No", the total follows "Total"
   c. A PDF without an invoice number or a total is moved to the failed folder *[Inferred]* [EXC-002]
4. **Validate the invoice** (input: invoice fields, vendor list; output: approved or rejected with the reason): apply the vendor and amount rules. [RULE-001] [RULE-002]
5. **Hand on or reject** (input: validation result; output: queue item or notice): an approved invoice becomes an item of the ERP_InvoicePosting queue; a rejected one is mailed to the AP lead with subject "Invoice <number> rejected". [DEC-001]
6. **End the run**: log one result row per invoice and the end of the run.

## Business Rules

### Step 4: Validate the invoice
- If the vendor is not on the approved vendor list, the invoice is rejected as unknown vendor. [RULE-001]
- If the total is zero or less, exceeds the vendor's credit limit, or exceeds 25,000, the invoice is rejected. [RULE-002]

## Error Handling

### Step 3: Read the invoice
- Invoice number or total not found: the PDF is moved to the failed folder and the next mail is read; where a person picks it up, and who is told, is not recorded in the source. *[Inferred]* [EXC-002]

### Global
- Unhandled exception: the run stops naming the step.

## Transactional Shape

**Flows:** Flow 1 — invoice: step 5 → ERP posting outside this genome.

### Flow 1 — invoice: Invoice Intake → ERP posting

**Unit of work:** one invoice; reference the invoice number; about 40 a day; chosen because each invoice is queued, rejected or set apart on its own.
**Alternative units of work:** none.

**As-is** — how the project handles the units today:

| Aspect | As-is |
|---|---|
| Produced by | step 5, one queue item per approved invoice |
| Consumed by | another process outside this genome |
| Item store | Orchestrator queue ERP_InvoicePosting |
| Coordination | none |
| Item kinds | one kind |
| Step groups | once per run: step 1; per item: steps 2–5; at the end: step 6 |

Split options: none — the consumer is outside this genome: the ERP posting process.

**Evidence:** one robot, one weekday run; the queue is read by the ERP posting process.
**Configuration:** settings — questions 1, 2, 3; assets — AP_Mailbox_Login.
**Traceability:** one result row per invoice in the run's log; the queue item per approved invoice.

## Acceptance Criteria

1. Given an invoice from an approved vendor within its credit limit, the automation adds one ERP_InvoicePosting item for it. [DEC-001]
2. Given an invoice from a vendor not on the list, the automation rejects it and mails the AP lead. [RULE-001]
3. Given an invoice whose total exceeds 25,000, the automation rejects it and mails the AP lead. [RULE-002]
4. When a mail has no attachment, the automation answers the sender that the attachment is missing. [EXC-001]
5. When the PDF has no invoice number, the automation moves it to the failed folder and continues. [EXC-002]

## Complexity

medium

## Tags

accounts-payable, invoice, mailbox, excel, pdf, queues

## Source Map

| Row | Source artifact | Notes |
|-----|-----------------|-------|
| Source framework | UiPath: `InvoiceIntake` (project 1.4.0) | Windows-Legacy XAML project |
| Related resources | none | the request named none |

### Steps

| Step | Source objects | Data sets | Captures | Notes |
|------|----------------|-----------|----------|-------|
| 1 | `Main.xaml` | none | 0 | reads the vendor workbook |
| 2 | `Main.xaml` | none | 0 | the attachment check |
| 3 | `ExtractInvoiceFields.xaml` | none | 0 | called per mail |
| 4 | `ValidateInvoice.xaml` | none | 0 | called per invoice |
| 5 | `Main.xaml` | none | 0 | queue item or rejection mail |
| 6 | `Main.xaml` | none | 0 | result rows |
