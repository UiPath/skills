<!-- UIPATH-AUTOMATION-GENOME: component | This file is a build specification for one UiPath automation project.
     To build it, invoke the uipath-genome skill: it asks the configuration questions,
     then invokes the skills referenced in Build With. Do NOT execute these steps directly, and do NOT
     start from a Build With skill. To change it, invoke the uipath-planner skill. -->

# Genome: SupplierInvoiceEntry

> Collects supplier invoice PDFs from the AP shared mailbox into a queue. Then, one invoice per job, it extracts the fields, checks them against Contoso ERP, gets approval over the limit, and posts the invoice or sets it aside.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Build it with the **uipath-genome** skill, which hands each part to the skill listed in **Build With** below.

> Part of: [Supplier Invoice Entry](../supplier-invoice-entry-genome.md) — the RPA process that collects invoices and works each one through to posting or set-aside, calling the extraction model and Action Center.

## Overview

This process does the supplier invoice entry that AP clerks do by hand today. It has two entry points. The collection entry point runs on a schedule. It reads the unread e-mails in the AP shared mailbox, stores every PDF attachment, and adds one queue item per PDF, so each invoice is tracked on its own from that point. The invoice entry point is started by the queue, one item per job, and works one invoice end to end. It reads the five fields with the extraction model (component 1) and validates them. It checks that the invoice is not already in Contoso ERP and matches it against its purchase order. When the total is over the approval limit, it waits for an approver in Action Center, suspended and holding no robot. It then posts the invoice and records the ERP document number.

Every invoice that cannot be completed is set aside. Its PDF and the reason go to the AP shared mailbox, and the queue item records the outcome. Set-aside reasons: the PO does not match, the approver rejected it, a field could not be read, or it is already in the ERP. AP clerks handle set-aside invoices by hand.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| AP shared mailbox | Both — invoices read from it; e-mails moved to its processed and unprocessed folders; notices sent to it | IMAP to read and SMTP to send *[Inferred: D2]* (SDD [SME REVIEW]: D4: mail platform and protocol) |
| Contoso ERP | Both — purchase order and invoice lookup; invoice posting | Driven through its screens on a Windows unattended robot at 1920×1080 *[Inferred: D1]* (SDD [SME REVIEW]: D5: ERP access route and interface); browser with the UiPath extension or the desktop client installed on the machine; `UI targets: the Contoso ERP test instance` |
| Action Center | Output target — approval tasks | Form task; the job suspends while it waits and resumes on an unattended robot |
| Orchestrator queue and storage bucket | Both — invoice items and their PDFs | Platform Dependencies |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| Steps 1–3 (collection entry point) | `uipath-rpa` | Mail read, move and send, bucket upload and queue add are plain activities. A Sequence project on a cross-platform robot, XAML as the SDD §13 decides. Not an API workflow: there is no confirmed mail API (D2) |
| Steps 4–14 (invoice entry point) | `uipath-rpa` | UI automation of Contoso ERP around one extraction call and one Action Center task: an REFramework project in XAML, Windows, with persistence for the approval wait (SDD §11, §13). The approval form is designed with `uipath-human-in-the-loop` from the business intent in step 10. The SDD §14 packages: System, Mail, UIAutomation, IntelligentOCR, Persistence and FormActivityLibrary activities, latest versions pinned at build |

## Platform Dependencies

### Queues

| Queue | One item is | Item fields | Unique reference | Retries | Added by | Worked by |
|-------|-------------|-------------|------------------|---------|----------|-----------|
| `SupplierInvoiceEntry_Invoices` (Configuration Question 11) | one invoice PDF | MessageId: Text, AttachmentIndex: Integer, AttachmentName: Text, BucketPath: Text, Sender: Text, ReceivedAt: Text (ISO 8601); output Supplier, InvoiceNumber, InvoiceDate, PONumber, Total, ERPDocumentNumber: Text; analytics Outcome, ApprovalOutcome, SetAsideReason: Text; encrypted | `<MessageId>_<AttachmentIndex>`, on | Configuration Question 9 | step 3 | steps 5–13 |

### Assets

| Asset | Type | Value | Used by | Purpose |
|-------|------|-------|---------|---------|
| `SupplierInvoiceEntry_MailServer` | Text | Configuration Question 2 | step 2 | IMAP host and port |
| `SupplierInvoiceEntry_SmtpServer` | Text | Configuration Question 2 | steps 2, 13 | SMTP host and port |
| `SupplierInvoiceEntry_MailFolder` | Text | Configuration Question 3 | steps 2, 3 | Inbox folder collection reads; its processed and unprocessed sub-folders |
| `SupplierInvoiceEntry_SetAsideRecipient` | Text | Configuration Question 4 | steps 2, 13 | Address that set-aside and no-PDF notices go to |
| `SupplierInvoiceEntry_ERPUrl` | Text | Configuration Question 5 | step 4 | ERP address or application path |
| `SupplierInvoiceEntry_ApprovalLimit` | Text | Configuration Question 6 | step 10 | Approval limit, a decimal in Contoso's currency |
| `SupplierInvoiceEntry_ExtractionConfidence` | Text | Configuration Question 7 | step 7 | Minimum confidence per extracted field |
| `SupplierInvoiceEntry_ApproverGroup` | Text | Configuration Question 8 | step 10 | Action Center group that approves |
| `SupplierInvoiceEntry_EscalationGroup` | Text | Configuration Question 8 | step 10 | AP lead group the open task escalates to |

### Credentials

| Asset | Account or persona | Signs in to | Used by |
|-------|--------------------|-------------|---------|
| `SupplierInvoiceEntry_MailCredential` (Configuration Question 11) | AP shared mailbox account | AP shared mailbox (read, move, send) | steps 2, 3, 13 |
| `SupplierInvoiceEntry_ERPCredential` (Configuration Question 11) | Contoso ERP robot account, least privilege: purchase order read, invoice create and post | Contoso ERP | steps 4, 10 |

### Storage buckets

| Bucket | Holds | Written by | Read by |
|--------|-------|------------|---------|
| `SupplierInvoiceEntry_Invoices` (Configuration Question 11) | Each invoice PDF under a folder named after its e-mail's Message-ID | step 3 | steps 6, 10, 13 |

### Triggers

| Trigger | Starts | Kind | When | Runners |
|---------|--------|------|------|---------|
| Collection schedule | collection entry point (step 1) | Time | Configuration Question 1 | 1; a run is skipped while the previous one still runs |
| Invoice queue trigger | invoice entry point (step 4) | Queue | one job per new item on `SupplierInvoiceEntry_Invoices`, one item per job | Configuration Question 10 |

### Action Center

| Resource | Used by | Purpose |
|----------|---------|---------|
| Invoice approval form task | step 10 | The approver approves or rejects an invoice over the limit; a rejection carries a reason |

### Document Understanding

| Resource | Used by | Purpose |
|----------|---------|---------|
| Extraction model SupplierInvoiceEntry_Extraction (component 1) | step 6 | Reads the five invoice fields with a confidence each |

## Interface

- **Inputs:** collection entry point — none; it reads the AP shared mailbox. Invoice entry point — one queue item from `SupplierInvoiceEntry_Invoices` with the fields of the process genome's Handoffs row 1. From component 1, per invoice: Supplier, InvoiceNumber, InvoiceDate, PONumber, Total, each with a confidence (Handoffs row 2). From Action Center: Approved or Rejected, and the approver's reason (Handoffs row 3).
- **Outputs:** per invoice, on its queue item: the extracted fields, ERPDocumentNumber, Outcome (Posted or SetAside), ApprovalOutcome (NotRequired, Approved or Rejected) and SetAsideReason (Unmatched, Rejected, Unreadable or Duplicate), plus ApproverComment for a rejection.
- **Side effects:** PDFs stored in the bucket; e-mails moved to the processed or unprocessed folder; supplier invoices posted in Contoso ERP with the queue reference in their reference text; approval tasks created in Action Center; set-aside and no-PDF notices mailed to the AP shared mailbox.

## Configuration Questions

1. When does collection run — interval, business days and hours, time zone and holiday calendar? (setting; default: every 30 minutes, Monday to Friday 08:00–18:00, Contoso's local time zone, no holiday calendar) *[Inferred: CQ1]* (SDD [SME REVIEW]: D2: business hours and calendar)
2. Which mail servers does the robot use — the IMAP host and port, and the SMTP host and port? (setting; default: none)
3. Which mailbox folder does collection read, with its processed and unprocessed sub-folders? (setting; default: the AP shared mailbox's inbox, with sub-folders `Processed` and `Unprocessed`)
4. Which address receives set-aside and no-PDF notices? (setting; default: the AP shared mailbox address)
5. What is the Contoso ERP address or application path? (setting; default: none)
6. What is the approval limit — an invoice strictly above it needs approval? (constant; default: none — empty sends every invoice to approval) *[Inferred: CQ6]* (SDD [SME REVIEW]: D3: limit value)
7. What is the minimum extraction confidence per field? (constant; default: 0.80)
8. Which Action Center groups approve invoices and receive the escalation? (setting; default: approvers `AP Approvers`, escalation `AP Lead`, both in the process folder) *[Inferred: CQ8]* (SDD [SME REVIEW]: D10: Action Center groups)
9. How many times is a failed invoice retried, and when is support alerted? (constant; default: retried 3× by the queue for system exceptions, none for business exceptions; one item per job, so no consecutive-failure stop; alert after 3 consecutive system exceptions and on every item that exhausts its retries)
10. How many invoice jobs may run at once? (setting; default: 2; suspended jobs do not count)
11. Which names do the Orchestrator resources take? (setting; default: queue and storage bucket `SupplierInvoiceEntry_Invoices`, credentials `SupplierInvoiceEntry_MailCredential` and `SupplierInvoiceEntry_ERPCredential`)

## Open Decisions

1. How is Contoso ERP reached? (reading; answered by: the system's owner; reading: UI automation of the ERP screens on a Windows robot, as the SDD builds now, because the PDD names the ERP but no interface; instead: a REST API through a catalog or custom Integration Service connector; instead: something else, in the owner's words) — Target Applications; steps 4, 8, 9, 11
2. Which mail platform hosts the AP shared mailbox, and how does the robot reach it? (reading; answered by: the system's owner; reading: IMAP to read and SMTP to send, as the SDD builds now, because the PDD says only "E-mail"; instead: Microsoft 365 through the Outlook 365 Integration Service connector; instead: Gmail through the Gmail Integration Service connector) — Target Applications; steps 2, 3, 13
3. Must the invoice date be no later than today? (business outcome; answered by: the process owner; builds now: an invoice dated after today is set aside as Unreadable; instead: accept any real date) — step 7, Validate the extraction
4. Must the total be greater than zero? (business outcome; answered by: the process owner; builds now: a total of zero or less is set aside as Unreadable; instead: accept zero and negative totals, such as credit notes, and post them) — step 7, Validate the extraction
5. How is the invoice's supplier compared with the purchase order's supplier? (business outcome; answered by: the process owner; builds now: the names are equal when case and surrounding spaces are ignored; instead: an exact match; instead: a supplier number read from the invoice) — step 9, Match the purchase order
6. Is the queue reference written into the ERP invoice's reference text when posting? (business outcome; answered by: the process owner; builds now: yes, so a retry recognises its own posting; instead: another ERP field the system's owner names) — step 11, Post the invoice
7. Does an e-mail with no PDF attachment send a notice to AP? (run behaviour; answered by: the process owner; recommended: yes, a notice naming the sender, subject and arrival time, and the e-mail moved to the unprocessed folder) — step 2, Read unread invoice e-mails

## Workflow

### Collection entry point

1. **Trigger: collection schedule** — started by the collection schedule (Configuration Question 1). A run is skipped while the previous one still runs.
2. **Read unread invoice e-mails** (input: the mailbox folder, Configuration Question 3; output: the unread e-mails that carry at least one PDF):
   a. Sign in to the AP shared mailbox with the mailbox credential *[Inferred: D2]*.
   b. Read every unread e-mail in the configured folder, oldest first.
   c. For each e-mail with no PDF attachment: move it to the unprocessed sub-folder and send a notice to the set-aside recipient (Configuration Question 4) naming the sender, subject and arrival time *[Inferred: D7]* (SDD [DEFAULT]: B5 notice). No queue item is added.
3. **Store each PDF and add one queue item per PDF** (input: the e-mails with PDFs; output: queue items, the count added):
   a. Number the e-mail's PDF attachments by their 1-based position in the e-mail.
   b. Upload each PDF to the storage bucket, under a folder named after the e-mail's Message-ID, as the position, an underscore and the attachment's file name.
   c. Add one queue item per PDF with reference Message-ID, underscore, position, carrying the Message-ID, position, file name, bucket path, sender address and arrival time (ISO 8601). A reference the queue refuses as already present counts as added.
   d. Only once every PDF of the e-mail is added, move the e-mail to the processed sub-folder.
   e. At the end of the run, log the e-mails read, items added and e-mails moved to the unprocessed folder.

### Invoice entry point

4. **Start the job and sign in** (input: settings and assets; output: an open, signed-in ERP session):
   a. Read the settings and the asset values of Platform Dependencies.
   b. Open Contoso ERP at its address (Configuration Question 5) if it is not already open. On the Login screen, type the user name and password from the ERP credential and click Sign in *[Inferred: D1]*.
5. **Take the invoice item** (input: the queue; output: the item's fields and reference): take the one queue item this job was started for. Every log line from here on carries the item's reference.
6. **Extract the invoice fields** (input: the bucket path; output: Supplier, InvoiceNumber, InvoiceDate, PONumber, Total and a confidence per field):
   a. Download the PDF from the storage bucket.
   b. Send it to the extraction model (component 1) and receive the five fields with their confidences.
7. **Validate the extraction** (input: the five fields and confidences; output: valid fields, or the list of failing fields):
   a. Supplier, invoice number and PO number are each not empty after trimming.
   b. The invoice date is a real date no later than today *[Inferred: D3]* (SDD [DEFAULT]: BR-06).
   c. The total is a decimal greater than zero *[Inferred: D4]* (SDD [DEFAULT]: BR-08).
   d. Each of the five fields has a confidence at or above the minimum (Configuration Question 7).
   e. If any check fails, the invoice is set aside as Unreadable, listing every failing field (business exception).
8. **Check the invoice is not already in the ERP** (input: supplier, invoice number, the item's reference; output: none found, or the found document number):
   a. On the Supplier invoice search screen, enter the supplier and the invoice number, search, and read the Results list.
   b. If no invoice is found, continue to step 9.
   c. If an invoice is found whose reference text carries this item's reference, it is this item's own earlier attempt: record Outcome Posted with the found document number and continue at step 12. Steps 9 to 11 are skipped.
   d. If an invoice is found with any other reference text, the invoice is set aside as Duplicate, carrying the existing document number (business exception).
9. **Match the purchase order** (input: PO number, supplier, total; output: Matched or Unmatched):
   a. On the Purchase order lookup screen, type the PO number into PO number search and read PO status, PO supplier and PO open amount.
   b. Matched only when the PO is found and open, the PO supplier equals the invoice supplier with case and surrounding spaces ignored *[Inferred: D5]* (SDD [DEFAULT]: §6 supplier comparison), and the total is at or below the PO open amount.
   c. Otherwise the invoice is set aside as Unmatched, naming the check that failed: PO not found or not open, other supplier, or total over the open amount (business exception).
10. **Decide the approval route and get approval** (input: the fields, the PDF, the approval limit; output: ApprovalOutcome, ApproverComment):
    a. If the approval limit (Configuration Question 6) is empty, or the total is strictly above it, approval is needed. Otherwise ApprovalOutcome is NotRequired and the step ends.
    b. Create an approval task for the approver group (Configuration Question 8) showing supplier, invoice number, invoice date, PO number, total and the PDF. Business intent: the approver approves or rejects, and a rejection carries a reason. The task reminds after 2 business days and escalates to the escalation group after 5. The invoice keeps waiting until someone acts.
    c. Suspend the job until the task completes; it resumes on an unattended robot. The ERP session does not survive the wait: on resume, open Contoso ERP and sign in again as in step 4b.
    d. Approved: ApprovalOutcome Approved, continue to step 11. Rejected: ApprovalOutcome Rejected, ApproverComment keeps the reason, and the invoice is set aside as Rejected (business exception).
    e. An item retried after a system exception asks for approval again with a new task. The approval of an earlier attempt is not carried over (decided by the process owner, 2026-11-22).
11. **Post the invoice** (input: the five fields, the item's reference; output: ERPDocumentNumber):
    a. On the Supplier invoice entry screen, type the supplier, invoice number, invoice date, PO number and total. Type the item's reference into the invoice's reference text *[Inferred: D6]* (SDD [DEFAULT]: posting reference text).
    b. Click Post and read the Document number shown. Confirm it is not empty.
12. **Record the outcome** (input: the results of steps 6–11; output: the completed queue item): write the extracted fields, Outcome Posted, ApprovalOutcome and ERPDocumentNumber to the item's output and analytics, and mark the item Successful.
13. **Set the invoice aside** (input: the PDF, the reason, the fields; output: the set-aside notice; runs on every business exception, and after the last retry of a system exception):
    a. Mail the set-aside recipient (Configuration Question 4) with the PDF attached. The mail states the item's reference, the reason, and, by reason: the failing fields (Unreadable), the failed check (Unmatched), the approver's reason (Rejected), the existing document number (Duplicate), or the error (after the last retry).
    b. Write Outcome SetAside, SetAsideReason, ApprovalOutcome and whatever fields were extracted to the item's output and analytics. Mark the item Failed as a business exception, or as a system exception after the last retry.
14. **End the job** — close Contoso ERP.

## Business Rules

### Step 7: Validate the extraction
- Supplier, invoice number and PO number must each be present after trimming; whether the PO exists is decided in step 9.
- The invoice date must be a real date and no later than today *[Inferred: D3]*; the total must exceed zero *[Inferred: D4]*.
- Every one of the five fields must have a confidence at or above the configured minimum (Configuration Question 7, default 0.80); one field below it sets the invoice aside as Unreadable.

### Step 8: Check the invoice is not already in the ERP
- An invoice already in the ERP with the same supplier and invoice number is a duplicate, unless its reference text carries this item's reference, in which case it is this item's own earlier posting and the item ends Posted.

### Step 9: Match the purchase order
- Matched only when all three hold: the PO exists and is open; the PO supplier is the invoice supplier; the invoice total does not exceed the PO open amount. Any other combination is Unmatched.

### Step 10: Decide the approval route and get approval
- If the approval limit is not set, every invoice goes to approval *[Inferred: CQ6]*.
- If the total exceeds the limit, the invoice goes to approval; if it is at or under the limit, it is posted without approval.
- An invoice that needs approval is never posted before an Approve; a Reject sets it aside.

### General
- Outcome is Posted or SetAside; ApprovalOutcome is NotRequired, Approved or Rejected; SetAsideReason is Unmatched, Rejected, Unreadable or Duplicate.
- A posted invoice always carries the ERP document number.
- Logs carry only the reference, supplier, invoice number, PO number, outcome and set-aside reason: no totals, invoice contents or credential values.

## Error Handling

### Step 2: Read unread invoice e-mails
- Mailbox unreachable or sign-in fails: retried 3 times with exponential backoff, then the collection job faults and the support owner is alerted. The next scheduled run picks up the same unread e-mails.

### Step 3: Store each PDF and add one queue item per PDF
- Bucket upload or queue add fails: retried 3 times with exponential backoff. If it still fails, the e-mail stays in the inbox (not moved), so the next run retries it; the unique reference stops a second item.

### Step 6: Extract the invoice fields
- Extraction service error, timeout or no result: system exception; the item is retried by the queue (Configuration Question 9).

### Steps 4, 8, 9, 10 and 11: Contoso ERP
- ERP does not start, login is rejected, or the session is lost: system exception; the ERP is closed and its process killed, then the item is retried. A rejected login is attempted no more than once per attempt, to avoid locking the robot account, and alerts the support owner.
- An ERP screen element not found within 10 seconds, or a page taking more than 30 seconds to load: screenshot logged, ERP restarted, item retried.

### Step 10: Decide the approval route and get approval
- Approval task cannot be created: system exception; item retried; nothing is posted without an approval.

### Step 11: Post the invoice
- Robot or ERP fails after the post is submitted, so the result is unknown: system exception; on the retry, step 8 finds the invoice by this item's reference and completes the item as Posted with the found document number. There is no second posting.

### Global
- Any unanticipated business exception: set the invoice aside with its reason as in step 13 and fail the item as a business exception.
- Any unanticipated system exception: screenshot, log with the item's reference, fail the item as a system exception so the queue retries it (Configuration Question 9). After the last retry, set the invoice aside with the error (step 13) and alert the support owner.

## Transactional Shape

### Flow 1 — one invoice PDF: collection entry point → invoice entry point

**Role:** producer and consumer (it works the items it adds) — the collection entry point turns each PDF in the AP mailbox into a queue item, and the invoice entry point works each item to Posted or SetAside.

| Aspect | As-is |
|---|---|
| Produced by | steps 1–3. Source: unread e-mails in the AP shared mailbox. Reference: Message-ID, underscore, the PDF's 1-based position. The e-mail moves to the processed folder once all its items are added, or to the unprocessed folder when it has no PDF |
| Consumed by | steps 4–14, one item per job, started by the queue trigger, at most Configuration Question 10 jobs running; a job waiting for approval is suspended |
| Step groups | once per run: step 4; per item: steps 5–13; at the end: step 14 |

| Outcome | When | Effect |
|---|---|---|
| Success | every per-item step completed | item Successful with Outcome Posted, ERPDocumentNumber and ApprovalOutcome |
| Business exception | Step 7 rules: field unreadable; Step 8 rules: already in the ERP; Step 9 rules: PO not matched; Step 10 rules: approval rejected | no retry; set-aside notice (step 13); item Failed as a business exception with SetAsideReason |
| System exception | every other failure — Step 6, 8, 9, 10 and 11 handlers | ERP closed and reopened, item retried per Configuration Question 9, then set aside with the error and failed as a system exception; one item per job, so no consecutive stop |

**Configuration:** settings — questions 1, 2, 3, 4, 5, 8, 10, 11; constants — questions 6, 7, 9; assets — every asset row of Platform Dependencies, read at start, except each credential, read where its secret is used (steps 2, 4, 10c).
**Traceability:** reference, status and output on each queue item; the reference in every log line and in the ERP invoice's reference text; a screenshot on every system exception; collection run totals (step 3e).
Split options: per the process genome, Flow 1.

## Acceptance Criteria

1. Given an e-mail with one PDF invoice under the limit that matches an open purchase order, collection adds one queue item with reference `<MessageId>_1`. The invoice is posted in the ERP with the reference in its reference text. The item ends Successful with Outcome Posted, ApprovalOutcome NotRequired and a non-empty ERPDocumentNumber, and the e-mail is in the processed folder.
2. Given an e-mail with two PDF invoices, collection adds two queue items with references ending `_1` and `_2`, and each is worked and recorded independently.
3. Given an e-mail with only a Word attachment, collection adds no queue item, moves the e-mail to the unprocessed folder, and sends a notice to the AP shared mailbox.
4. When collection runs on an e-mail whose items are already queued (moved back to the inbox), no second queue item is added.
5. Given an invoice over the limit, the job suspends with an approval task for the approver group showing the five fields and the PDF; on Approve it resumes, signs in to the ERP again, posts, and records ApprovalOutcome Approved.
6. Given an invoice over the limit that the approver rejects with a reason, the item ends Failed as a business exception with SetAsideReason Rejected and the reason kept, the notice carries the reason, and nothing is posted.
7. When an approval task is left open, it shows the reminder after 2 business days and the escalation to the escalation group after 5 (checked with a shortened test calendar).
8. When the approval limit asset is empty, any invoice, whatever its total, goes to approval.
9. When the limit is set and the total equals it, the invoice is posted without approval; when the total is above it, the invoice goes to approval.
10. Given a PO number not in the ERP, a PO of another supplier, or a total above the PO's open amount, the item ends Failed as a business exception with SetAsideReason Unmatched; the notice names the failed check; nothing is posted.
11. Given a PO found and open, with the same supplier differing only in case or surrounding spaces, and a total at or below the open amount, the invoice is Matched.
12. Given an extraction with an empty supplier, an empty invoice number, an empty PO number, an invoice date of tomorrow, a total of 0, or one field below 0.80 confidence, the item ends Failed as a business exception with SetAsideReason Unreadable, and the notice lists the failing fields.
13. Given an invoice whose supplier and number already exist in the ERP, entered by hand, the item ends Failed as a business exception with SetAsideReason Duplicate; the notice carries the existing document number; nothing is posted.
14. When the robot is stopped right after the post is submitted, the retry finds the invoice by its reference in step 8, completes the item Successful with that document number, and the ERP holds one invoice.
15. When the ERP test instance is stopped or the robot account is locked, the item is retried per Configuration Question 9; a rejected login alerts without repeated sign-in attempts.
16. When an ERP screen element is missing or the page is slow, a screenshot is logged and the item is retried.
17. When the extraction model is unavailable, the item is retried 3 times, then set aside with the error and failed as a system exception, and support is alerted.
18. When the Action Center task cannot be created, the item is retried and nothing is posted.
19. When the mailbox password is wrong, collection faults after its retries, alerts, and leaves the e-mails unread in the inbox.
20. When the bucket upload fails, the e-mail stays in the inbox and the next run, after the fix, adds its items without duplicates.
21. When an approved invoice fails with a system exception before posting, its retry creates a new approval task and posts only after a new Approve.
22. Given 50 invoices delivered in one hour, all are worked within business hours on one runtime, with two invoice jobs on the queue at once and no invoice worked twice.
23. Given readable invoices from at least 5 supplier layouts, the five fields are correct on at least 95% of them, and every invoice not read correctly is set aside as Unreadable, never posted wrong (test data: process D1).

## Complexity

complex

## Tags

accounts-payable, supplier-invoices, contoso-erp, email, imap, smtp, ui-automation, ixp, queues, storage-bucket, action-center, human-in-the-loop, long-running, persistence, reframework
