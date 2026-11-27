<!-- UIPATH-AUTOMATION-GENOME: component | This file is a build specification for one UiPath automation project.
     To build it, invoke the uipath-genome skill: it asks the configuration questions,
     then invokes the skills referenced in Build With. Do NOT execute these steps directly, and do NOT
     start from a Build With skill. To change it, invoke the uipath-planner skill. -->

# Genome: Supplier Invoice Entry and Approval

> Reads each supplier invoice mailed to the accounts-payable mailbox, enters it in SAP S/4HANA, and has the finance approver group approve it before posting when its amount is over the approval limit.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Build it with the **uipath-genome** skill, which hands each part to the skill listed in **Build With** below.

## Overview

Suppliers mail their invoices, as PDF or scanned attachments, to the shared accounts-payable mailbox. Today an AP clerk opens each mail, keys the invoice into SAP S/4HANA and, when the amount is over the company's approval limit, chases a finance approver before the invoice may be posted. This automation takes that work over: every mail that arrives in the AP mailbox starts it, each invoice document attached to the mail is read, checked against SAP (supplier, duplicates, purchase order) and entered.

An invoice at or under the approval limit is posted in SAP straight away. An invoice over the limit is parked in SAP and an approval task is put to the finance approver group; once approved, the parked invoice is posted; once rejected, it stays parked and the AP clerks are told why, so they can settle it with the supplier. The group is reminded after two working days and the AP clerks are told after five, while the task stays open.

The automation serves the accounts-payable team (fewer keyed invoices, no approval chasing) and finance (no over-limit invoice is posted without an approval on record). Under 50 invoices arrive a day, purchase-order based and non-PO invoices mixed. Every invoice the automation cannot settle on its own — unreadable, unknown supplier, duplicate, amounts that do not add up, rejected — is handed to the AP clerks with the reason and the document.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| Microsoft Outlook 365 — the AP shared mailbox | Input source; output target for notifications | Mail with invoice attachments is read from the inbox folder; handled mail is moved to folders; notifications are sent from this mailbox. Reached through Integration Service, no UI. Mail provider: CQ13 |
| SAP S/4HANA | Both | Finance / Materials Management, supplier invoices for the company code(s) of CQ4. Read: supplier master, purchase orders, existing supplier invoices, exchange rates. Write: park, post and attach the document to supplier invoices. Reached through the SAP OData connector, no UI *[Inferred: D1]* |
| UiPath Action Center | Both | The finance approver group decides over-limit invoices in an approval task |
| UiPath Document Understanding | Input source | Classifies attached documents and extracts invoice fields with the pre-trained invoice model |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| 1–2 Mail trigger and intake | `uipath-rpa` | Integration Service Outlook 365 activities and the mail event trigger inside the one RPA process that works the invoice end to end; a Flow would add a coordinator the single process does not need |
| 3–4 Classify and extract | `uipath-rpa` | Document Understanding classification and extraction run as steps of the process that uses them (pre-trained invoice model, no model of its own to train, so no `uipath-ixp` project) |
| 5–8 Supplier, duplicate, amount and PO / coding checks | `uipath-rpa` | Deterministic checks over SAP reads made through the SAP connection; one consumer, so no separate function or API workflow |
| 9 Compare with the approval limit | `uipath-rpa` | One threshold, kept as a configuration constant; no decision table the business maintains apart |
| 10 Enter in SAP S/4HANA | `uipath-rpa` | SAP connector calls to park or post and attach the document |
| 11–12 Approval and decision | `uipath-rpa` | One approval inside one process is a long-running RPA workflow with an Action Center task, not a Maestro coordinator |
| 13 Report the outcome | `uipath-rpa` | Notification mail through the same Outlook 365 connection |

## Platform Dependencies

### Connections

| Connection | Connector | Signs in as | Used by |
|------------|-----------|-------------|---------|
| AP mailbox | Microsoft Outlook 365 | the AP shared mailbox's service account, with access to the mailbox of CQ1 | steps 1, 2, 13 |
| SAP S/4HANA | SAP OData *[Inferred: D1]* | a technical SAP user allowed to read suppliers, purchase orders and supplier invoices and to park, post and attach supplier invoices in the company code(s) of CQ4 | steps 5, 6, 8, 9, 10, 12 |

### Data Fabric entities

| Entity | Fields | Written by | Read by |
|--------|--------|------------|---------|
| SupplierInvoiceCoding *[Inferred: D3]* | SupplierNumber: Text, CompanyCode: Text, GLAccount: Text, CostCenter: Text, TaxCode: Text, Active: Boolean | the AP team (maintained by hand) | step 8 |

### Triggers

| Trigger | Starts | Kind | When | Runners |
|---------|--------|------|------|---------|
| NewSupplierInvoiceMail | this process | Event | a new mail arrives in the inbox folder of the AP mailbox (CQ1) | 1 |

### Action Center

| Resource | Used by | Purpose |
|----------|---------|---------|
| Supplier invoice approval task, assigned to the finance approver group (CQ5) | steps 11, 12 | The approver approves or rejects an over-limit invoice; a rejection carries a reason |

### Document Understanding

| Resource | Used by | Purpose |
|----------|---------|---------|
| Pre-trained invoice extraction model and a document classifier | steps 3, 4 | Tell invoices from other attachments and extract the invoice fields with a confidence per field |

## Interface

- **Inputs:** the mail that fires the trigger — sender, subject, received time, message id and attachments — read from the AP mailbox; no start arguments.
- **Outputs:** per invoice, the SAP supplier invoice (company code, fiscal year, document number) in status posted or parked; the approval decision with approver, time and reason; the outcome and its reason in the job's log.
- **Side effects:** supplier invoices parked and posted in SAP S/4HANA with the invoice document attached; approval tasks created in Action Center; handled mail moved to the processed or needs-review folder; notification mails to the AP clerks and reminder mails to the finance approver group.

## Configuration Questions

1. Which mailbox and which of its folders receive supplier invoices? (setting; default: none)
2. Which folders take handled mail and mail that needs a person? (setting; default: subfolders "Processed" and "Needs review" of the folder in CQ1)
3. What is the approval limit, and in which currency is it stated? (constant; default: none — required: every invoice is compared with it)
4. Which SAP company code or codes does the automation enter invoices for? (constant; default: none)
5. Which Action Center group is the finance approver group? (setting; default: none)
6. Which mail address reaches the AP clerks for notifications? (setting; default: none)
7. After how many working days is the approver group reminded, and after how many are the AP clerks told? (constant; default: reminder after 2 working days; AP clerks told after 5, the task staying open)
8. Which working-day calendar counts the days of CQ7? (setting; default: none)
9. What is the lowest extraction confidence a mandatory field may have? (constant; default: 80%)
10. What difference between the stated and the computed amounts is tolerated? (constant; default: 0.01 in the invoice currency)
11. How often is an invoice retried after a system failure, and after how many consecutive failures does the run stop? (constant; default: retried 2×; stop after 3 consecutive)
12. Who is told when an invoice fails after its retries? (setting; default: the AP clerks of CQ6)
13. Which mail provider hosts the AP mailbox? (constant; default: Microsoft Outlook 365)
14. Which attachment file types can hold an invoice? (constant; default: PDF, TIFF, JPG, PNG)

## Open Decisions

1. How does the automation reach SAP S/4HANA — the SAP OData connector, the SAP BAPI connector, or the Fiori / SAP GUI screens? (reading; answered by: the system's owner; reading: the SAP OData connector with the standard supplier invoice, supplier, purchase order and attachment services, because an API is preferred over UI and the connector is in the Integration Service catalog; whether the S/4HANA system is reachable from the cloud, or needs a relay, and whether those services are active is not known) — Target Applications; Connections; steps 5, 6, 8, 9, 10, 12
2. When a mandatory field is missing or below the confidence of CQ9, what happens to the invoice? (business outcome; answered by: the process owner; builds now: the invoice is not entered and goes to the AP clerks with the fields at fault and the document; instead: an Action Center validation task lets an AP clerk correct the fields, and the invoice then continues at step 5) — step 4, Extract the invoice fields
3. Where does a non-PO invoice take its G/L account, cost centre and tax code? (business outcome; answered by: the process owner; builds now: from a coding table the AP team keeps per supplier and company code, a supplier missing from it going to the AP clerks; instead: from the supplier's defaults in SAP; instead: an AP clerk codes each non-PO invoice in an Action Center task) — step 8, Check the purchase order or the coding
4. Which amount is compared with the approval limit, and in which currency? (business outcome; answered by: the process owner; builds now: the gross amount, converted to the limit's currency at SAP's current exchange rate when the invoice is in another currency; instead: the net amount; instead: the amount in the invoice currency, unconverted) — step 9, Compare with the approval limit
5. Does an invoice exactly at the limit need approval? (business outcome; answered by: the process owner; builds now: no — only an amount that exceeds the limit needs approval; instead: yes, at or over the limit) — step 9, Compare with the approval limit
6. What happens to a supplier credit note? (business outcome; answered by: the process owner; builds now: it is not entered and goes to the AP clerks; instead: it is entered as a credit memo by the same rules, a credit never needing approval) — step 3, Classify each document
7. Is the invoice document attached to the SAP supplier invoice? (business outcome; answered by: the process owner; builds now: yes, the original file is attached to the parked or posted document; instead: no attachment, the document kept only in the mailbox) — step 10, Enter the invoice in SAP S/4HANA
8. What happens to attachments that are not invoices (terms and conditions, delivery notes, statements)? (business outcome; answered by: the process owner; builds now: they are left in the mail and not worked, the mail's invoices still being worked; instead: the AP clerks are told of each one) — step 3, Classify each document
9. When a PO invoice differs from its purchase order or goods receipt beyond SAP's own tolerances, what happens? (business outcome; answered by: the process owner; builds now: the invoice is entered and SAP's invoice verification sets its payment block, the AP clerks being told of the block; instead: the invoice is not entered and goes to the AP clerks) — step 10, Enter the invoice in SAP S/4HANA
10. Once the AP clerks settle a rejected invoice, does it come back for approval? (business outcome; answered by: the process owner; builds now: no — the automation's work on it ends at the rejection, and the AP clerks finish it in SAP; instead: an AP clerk resubmits it, which starts a new approval task) — step 12, Act on the decision
11. Which posting date does the SAP document carry? (business outcome; answered by: the process owner; builds now: the day the document is posted, the invoice date as document date; instead: the invoice date as posting date) — step 10, Enter the invoice in SAP S/4HANA
12. How is the supplier found in SAP? (reading; answered by: whoever knows the process; reading: by the tax (VAT) number on the invoice, then by the bank account (IBAN), then by the exact supplier name, because those are the identifiers an invoice reliably carries and a name alone is ambiguous) — step 5, Identify the supplier

## Workflow

1. **Trigger** (input: a new mail in the AP mailbox; output: the mail): a mail arriving in the inbox folder of the AP mailbox (CQ1) starts the work for that mail.
2. **Take the mail's invoice documents** (input: the mail; output: one invoice item per document, each with reference message id plus attachment file name):
   a. Take every attachment whose file type is one of CQ14; leave out images embedded in the mail body (logos, signatures).
   b. If the mail has no such attachment, send the AP clerks (CQ6) the mail as an attachment with the reason "no invoice document attached", move the mail to the needs-review folder (CQ2) and end the work for this mail.
   c. Make each attachment one invoice item, keeping the sender, the subject, the received time and the file itself with it.
   d. Move the mail to the processed folder (CQ2) once its items exist.
3. **Classify each document** (input: one invoice item's file; output: document type invoice, credit note or other):
   a. Classify the document as invoice, credit note or other.
   b. Route on the type: invoice → step 4; credit note → not entered, sent to the AP clerks with the reason "credit note received" *[Inferred: D6]*; other → not worked, left in the mail *[Inferred: D8]*.
4. **Extract the invoice fields** (input: the invoice file; output: the extracted invoice record with a confidence per field):
   a. Extract the supplier name, the supplier's tax (VAT) number, address and bank account (IBAN), the invoice number, the invoice date, the due date, the purchase order number(s), the currency, the net amount, the tax amount and rate, the gross amount, and each line item's description, quantity, unit price, line amount and purchase order item.
   b. The mandatory fields are the supplier name, the invoice number, the invoice date, the currency, the net amount, the tax amount and the gross amount; the purchase order number is mandatory when the invoice states one.
   c. If a mandatory field is missing or its confidence is below CQ9, the invoice goes to the AP clerks with the fields at fault and the document *[Inferred: D2]*.
5. **Identify the supplier** (input: the extracted supplier identifiers; output: the SAP supplier number):
   a. Look the supplier up in SAP among suppliers that are not blocked for posting in the company code(s) of CQ4: first by the tax (VAT) number, then by the bank account (IBAN), then by the exact supplier name *[Inferred: D12]*.
   b. Exactly one match → the supplier number; none or more than one → the invoice goes to the AP clerks with the reason "supplier not found" or "supplier ambiguous: <the supplier numbers found>".
6. **Check for duplicates** (input: supplier number, invoice number, invoice date, gross amount; output: new or duplicate):
   a. Read SAP's supplier invoices — parked and posted, not reversed — of that supplier whose supplier invoice reference equals the invoice number, in any fiscal year.
   b. If one is found and its header text carries this item's reference, it is this item's own earlier attempt: continue from it — a parked one at step 11, a posted one at step 13.
   c. If one is found otherwise, the invoice is a duplicate: it goes to the AP clerks with the reason "duplicate of SAP document <number>/<fiscal year>".
7. **Check the amounts** (input: the extracted invoice record; output: consistent or the differences):
   a. The net amount plus the tax amount equals the gross amount within CQ10.
   b. When line items were extracted, their line amounts add up to the net amount within CQ10.
   c. Any difference beyond CQ10 → the invoice goes to the AP clerks with each field, the stated value and the computed value.
8. **Check the purchase order or the coding** (input: invoice record and supplier number; output: the SAP lines to enter — PO items or G/L lines):
   a. Route on the purchase order number: present → PO invoice (substeps b–d); absent → non-PO invoice (substeps e–f).
   b. Read the purchase order from SAP; it must exist, belong to the supplier and to a company code of CQ4, and not be closed for invoicing; otherwise the invoice goes to the AP clerks with the reason "purchase order <number> not found for supplier <number>".
   c. Match each invoice line to a purchase order item: by the item number when the line states one; otherwise by the material or description equal to the item's text, a line matching no item or several going to the AP clerks with the reason "line <n> matches no single PO item".
   d. Each matched line becomes a PO line with its quantity and amount; price and quantity differences are left to SAP's own invoice verification *[Inferred: D9]*.
   e. Read the supplier's row of the coding table for the company code: the G/L account, the cost centre and the tax code *[Inferred: D3]*.
   f. No active row → the invoice goes to the AP clerks with the reason "no coding for supplier <number>"; otherwise one G/L line carries the net amount with that account, cost centre and tax code.
9. **Compare with the approval limit** (input: gross amount and currency; output: under or over the limit):
   a. Take the gross amount; when its currency differs from the limit's (CQ3), convert it at SAP's current exchange rate for the company code *[Inferred: D4]*.
   b. If the amount exceeds the limit, the invoice is over the limit; otherwise it is under the limit — an amount equal to the limit included *[Inferred: D5]*.
10. **Enter the invoice in SAP S/4HANA** (input: invoice record, supplier, lines, limit result; output: company code, fiscal year, document number and status):
    a. Fill the supplier invoice: company code, supplier, supplier invoice reference = invoice number, document date = invoice date, posting date = the day of entry *[Inferred: D11]*, currency, gross amount, tax amount and code, the PO lines or the G/L line from step 8, and a header text carrying this item's reference.
    b. Under the limit → post the supplier invoice; over the limit → park it.
    c. Attach the invoice file to the document *[Inferred: D7]*.
    d. Confirm SAP returned a document number and the status posted or parked; a posted PO invoice that SAP blocked for payment is reported to the AP clerks with SAP's block reason *[Inferred: D9]*.
    e. Under the limit → step 13; over the limit → step 11.
11. **Request approval** (input: the parked document and the invoice record; output: the decision — approved, or rejected with a reason — with approver and time):
    a. Create an approval task for the finance approver group (CQ5) titled "Approve supplier invoice <invoice number> — <supplier name>", showing the supplier, the invoice number and date, the gross amount and currency, the amount compared with the limit and the limit, the purchase order or the cost centre, the SAP parked document number, and the invoice file.
    b. The approver approves or rejects; a rejection needs a reason.
    c. Wait for the decision. When the task is still open after the first period of CQ7, send the group a reminder; after the second period, tell the AP clerks that the invoice awaits approval, with its details — the task stays open and the wait goes on.
12. **Act on the decision** (input: the decision and the parked document; output: posted document, or rejected invoice handed to the AP clerks):
    a. Read the document again in SAP; if it is no longer parked (posted or deleted by a person meanwhile), the invoice goes to the AP clerks with the reason "parked document changed while awaiting approval: <status>".
    b. Approved → post the parked document and confirm its status is posted.
    c. Rejected → leave the document parked and send the AP clerks the supplier, the invoice number, the parked document number, the approver, the reason and the invoice file *[Inferred: D10]*.
13. **Report the outcome** (input: the item's outcome; output: the outcome recorded and, when a person must act, a notification):
    a. Record per invoice: the item reference, the supplier invoice number, the SAP document number and status, the approval decision when there was one, and the outcome with its reason.
    b. Every invoice handed to the AP clerks by a step above reaches them as one mail with the reason, the invoice details known so far and the invoice file.

## Business Rules

### Step 2: Take the mail's invoice documents
- Only attachments of the types of CQ14 are documents; images embedded in the mail body are never documents.
- A mail without a document goes to the AP clerks and to the needs-review folder; it is not an invoice item.

### Step 3: Classify each document
- Only documents classified as invoices are entered; credit notes go to the AP clerks *[Inferred: D6]*; other documents are not worked *[Inferred: D8]*.

### Step 4: Extract the invoice fields
- If a mandatory field is missing or below the confidence of CQ9, the invoice is not entered *[Inferred: D2]*.

### Step 5: Identify the supplier
- If no supplier, or more than one, matches, the invoice is not entered.

### Step 6: Check for duplicates
- If SAP holds a parked or posted, not reversed, supplier invoice of the same supplier with the same supplier invoice reference, the invoice is a duplicate and is not entered — unless that document is this item's own earlier attempt.

### Step 7: Check the amounts
- If net plus tax differs from gross, or the line amounts differ from net, by more than CQ10, the invoice is not entered.

### Step 8: Check the purchase order or the coding
- If the invoice states a purchase order, the order must exist, belong to the supplier and a company code of CQ4, and be open for invoicing.
- If the invoice states no purchase order, its coding comes from the supplier's coding row *[Inferred: D3]*; no row, no entry.

### Step 9: Compare with the approval limit
- If the gross amount, in the limit's currency, exceeds the approval limit (CQ3), the invoice is over the limit and needs approval before posting; otherwise it is posted without approval *[Inferred: D4]* *[Inferred: D5]*.

### Step 10: Enter the invoice in SAP S/4HANA
- An invoice under the limit is posted; an invoice over the limit is parked and never posted without an approval.

### Step 12: Act on the decision
- Only an approved task posts a parked document; a rejected one stays parked, and the automation does not touch it again *[Inferred: D10]*.

### General
- Every invoice the automation does not enter, or enters and cannot finish, reaches the AP clerks (CQ6) with its reason and its file; none is dropped silently.
- An over-limit invoice is never posted before an approval is recorded on its task.

## Error Handling

### Step 2: Take the mail's invoice documents
- The mail cannot be read or moved: system exception; the mail stays in the inbox folder, so a later attempt finds it again.

### Step 3: Classify each document; Step 4: Extract the invoice fields
- The document cannot be read (encrypted, corrupt, password-protected): business exception, sent to the AP clerks with the reason "document cannot be read".

### Step 10: Enter the invoice in SAP S/4HANA
- SAP refuses the document with a business message (posting period closed, supplier blocked, tax code invalid): business exception, sent to the AP clerks with SAP's message; nothing is retried.
- SAP does not answer or times out: system exception; before the retry enters the document again, step 6 finds this item's own earlier attempt by its header text and continues from it, so no invoice is entered twice.

### Step 11: Request approval
- The task cannot be created: system exception; the document stays parked and the retry creates the task.

### Step 12: Act on the decision
- Posting the approved document fails with a business message from SAP: business exception, sent to the AP clerks with SAP's message; the document stays parked and the approval stays on record.

### Global
- Every other failure is a system exception: the invoice is retried as CQ11 states; after the last retry it is recorded as failed with the reason, and the recipients of CQ12 are told with the item reference, the step and the error message.
- The run stops after the number of consecutive system exceptions of CQ11.

## Transactional Shape

**Flows:** Flow 1 — supplier invoice: steps 1–2 → steps 3–13.

### Flow 1 — supplier invoice: steps 1–2 → steps 3–13

**Unit of work:** one invoice document attached to a mail; reference the mail's message id plus the attachment file name (the business key — supplier and supplier invoice number — is known only after step 5 and is checked by step 6); fields as in Interface and step 2; under 50 a day, arriving throughout the working day; chosen because each invoice is read, checked, entered, approved and reported on its own, the reference exists when the item is made, and a retry redoes one invoice.
**Alternative units of work:** one mail with all its invoice documents — fits when suppliers send one invoice per mail, or when the invoices of one mail must be settled together.

**As-is** — how the process handles the units as described:

| Aspect | As-is |
|---|---|
| Produced by | steps 1–2, for every mail that arrives in the AP mailbox; one source; no guard against a mail taken twice beyond moving it to the processed folder |
| Consumed by | steps 3–13; the description names no robot count; an over-limit invoice waits at step 11 for the approver group, up to days |
| Item store | none named — the description implies each mail's invoices are worked as the mail arrives; per-item state is the SAP document number and status, and the approval task's decision |
| Coordination | none |
| Item kinds | one kind, supplier invoice, with paths routed inside the consumer: PO or non-PO (step 8), under or over the limit (steps 9–12) |
| Step groups | once per run: none — every step works one mail or one invoice; per item: steps 3–13; at the end: none |

| Outcome | When | Effect |
|---|---|---|
| Success | every per-item step completed — posted under the limit, or approved and posted | item recorded as done with the SAP document number and status |
| Business exception | Step 3 rules: credit note; Step 4 rules: mandatory field missing or below confidence, document cannot be read; Step 5 rules: supplier not found or ambiguous; Step 6 rules: duplicate; Step 7 rules: amounts differ; Step 8 rules: purchase order not valid, no coding; Step 10 handlers: SAP refuses the document; Step 12 rules: rejected, parked document changed; Step 12 handlers: SAP refuses the posting | no retry; item recorded with the reason and sent to the AP clerks; run continues |
| System exception | every other failure — Step 2, Step 10, Step 11 and Global handlers | connections opened again, item retried as CQ11 states (default 2×), then recorded as failed with the reason; run stops after CQ11's consecutive count (default 3) |

**Split options:**

| Unit of work | Option | Requires | Changes against as-is |
|---|---|---|---|
| one invoice | A | one job per mail works that mail's invoices in turn, suspended while an approval is open; several jobs suspended at once | no queue; per-invoice state visible only in the job's log, SAP and the task; a system retry of the job redoes the mail's unfinished invoices; a second invoice in the same mail waits behind the first one's approval |
| one invoice | B | an intake process on the mail trigger adds one queue item per invoice, unique reference message id plus attachment file name; a worker process on a queue trigger works each item and is suspended while its approval is open | two processes and two triggers; per-invoice status, retries and reasons visible in the queue; each invoice of a mail waits for its own approval only |
| one invoice | C | one process on the mail trigger adds the mail's invoices to a queue, the queue refusing a reference added twice as its once-guard, then works items from it | one process, one trigger, and the queue between its roles; per-invoice status visible in the queue; any job may work any mail's invoices |
| one mail | A | one job per mail works its invoices together; a mail is settled when all its invoices are | no queue; one mail's invoices wait for one another's approvals; a system retry redoes the mail's unfinished invoices |
| one mail | B | an intake process adds one queue item per mail; a worker takes a mail and works all its invoices | two processes; status per mail, not per invoice, in the queue; per-invoice outcomes recorded inside the mail's item |
| one mail | C | one process adds the mail to a queue, refusing a message id added twice, then works it | one process; status per mail in the queue |

**Evidence:** under 50 invoices a day from one mailbox, arriving throughout the day; one item kind; an over-limit invoice waits days for a person (reminder after 2 working days, AP clerks told after 5); every system is reached through Integration Service connections, so no worker needs a particular machine or a desktop session; the description names no robot count and no need for items to survive a failed run beyond the mail staying in the inbox until step 2 moves it.
**Configuration:** settings — questions 1, 2, 5, 6, 8, 12; constants — questions 3, 4, 7, 9, 10, 11, 13, 14; assets — none (the connections hold the sign-ins).
**Traceability:** per invoice: the item reference, the supplier invoice number, the SAP document number and status, the approval decision with approver, time and reason, and the outcome with its reason, in the job's log and — under B and C — the queue item; the failure notice of CQ12 per failed invoice; per job, a summary of invoices taken, posted, parked for approval, handed to the AP clerks and failed.

## Acceptance Criteria

1. Given a mail in the AP mailbox with one invoice PDF from a known supplier for 2,000.00 when the limit is 5,000.00 in the same currency, the automation posts the invoice in SAP with supplier invoice reference equal to the invoice number and the file attached, and moves the mail to the processed folder.
2. Given an invoice whose gross amount exceeds the limit, the automation parks it in SAP and creates one approval task for the finance approver group showing the supplier, invoice number, gross amount, limit and parked document number.
3. When the approver approves an over-limit invoice, the automation posts the parked document and its SAP status is posted.
4. When the approver rejects an over-limit invoice with a reason, the document stays parked and the AP clerks receive a mail with the supplier, invoice number, parked document number, approver and reason.
5. When an approval task is still open after 2 working days, the approver group gets a reminder; after 5 working days the AP clerks are told, and the task is still open.
6. Given an invoice whose gross amount equals the limit, the automation posts it without approval.
7. Given an invoice in a foreign currency, the automation compares its gross amount, converted at SAP's current rate, with the limit and parks or posts accordingly.
8. Given a mail with two invoice PDFs, the automation enters two SAP documents, one per invoice, each with its own outcome.
9. Given a mail with no attachment of the types of CQ14, the automation sends it to the AP clerks with the reason "no invoice document attached" and moves it to the needs-review folder; no SAP document is created.
10. Given an attachment classified as a credit note, the automation creates no SAP document and the AP clerks receive it with the reason "credit note received".
11. Given an invoice whose invoice number is missing or extracted below the confidence of CQ9, the automation creates no SAP document and the AP clerks receive the file with the field named.
12. Given an invoice whose tax number, bank account and name match no supplier, the automation creates no SAP document and the AP clerks receive the reason "supplier not found".
13. Given an invoice whose supplier and invoice number match a posted SAP supplier invoice, the automation creates no document and reports "duplicate of SAP document <number>/<fiscal year>".
14. Given an invoice whose net plus tax differs from its gross by 1.00, the automation creates no document and reports the three values.
15. Given a PO invoice whose purchase order belongs to another supplier, the automation creates no document and reports "purchase order <number> not found for supplier <number>".
16. Given a non-PO invoice from a supplier with a coding row, the automation enters one G/L line with the row's G/L account, cost centre and tax code; from a supplier with none, it creates no document and reports "no coding for supplier <number>".
17. When SAP refuses an entry with a business message, the AP clerks receive SAP's message and the invoice is not retried.
18. When SAP times out after it has created the document, the retry finds the document by its header text and continues from it; SAP holds exactly one document for the invoice.
19. When a parked invoice is posted by a person before the approver decides, the automation does not post it again and reports "parked document changed while awaiting approval".
20. When an invoice fails with a system error on every attempt of CQ11, it is recorded as failed and the recipients of CQ12 are told with the item reference, the step and the error.

## Complexity

complex

## Tags

finance, accounts-payable, supplier-invoices, sap-s4hana, outlook-365, integration-service, document-understanding, action-center, human-in-the-loop, long-running-workflow
