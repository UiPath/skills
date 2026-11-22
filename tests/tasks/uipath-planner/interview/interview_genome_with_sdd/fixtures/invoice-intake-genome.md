<!-- UIPATH-AUTOMATION-GENOME: component | This file is a build specification for one UiPath automation project.
     To build it, invoke the uipath-genome skill: it asks the configuration questions,
     then invokes the skills referenced in Build With. Do NOT execute these steps directly, and do NOT
     start from a Build With skill. To change it, invoke the uipath-planner skill. -->

# Genome: Invoice Intake

> Reads supplier invoice mails from the accounts-payable mailbox, extracts each PDF invoice's vendor, number and total, checks them against the approved vendor list and queues approved invoices for ERP posting.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Build it with the **uipath-genome** skill, which hands each part to the skill listed in **Build With** below.

## Overview

Invoice Intake is the front door of accounts payable for supplier invoices that arrive by mail. An unattended run reads the unread mails of one folder of the AP mailbox, saves each mail's PDF invoice, reads the vendor name, the invoice number and the total from the PDF's text, and checks the invoice against the approved vendor list kept by Finance: the vendor must be on the list, the amount must be positive, within the vendor's credit limit and not above the auto-approval ceiling of 25000.

An approved invoice becomes one item of the ERP posting queue, which a separate posting process works. A rejected invoice is reported to the AP lead by mail with its reason; a mail with no attachment gets a reply asking the sender to resend it with the invoice attached. Invoices whose number or total cannot be read are logged and left for a person; any other failure moves the saved PDF to a failed folder and the run goes on with the next mail.

It serves the AP team, who would otherwise open, read and triage every invoice mail by hand. What starts a run is not recorded in the project *[Inferred: D6]*.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| AP mailbox (IMAP mail server) | Input source | Read over IMAP with SSL port 993; unread mails of one folder (Configuration Questions 1–3) |
| Mail server (SMTP) | Output target | Sends the attachment-missing reply and the rejection notice; server and sender not in the export (Configuration Question 5) |
| Approved vendor workbook | Input source | Excel workbook read as a file — Excel need not be installed; sheet `Vendors` with columns `VendorName` and `CreditLimit` (Configuration Question 7) |
| PDF invoices | Input source | Text read from the PDF without its layout; no OCR |
| Shared folders for invoices | Both | Inbox folder for saved PDFs, failed folder for PDFs whose processing failed (Configuration Question 8) |
| Intake log workbook | Output target | One row per handled invoice mail, when kept (Configuration Questions 10–11) |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| 1–10 | `uipath-rpa` | One unattended RPA process: IMAP and SMTP mail, workbook reads and appends, PDF text reading, file moves and an Orchestrator queue add are all RPA activities; no screen is driven, so no Object Repository. Target answer (unattended default, Recommended): an RPA process on Portable, since every activity the steps need exists cross-platform; the source is a Windows project. |

## Platform Dependencies

### Queues

| Queue | One item is | Item fields | Unique reference | Retries | Added by | Worked by |
|-------|-------------|-------------|------------------|---------|----------|-----------|
| ERP_InvoicePosting (Configuration Question 9) | one approved invoice | VendorName: Text, InvoiceNumber: Text, Amount: Number, PdfPath: Text | Reference is the invoice number; whether the queue enforces it unique is not in the export *[Inferred: D5]* | not in the export | step 8 | the ERP posting process, outside this genome; priority Normal |

### Credentials

| Asset | Account or persona | Signs in to | Used by |
|-------|--------------------|-------------|---------|
| Asset named by Configuration Question 4 | the AP mailbox account `ap-invoices@contoso.com` | the IMAP mail server | step 3 |
| Asset named by Configuration Question 5 | the sending account of the SMTP server | the SMTP mail server | steps 4, 8 |

## Interface

- **Inputs:** `MailboxFolder` (Text) — the IMAP folder of the AP mailbox to read, given when the run starts (Configuration Question 3).
- **Outputs:** none returned; the outputs are the side effects below.
- **Side effects:** saves PDF attachments to the inbox folder; adds one item per approved invoice to the ERP posting queue; mails the AP lead per rejected invoice; mails the sender of every mail with no attachment; moves the PDF of a failed invoice to the failed folder; appends a row per handled mail to the intake log when it is kept. Mails are left unread in the mailbox *[Inferred: D3]*.

## Configuration Questions

1. Which IMAP server and port serve the AP mailbox? (setting; default: `imap.contoso.com`, port 993, SSL)
2. Which mailbox account does the run read? (setting; default: `ap-invoices@contoso.com`)
3. Which mailbox folder does the run read — the start argument? (setting; default: not in the export — the start argument has no default and the project declares no input in its entry point)
4. Which credential asset holds the AP mailbox's sign-in? (setting; default: not in the export — the source sets no password)
5. Which SMTP server, port, sending address and credential asset send the run's mails? (setting; default: not in the export — the source sets none)
6. Who receives the rejection notice? (setting; default: `ap-lead@contoso.com`)
7. Where is the approved vendor workbook? (setting; default: `C:\Finance\Config\ApprovedVendors.xlsx`)
8. Which folders hold the saved invoices — the inbox folder and the failed folder? (setting; default: `C:\Finance\Invoices\Inbox` and `C:\Finance\Invoices\Failed`)
9. Which queue receives approved invoices? (setting; default: `ERP_InvoicePosting`)
10. Does the run keep writing its intake log workbook besides the job's log? (constant; default: the job's log in Orchestrator; the option keeps one row per handled mail in the workbook of Configuration Question 11)
11. Where is the intake log workbook, when kept? (setting; default: `C:\Finance\Invoices\IntakeLog.xlsx`, sheet `Log`)

## Open Decisions

1. When a mail carries several PDF attachments, which invoice does the run work? (business outcome; answered by: the process owner; builds now: every PDF is saved, the first saved PDF is worked as the mail's one invoice; instead: one invoice per saved PDF, each extracted, validated and routed on its own) — step 5, Save the PDF attachment
2. Which columns does a row of the intake log carry, when it is kept? (run behaviour; answered by: the process owner; recommended: one row per handled mail with the sender, vendor, invoice number, amount, approved or rejected, the rejection reason and the time handled; builds now: the same) — step 9, Record the result row
3. Should a handled mail be marked read or moved, so a later run does not take it again? (business outcome; answered by: the process owner; builds now: mails are left unread, as the source leaves them, so every run takes them again — a second queue item, rejection notice or reply per run; instead: mark each handled mail read; instead: move each handled mail to a processed folder) — step 3, Fetch unread invoice mails
4. A mail whose attachments hold no PDF: reply to the sender, or fail as the source does? (business outcome; answered by: the process owner; builds now: the attachment-missing reply, the intent the reply's own text states; instead: the source's behaviour, a system failure for that mail) — step 4, Check the mail carries an attachment
5. Does the ERP posting queue refuse a second item with the same invoice number? (business outcome; answered by: the ERP posting process owner; builds now: the queue as the target environment has it, uniqueness not set by this build; instead: unique reference enforced, so a duplicate invoice is refused) — Platform Dependencies, Queues
6. What starts a run, and how often? (reading; answered by: whoever knows the process; reading: started on demand with the mailbox folder, since the project holds no trigger and does not run in Orchestrator today) — step 1, Start the run
7. Once an invoice is queued, should a later failure for that mail still move its PDF to the failed folder? (business outcome; answered by: the process owner; builds now: the source's behaviour — the PDF is moved, and the queued item's PDF path no longer points to it; instead: leave a queued invoice's PDF in the inbox folder) — Error Handling, Steps 5–9
8. What do the approved vendor workbook's rows look like? (material; answered by: whoever holds the source; until answered: the build reads sheet `Vendors` with header columns `VendorName` and `CreditLimit`, as the source names them, and tests against a sample workbook it makes) — step 2, Read the approved vendor list

## Workflow

1. **Start the run** (input: mailbox folder; output: start log line): the run is started with the mailbox folder to read *[Inferred: D6]* and logs "Invoice intake started for folder {mailbox folder}" at Info level.
2. **Read the approved vendor list** (input: approved vendor workbook; output: vendor table): reads the whole sheet `Vendors` of the approved vendor workbook, first row as headers. Each row holds a vendor name (`VendorName`) and its credit limit (`CreditLimit`); the workbook itself is not in the export (D8). Read once per run.
3. **Fetch unread invoice mails** (input: mailbox folder; output: list of mails):
   a. Signs in to the AP mailbox over IMAP (SSL, port 993) and takes the unread mails of the mailbox folder, at most 50 per run.
   b. The mails are not marked read *[Inferred: D3]*.
   c. On failure the fetch is tried again, up to 3 attempts, 30 seconds apart (Error Handling).
4. **Check the mail carries an attachment** (input: one mail; output: continue, or reply sent), for each fetched mail in the order fetched:
   a. If the mail has no attachment at all: logs at Warn "No attachment on mail from {sender address} - skipping", sends the sender a mail with subject `Invoice not processed - attachment missing` and body `Your email did not contain a PDF invoice. Please resend with the invoice attached.`, and goes on with the next mail.
   b. **Source defect:** the test counts every attachment, so a mail whose attachments hold no PDF passes it and fails at step 6 with no file to read. Evident intent: "Your email did not contain a PDF invoice" — a mail with no PDF attachment gets the reply; the rebuild follows it (D4).
5. **Save the PDF attachment** (input: one mail; output: saved PDF path): saves the mail's attachments whose file name ends in `.pdf` into the inbox folder.
   **Source defect:** the saved files' paths are never captured, so no later step receives the PDF it works on, and the source as exported cannot run this step as designed *[Inferred: D1]*. Evident intent: the steps after it read, queue and move "the saved PDF" — the rebuild captures the saved PDF's path and works the first saved PDF as the mail's invoice *[Inferred: D1]*.
6. **Extract invoice fields** (input: saved PDF; output: vendor name, invoice number, amount):
   a. Reads the PDF's text without its layout.
   b. Vendor name: the first non-empty line of the text, trimmed of surrounding spaces.
   c. Invoice number: the first match anywhere in the text, ignoring case, of `Invoice` followed by optional spaces, then `No`, `Number` or `#`, then an optional `:` or `.`, optional spaces, and the number itself: one or more capital letters, digits or hyphens (case is ignored here too, so lower-case letters match). The number is the captured part only.
   d. Total: the first match anywhere in the text, ignoring case, of `Total`, optional spaces, an optional `Due`, an optional `:` or `.`, optional spaces, an optional `$` or `€`, optional spaces, and an amount — a digit, then digits and commas, an optional decimal point and up to two digits. `Total` also matches inside `Subtotal`, so a subtotal printed before the total is the one read.
   e. If no total is found, or the invoice number is empty: a business exception with the unreadable-invoice message, which names the PDF (step 6 rule; Error Handling).
   f. Otherwise the amount is the captured total with its commas removed, read as a decimal number with `.` as the decimal point.
7. **Validate the invoice** (input: vendor name, amount, vendor table; output: approved flag, rejection reason):
   a. The vendor is known when a row's `VendorName` equals the invoice's vendor name, both trimmed, ignoring case.
   b. Unknown vendor: rejected with the reason `Vendor not in approved vendor list`.
   c. Known vendor: its credit limit is the `CreditLimit` of the first matching row, read as a number.
   d. Rejected when the amount is zero or less, exceeds the vendor's credit limit, or exceeds 25000; the reason, checked in this order: amount zero or less → `Amount must be positive`; amount above 25000 → `Amount exceeds auto-approval ceiling of 25000`; otherwise `Amount exceeds vendor credit limit of {credit limit}`.
   e. Otherwise approved, with an empty reason.
8. **Route the invoice** (input: approved flag, invoice fields, PDF path; output: queue item or rejection notice):
   a. Approved: adds one item to the ERP posting queue, reference the invoice number, priority Normal, carrying VendorName, InvoiceNumber, Amount and PdfPath (the saved PDF's path).
   b. Rejected: mails the AP lead, subject `Invoice {invoice number} rejected`, body three lines `Vendor: {vendor name}`, `Amount: {amount}`, `Reason: {rejection reason}`.
9. **Record the result row** (input: the mail's result; output: one row appended to the intake log): appends the mail's result to sheet `Log` of the intake log workbook, when kept (Configuration Question 10).
   **Source defect:** the table appended is never filled, so no result is ever recorded, and the append fails each time *[Inferred: D2]* — which sends every mail that reached this step to the failed-mail handling after it was queued or rejected. Evident intent: the step's name, "log result row" — the rebuild appends one row per handled mail with the columns of D2 *[Inferred: D2]*.
10. **End the run** (input: the fetched mails; output: end log line): logs at Info "Invoice intake finished. Emails processed: {number of mails fetched}" — the count of mails fetched, whatever their outcome.

## Business Rules

### Step 4: Check the mail carries an attachment
- If the mail has no attachment, reply to the sender and skip it; otherwise go on to save its PDF. The rebuild tests for a PDF attachment (D4).

### Step 6: Extract invoice fields
- If the total is not found or the invoice number is empty, the invoice is a business exception: the run logs it and leaves the PDF in the inbox folder; no one is notified.
- The patterns of substeps 6c and 6d are case-insensitive and take the first match in the text.

### Step 7: Validate the invoice
- Vendor matching is exact after trimming, ignoring case; no partial or fuzzy match.
- If the amount is zero or less, or exceeds the vendor's credit limit, or exceeds the auto-approval ceiling of 25000, the invoice is rejected; otherwise it is approved. The reason names the first failed check in the order positive → ceiling → credit limit.

### Step 8: Route the invoice
- Route on the validation result: approved → ERP posting queue; rejected → notice to the AP lead. The rejected invoice is not queued and its PDF stays in the inbox folder.

## Error Handling

### Step 3: Fetch unread invoice mails
- Mailbox unreachable or sign-in refused: tried up to 3 attempts, 30 seconds apart; then the failure ends the run before any mail is worked.

### Step 6: Extract invoice fields
- Unreadable invoice number or total (business exception): logged at Warn as "Business rule failure for {invoice number}: {reason}"; the PDF stays in the inbox folder, the mail is not answered, and the run goes on with the next mail. **Source defect:** the invoice number in that line is the previous mail's, since this mail's number was never read. Evident intent: the log text names the failing invoice — the rebuild names this mail's invoice number, empty when it could not be read.

### Steps 5–9: Per mail
- Any other failure while working a mail — the PDF cannot be read, the credit limit is not a number, the queue or the mail server refuses, the append fails: logged at Error as "Failed to process mail from {sender address}: {error message}", the saved PDF is moved to the failed folder, replacing a file of the same name, and the run goes on with the next mail. The mail is not retried in this run.
- **Source defect:** the move runs whether or not the invoice was already queued, so a failure after step 8 leaves a queue item whose PDF path no longer exists. Evident intent: not stated *[Inferred: D7]*; the rebuild keeps the source's behaviour until the process owner rules (D7).
- A failure of the move itself — no PDF was saved — escapes the handler and ends the run *[Inferred: D4]*.

### Global
- Any failure outside the per-mail handling (steps 1–3, 10) ends the run; there is no global handler, no screenshot and no notification.
- Logging policy: the source logs at the start and end of the run and at every skip, rejection-less business exception and failure; the rebuild logs where the source logs, to the job's log in Orchestrator, and adds its own logs only at business milestones and decisions. The source writes no screenshots; none are added except the robot's screenshot on failure. The source's own run log is the intake log workbook — sheet `Log`, one row per handled mail, no retention set — kept only when Configuration Question 10 says so.
- Kept out of the logs: values of variables and arguments whose names start with `Private:` or contain `password`.

## Transactional Shape

**Flows:** Flow 1 — one invoice mail: step 3 → steps 4–9; Flow 2 — one approved invoice: step 8 → the ERP posting process, outside this genome; chains: steps 4–9 consume Flow 1 and produce Flow 2.

### Flow 1 — one invoice mail: fetch (step 3) → per-mail work (steps 4–9)

**Unit of work:** one unread invoice mail of the mailbox folder; reference the mail's message id *[Inferred: D3]* — the source keeps none; fields as in Interface and step 6; volume unknown, at most 50 mails per run; chosen because each mail is answered, rejected, queued or failed on its own and its failure does not stop the others.
**Alternative units of work:** one PDF attachment — fits when a mail can carry several invoices (D1).

**As-is** — how the project handles the units today:

| Aspect | As-is |
|---|---|
| Produced by | step 3: the unread mails of one folder, read once at the start of the run, up to 50; no guard against a mail being taken again by a later run (D3) |
| Consumed by | steps 4–9 of the same job, one robot, in the order fetched |
| Item store | in-memory list of mails; per-item state only in the logs, the inbox and failed folders, and the intake log |
| Coordination | none |
| Item kinds | one kind: a supplier invoice mail |
| Step groups | once per run: steps 1–3; per item: steps 4–9; at the end: step 10 |

| Outcome | When | Effect |
|---|---|---|
| Success | every per-item step completed and the invoice approved and queued | queue item added; PDF left in the inbox folder; result row recorded when kept |
| Business exception | Step 4 rule: no attachment; Step 6 rule: unreadable number or total; Step 7 rules: unknown vendor, amount not positive, above ceiling, above credit limit | not retried; step 4 replies to the sender, step 7 notifies the AP lead, step 6 only logs; run continues |
| System exception | every other failure — Steps 5–9 handler | not retried (0×); PDF moved to the failed folder; the run never stops on consecutive failures |

**Split options:**

| Unit of work | Option | Requires | Changes against as-is |
|---|---|---|---|
| one invoice mail | A | the mails taken again by a later run kept harmless (D3) | none: one job fetches and works its mails, as today |
| one invoice mail | B | a queue of invoice mails, one item per mail with its message id as reference; a producer that reads the mailbox and a consumer that works the items, each with its trigger | two processes; each mail visible and retried on its own in Orchestrator |
| one invoice mail | C | a queue of invoice mails, and a once-guard: the message id as a unique reference the queue refuses twice | one process that first queues the folder's unread mails, then works them; several runners possible |
| one PDF attachment | A | mails with several PDFs worked one invoice per PDF (D1) | each PDF extracted, validated and routed on its own inside the mail's run |
| one PDF attachment | B | a queue of PDFs, reference derived from the mail's message id and the file name; the attachment-missing reply stays per mail in the producer | two processes; retries per invoice |
| one PDF attachment | C | as B, in one process, the unique reference as once-guard | one process, producer phase then consumer phase |

**Evidence:** one robot, one job per run; trigger unknown (D6); the project does not run in Orchestrator today; mails are not marked read, so they are found again by every run (D3); every per-mail step uses the same applications.
**Configuration:** settings — questions 1–9, 11; constants — question 10; assets — the credential assets of Configuration Questions 4 and 5, read where their secret is used.
**Traceability:** per mail only in the job's log (start, skip, business exception and failure lines), the folder the PDF ends in, and the intake log row when kept; no screenshot; the end line counts the mails fetched, not the outcomes.

### Flow 2 — one approved invoice: step 8 → the ERP posting process

**Unit of work:** one approved invoice; reference the invoice number; fields VendorName, InvoiceNumber, Amount, PdfPath (Platform Dependencies, Queues); one item per approved mail.
**Alternative units of work:** none.

| Aspect | As-is |
|---|---|
| Produced by | step 8a, per approved invoice of Flow 1; the item is added before the result row is recorded, and a failure after it still moves the PDF (D7); a mail taken again by a later run adds the item again unless the queue refuses its reference (D3, D5) |
| Item store | Orchestrator queue ERP_InvoicePosting |

Split options: none — the consumer is outside this genome: the ERP posting process that works the ERP posting queue.
**Traceability:** the item carries the invoice number as its reference and the saved PDF's path.

## Acceptance Criteria

1. Given the run starts with folder `Invoices`, the job's log opens with "Invoice intake started for folder Invoices".
2. Given an approved vendor workbook whose sheet `Vendors` lists `Acme Ltd` with credit limit 10000, the run validates against that row; a missing workbook ends the run before any mail is fetched.
3. Given 60 unread mails in the folder, the run works at most 50 of them.
4. Given the mailbox is unreachable for the first attempt and reachable on the second, the run fetches the mails after a 30-second wait; unreachable for 3 attempts, the run ends with no mail worked.
5. Given a mail with no attachment from `supplier@example.com`, the sender receives a mail with subject `Invoice not processed - attachment missing` and the body `Your email did not contain a PDF invoice. Please resend with the invoice attached.`, a Warn line "No attachment on mail from supplier@example.com - skipping" is logged, and nothing is queued.
6. Given a mail whose only attachment is a Word document, the sender receives the attachment-missing reply (D4).
7. Given a mail with a PDF and a JPG attachment, only the PDF is saved to the inbox folder.
8. Given a PDF whose first non-empty line is `  Acme Ltd  ` and whose text holds `Invoice No: INV-1001` and `Total Due: $1,234.50`, the vendor is `Acme Ltd`, the invoice number `INV-1001` and the amount 1234.5.
9. Given a PDF with `invoice # A-7` and `TOTAL €980`, the invoice number is `A-7` and the amount 980.
10. Given a PDF with `Subtotal: 900.00` printed before `Total: 1,071.00`, the amount read is 900.
11. Given a PDF with no total, the run logs a Warn business-rule failure that names the PDF, queues nothing, notifies no one, leaves the PDF in the inbox folder and goes on with the next mail.
12. Given vendor `ACME LTD ` on the invoice and `Acme Ltd` on the list, the vendor is known.
13. Given a vendor not on the list, the AP lead receives `Invoice {number} rejected` with `Reason: Vendor not in approved vendor list`, and nothing is queued.
14. Given a known vendor with credit limit 10000 and amounts 0, 30000, 12000 and 9000, the results are rejected `Amount must be positive`, rejected `Amount exceeds auto-approval ceiling of 25000`, rejected `Amount exceeds vendor credit limit of 10000`, and approved.
15. Given an approved invoice `INV-1001` of `Acme Ltd` for 1234.5, one ERP posting queue item is added with reference `INV-1001`, priority Normal, and fields VendorName `Acme Ltd`, InvoiceNumber `INV-1001`, Amount 1234.5 and PdfPath the saved PDF's path.
16. Given the rejection notice for invoice `INV-2002` of `Beta GmbH` for 30000, its body reads `Vendor: Beta GmbH`, `Amount: 30000`, `Reason: Amount exceeds auto-approval ceiling of 25000` on three lines.
17. When the queue refuses the item, an Error line "Failed to process mail from {sender}: {message}" is logged, the PDF is moved to the failed folder, replacing a file of the same name, and the run goes on with the next mail.
18. Given a credit limit cell that is not a number, the mail ends as a failure: the PDF is moved to the failed folder and the next mail is worked.
19. When the intake log is kept, every handled mail adds one row with the columns of D2, and no handled mail fails because of the append.
20. Given 5 mails fetched of which 2 fail, the job's log ends with "Invoice intake finished. Emails processed: 5".
21. Given an empty folder, the run logs start and end with `Emails processed: 0` and does nothing else.
22. Given a run that leaves its mails unread, a second run takes the same mails again (D3).

## Complexity

medium

## Tags

finance, accounts-payable, invoice-intake, mail, IMAP, SMTP, PDF, Excel, queues, unattended

## Source Map

| Row | Source artifact | Notes |
|-----|-----------------|-------|
| Source framework | UiPath Studio 25.10.0.0; project schema 4.0; Windows target framework; VisualBasic expressions | Refactor source |
| Source export | `InvoiceIntake` | `projectId` 3b1f7c2e-9d4a-4e6b-8f1a-2c5d7e9a1b3c, `projectVersion` 1.4.0; not in a git repository; read 2026-11-22 |
| Inventory counts | 3 XAML workflows, 0 coded workflows, 0 test cases, 0 data variations, 0 Object Repository elements, 0 project settings files | One entry point (`Main.xaml`); all 3 workflows reached; no captures |
| Deployed state | not read | The request states the project does not run in Orchestrator; the package holds no bindings. Queue settings and trigger unknown (D5, D6) |
| Runtime | not read | No job history |
| Requested change | — (documentation request) | `Target: InvoiceIntake → RPA process on Portable` (unattended default, Recommended answer); Retire not asked (no deployed-state window); Fold not applicable (one component) |
| Related resources | none | The request states there are no other resources |
| Not covered | none | — |
| Unused | none | Package `UiPath.UIAutomation.Activities` 25.10.2 is a dependency no workflow uses |
| Interface mismatch | `project.json` `entryPoints[0].input` | Empty, while `Main.xaml` declares `in_MailboxFolder` (In, String); the manifest was not refreshed |
| Finding F1 — source defect (D4) | `Main.xaml` line 33 | `mail.Attachments.Count = 0` tests every attachment; the reply's body (line 37) states the PDF intent |
| Finding F2 — source defect (D1) | `Main.xaml` line 42 | Save Attachments binds its output `Attachments` to `{attachmentPath}`, an array literal, so `attachmentPath` is never written; read at lines 45, 67, 97. Whether Studio rejects the binding at validation is not verified (nothing built) |
| Finding F3 — source defect (D2) | `Main.xaml` lines 10, 75 | `dt_Results` declared, never assigned or filled, appended to `C:\Finance\Invoices\IntakeLog.xlsx` sheet `Log`; that the append of an unset table fails is inferred |
| Finding F4 — source defect | `Main.xaml` line 87; `ExtractInvoiceFields.xaml` line 29 | Business-rule catch logs `invoiceNumber`, a run-level variable the failed invoke never wrote, so it holds the previous mail's number. Intent stated by the log text; the rebuild follows it. Unreadable-invoice message in full: `"Could not read invoice number or total from " & in_PdfPath` |
| Finding F5 — source defect (D7) | `Main.xaml` lines 62–75, 97 | Generic catch moves `attachmentPath` to `C:\Finance\Invoices\Failed` with overwrite, whatever was done before; the queue item added at line 62 keeps the old path |
| Finding F6 — source fact (D3) | `Main.xaml` line 22 | Get IMAP Mail Messages sets no `MarkAsRead`; the activity's default (cleared) leaves mails unread. `Top` 50, `OnlyUnreadMessages` True, server `imap.contoso.com`, port 993, account `ap-invoices@contoso.com`, no password set |
| Finding F7 — source fact | `Main.xaml` lines 37, 72 | Send SMTP Mail activities set no server, port, sender or credential (Configuration Question 5) |
| Finding F8 — source rule | `ExtractInvoiceFields.xaml` line 25 | Total pattern `Total\s*(?:Due)?[:.]?\s*[$€]?\s*([0-9][0-9,]*\.?[0-9]{0,2})`, ignore case, first match — matches inside `Subtotal`; comma-decimal amounts (`1.234,56`) read wrongly. Invoice-number pattern (line 21): `Invoice\s*(?:No|Number|#)[:.]?\s*([A-Z0-9-]+)`, ignore case |
| Verification | all three workflows | Both passes made: each finding re-read in the full XAML with both directions of its argument bindings and the invoked workflow; a UiPath project is its own rendering, so rendering and source match |

### Steps

| Step | Source objects | Data sets | Captures | Notes |
|------|----------------|-----------|----------|-------|
| 1 | `Main.xaml` | none | 0 | Line 18, "Log start"; argument `in_MailboxFolder` |
| 2 | `Main.xaml` | none | 0 | Line 19, Read Range `C:\Finance\Config\ApprovedVendors.xlsx`, sheet `Vendors`, whole sheet, headers on |
| 3 | `Main.xaml` | none | 0 | Lines 20–24, Retry Scope 3, interval 30 s, around Get IMAP Mail Messages |
| 4 | `Main.xaml` | none | 0 | Lines 33–39; finding F1 |
| 5 | `Main.xaml` | none | 0 | Line 42, Save Attachments to `C:\Finance\Invoices\Inbox`, filter `*.pdf`; finding F2 |
| 6 | `ExtractInvoiceFields.xaml` | none | 0 | Called from `Main.xaml` line 43; Read PDF Text, formatting off; findings F4, F8 |
| 7 | `ValidateInvoice.xaml` | none | 0 | Called from `Main.xaml` line 51; ceiling 25000 at line 32 |
| 8 | `Main.xaml` | none | 0 | Lines 60–74: Add Queue Item `ERP_InvoicePosting`; rejection mail to `ap-lead@contoso.com` |
| 9 | `Main.xaml` | none | 0 | Line 75, Append Range `C:\Finance\Invoices\IntakeLog.xlsx`, sheet `Log`; finding F3 |
| 10 | `Main.xaml` | none | 0 | Line 105, "Log end" |
