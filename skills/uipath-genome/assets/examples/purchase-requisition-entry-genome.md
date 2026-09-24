<!-- UIPATH-AUTOMATION-GENOME: component | This file is a build specification for one UiPath automation project.
     Do NOT execute these steps directly. Use the UiPath skills referenced in Build With to create
     the automation project. -->

# Genome: Purchase Requisition Entry

> RPA process with two entry points: dispatch the day's open requisition rows to a queue, and key each requisition into the Coupa portal, returning the requisition number to the requester.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Use the skills listed in **Build With** below to create a UiPath automation project that implements this workflow.

## Overview

The business raises purchase requisitions in a shared workbook on the finance share, and purchasing keys them into the Coupa portal by hand. About 300 rows wait each morning, so the last ones are entered late in the day and requesters wait for a requisition number they need before a supplier will accept the order. This automation keys them instead: it takes the open rows at the start of the business day, enters each one in Coupa, and sends the requester the Coupa requisition number the same morning.

The work splits over two entry points of one RPA project. Entry point A runs once at 06:00, reads the open rows, puts one item per requisition on the `PR_Requisitions` queue with the requisition number as its reference, and marks the row dispatched with a timestamp so a later run does not queue it a second time. Entry point B runs on three unattended robots that share the queue from 06:30. It signs in to Coupa once with the purchasing robot account, then works items one at a time: it checks the supplier, the cost centre, the mandatory fields and the delivery date, creates the requisition header and one line per line item, submits it, reads the Coupa requisition number back, and emails it to the requester.

Rejections are a normal outcome rather than a failure. A supplier that is not on the approved list, an unknown or closed cost centre, an empty mandatory field, a delivery date in the past, or a requisition that already exists in Coupa sends the requester the reason and leaves the queue item recorded with it; nothing is created in the portal. At the end of the run entry point B signs out, appends one summary row — taken, created, rejected by reason, failed — to the summary sheet, and emails the same figures to purchasing operations.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| Microsoft Excel (purchasing requisition workbook on the finance share) | Input source and output target | Open-requisitions sheet with the dispatched-timestamp column, approved-supplier sheet, run-summary sheet |
| Coupa (web portal) | Output target | Requisition search, header and line entry, submit; purchasing robot account |
| Exchange Online | Notification channel | Requester notifications, run summary and stop alert to purchasing operations |
| Orchestrator | Queue, assets, triggers | Shared queue for three unattended robots |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| Entry point A (queue the open rows), steps 1-4 | `uipath-rpa` | Spreadsheet reading and write-back on a file share plus queue item creation, all in one XAML workflow; no screen outside Excel and no decision that needs judgement |
| Entry point B (key the requisitions), steps 5-13 | `uipath-rpa` | Browser UI automation against the portal, spreadsheet lookups and mail in the same project; the portal offers no supported interface for requisition creation here, so `uipath-api-workflow` does not apply, and every decision is a deterministic rule against reference data rather than a judgement for `uipath-agents` |

## Platform Dependencies

| Resource | Type | Purpose |
|----------|------|---------|
| PR_Requisitions | Queue | Entry point A writes one item per requisition row; three robots running entry point B share it, and an item survives a failed run |
| Coupa_PurchasingRobot | Credential asset | Portal sign-in for the purchasing robot account on the production Coupa tenant |
| Coupa_PortalUrl | Text asset | Address of the Coupa tenant entry point B opens |
| FinanceShare_RequisitionsPath | Text asset | Location of the requisition workbook and the summary sheet on the finance share |
| Purchasing_Mailbox | Integration Service connection (Exchange Online) | Sends requester notifications, the run summary and the stop alert |
| PR_DispatchSchedule | Time trigger | Starts entry point A every business day at 06:00 |
| PR_RequisitionsQueueTrigger | Queue trigger | Starts entry point B from 06:30 on up to three unattended robots |

## Interface

- **Inputs:** A: none (time trigger); reads the open-requisition rows. B: one queue item per requisition — requisition number, requester email, supplier name, cost centre, delivery date, line items (description, quantity, unit price)
- **Outputs:** A: one queue item per undispatched row, plus the dispatched count and the skipped count. B: per item, the Coupa requisition number or a rejection reason; one run-summary row (taken, created, rejected by reason, failed)
- **Side effects:** requisitions created and submitted in Coupa; emails to requesters and to purchasing operations; dispatched-timestamp column and summary sheet written in the workbook

## Configuration Questions

1. Which workbook holds the requisitions, and where does it live? (default: the purchasing folder on the finance share, workbook `Purchase Requisitions`)
2. Which sheets hold the open requisitions, the approved suppliers, and the run summary? (default: `Open Requisitions`, `Approved Suppliers`, `Run Summary`)
3. Which Orchestrator queue carries the requisitions? (default: `PR_Requisitions`)
4. Which purchasing portal does entry point B sign in to? (default: the production Coupa tenant address, held as a Text asset)
5. Which mailbox sends the requester notifications and the run summary? (default: purchasing-robot@contoso.com)
6. Which address receives the run summary and the stop alert? (default: purchasing-operations@contoso.com)
7. When does each entry point start, and on how many robots? (default: entry point A every business day at 06:00; entry point B from 06:30 on three unattended robots)
8. How many times is a requisition retried after a system exception? (default: 2)
9. After how many consecutive system exceptions does the run stop and alert purchasing operations? (default: 3)
10. Where is the supplier checked? (default: the approved-supplier sheet; alternative: the portal's supplier search)
11. How long does entry point B wait for the portal to return a requisition number before the submit counts as a system exception? (default: 60 seconds)
12. Is a delivery date equal to the run date accepted? (default: yes — only a date earlier than the run date is rejected)

## Workflow

1. **Trigger A**: time trigger, every business day at 06:00.
2. **Read the open requisitions** (input: the requisition workbook on the finance share; output: the rows not yet dispatched): open the open-requisitions sheet and read every row that carries no dispatched timestamp; fields per row are requisition number, requester email, supplier name, cost centre, delivery date, and the line items (description, quantity, unit price).
3. **Create one work item per requisition** (input: one row; output: one queue item, or a skip):
   a. Reference is the requisition number
   b. If the requisition number already has an item on `PR_Requisitions` in any state, create nothing and count the row as skipped
   c. Otherwise create the item carrying requisition number, requester email, supplier name, cost centre, delivery date and the line items
4. **Mark the row dispatched** (input: the row and the run timestamp; output: the updated workbook): write the run timestamp into the dispatched column of every row that now has an item — one it created and one it skipped as already queued — and record the dispatched and skipped counts for the run.
5. **Trigger B**: queue trigger on `PR_Requisitions` from 06:30; up to three unattended robots share the queue.
6. **Open the portal and load reference data** (input: portal address, purchasing robot credential asset; output: a signed-in session and the two reference lists): open Coupa, sign in as the purchasing robot account, confirm the landing page belongs to that account, then read the approved-supplier list and the cost-centre list once so the per-item checks do not read them again.
7. **Take the next requisition** (input: `PR_Requisitions`; output: one requisition record): take one item; its reference is the requisition number.
8. **Validate the requisition** (input: requisition record, approved-supplier list, cost-centre list; output: accepted, or a rejection reason):
   a. Supplier name appears on the approved-supplier list and is active → otherwise `supplier-not-approved`
   b. Cost centre exists and is open on the run date → otherwise `cost-centre-unknown` when it is absent, `cost-centre-closed` when it is present but closed
   c. Requisition number, requester email, supplier name, cost centre, delivery date and at least one line item with a description, a quantity above zero and a unit price are all present → otherwise `mandatory-field-empty` naming the first empty field
   d. Delivery date is not earlier than the run date → otherwise `delivery-date-past`
   e. On the first failing check, carry the reason to step 12 and skip steps 9-11; nothing is entered in the portal
9. **Check whether the requisition already exists** (input: requisition number; output: an existing Coupa requisition number, or none): search the portal for the requisition number in the external-reference field; a match carries the reason `already-created` and the existing Coupa requisition number to step 12, and steps 10-11 are skipped.
10. **Create the requisition** (input: requisition record; output: an unsubmitted requisition):
    a. Header: requester, supplier, cost centre, delivery date, and the requisition number in the external-reference field
    b. One line per line item, in the order of the source row: description, quantity, unit price
    c. Before submitting, the line count and the sum of quantity × unit price must equal the source row
11. **Submit and read the number back** (input: the unsubmitted requisition; output: the Coupa requisition number): submit the requisition and read the number from the confirmation; no number within the configured wait counts as a system exception.
12. **Record the outcome and notify the requester** (input: the outcome — Coupa requisition number or rejection reason; output: the recorded item and one email): record the outcome on the queue item; email the requester at the address on the item, naming the requisition number and either the Coupa requisition number or the rejection reason in business language.
13. **Sign out and report the run** (input: the recorded outcomes of the run; output: one summary row and one email): sign out of the portal and close the browser, append a row to the run-summary sheet with the run date, items taken, created, rejected by reason and failed, and email the same figures to purchasing operations.

## Business Rules

### Step 2: Read the open requisitions
- A row that already carries a dispatched timestamp is never read again, whatever its outcome was on the earlier run.

### Step 3: Create one work item per requisition
- The requisition number is the item's reference and is unique per requisition: a number that already has an item on the queue is never queued a second time, whatever state that item is in.
- A row with no requisition number has no reference: it is left undispatched and counted as skipped so a person can complete it in the workbook.

### Step 4: Mark the row dispatched
- The timestamp is written only after the item exists on the queue, so a failure between the two leaves the row to the next run rather than losing the requisition.

### Step 8: Validate the requisition
- Supplier names are matched against the approved-supplier list ignoring case and surrounding spaces; a supplier that is absent or marked inactive is rejected.
- The cost centre must both exist and be open on the run date.
- The first failing check decides the reason; the remaining checks do not run, so one reason reaches the requester.
- A rejected requisition is never entered in the portal, and no requisition is created for it later without a new row.

### Step 9: Check whether the requisition already exists
- A requisition number that already carries a Coupa requisition is a rejection with reason `already-created` and the existing Coupa requisition number; a second requisition is never created for the same requisition number.

### Step 10: Create the requisition
- The requisition number goes into the external-reference field of the header, because that is what step 9 searches on a later run.
- A line count or a total that differs from the source row abandons the unsubmitted requisition rather than submitting a wrong order.

### Step 12: Record the outcome and notify the requester
- Every per-item outcome is recorded on the queue item and emailed to the requester: a created requisition names the Coupa requisition number, a rejection names the reason.

### General
- Only entry point A writes the dispatched column, and only the end-of-run step writes the summary sheet, so three robots working at once never write the same cells.
- Each requisition is worked by exactly one robot, because the queue hands an item to one robot only.

## Error Handling

### Step 2: Read the open requisitions
- Workbook locked by another user, or the finance share unreachable: retry 3× with a one-minute wait, then end the run without dispatching and alert purchasing operations; the rows stay undispatched for the next run.
- No undispatched rows on the sheet: end the run with zero items created, record the zero counts, send no alert.

### Step 3: Create one work item per requisition
- Queue unavailable: retry 3×, then end the run; rows already queued keep their timestamp and the rest stay undispatched, and purchasing operations are alerted.

### Step 6: Open the portal and load reference data
- Portal unreachable, or sign-in refused: close the browser and retry the sign-in twice, then end the run and alert purchasing operations; items stay on the queue for the next run.
- Approved-supplier list or cost-centre list unreadable: end the run before taking any item and alert purchasing operations, rather than rejecting requisitions against missing reference data.

### Steps 9-11: Portal lookup, creation and submit
- Portal timeout, lost session, or an expected element not found: capture a screenshot, sign out or close the browser, sign in again, and retry the same requisition 2× (Configuration Question 8); still failing, record the item as failed with the reason and continue with the next item.
- An unsubmitted requisition left behind by a failure is abandoned before the retry, so the retry starts from the search in step 9 and finds nothing to create twice.

### Step 12: Record the outcome and notify the requester
- Mail server unavailable: retry the send twice; still failing, record the item as failed with reason `notification-not-sent`, keeping the Coupa requisition number on the record, so the run summary carries the number for purchasing operations to forward. The requisition is not created a second time.

### Step 13: Sign out and report the run
- Summary sheet locked or unreachable: retry 3×, then email the figures to purchasing operations and state in the mail that the sheet was not written.
- Sign-out failure: close the browser anyway and finish the run; it is not a run failure.

### Global
- Three consecutive system exceptions (Configuration Question 9): stop the run, sign out, close the browser, and alert purchasing operations with the three reasons; untaken items stay on the queue for the next run.
- Every system exception captures a screenshot of the portal before recovery, and the requisition number is recorded with the reason.
- Unhandled exception: capture a screenshot, record the requisition number and the step, sign out and close the portal, record the item as failed, and continue with the next item unless the consecutive-failure threshold is reached.

## Transactional Shape


**Flows:** Flow 1 — requisition row: steps 1–4 (entry point A) → steps 5–13 (entry point B).

### Flow 1 — one requisition row: steps 1–4 → steps 5–13

**Unit of work:** one requisition row; reference the requisition number, which is unique per requisition and keeps a number from being queued twice; fields as in Interface — requester email, supplier name, cost centre, delivery date, line items (description, quantity, unit price); about 300 a day, dispatched in one run every business day at 06:00 and worked from 06:30; chosen because Coupa accepts or rejects a requisition as a whole, the requisition number identifies it, and re-keying one requisition costs about a minute.
**Alternative units of work:** one requisition line — fits when each line is keyed into a separate order; today Coupa submits a requisition with all its lines at once, so a line cannot be retried without its header.

**As-is** — how the project handles the requisitions:

| Aspect | As-is |
|---|---|
| Produced by | Steps 1–4 (entry point A), once every business day at 06:00: read the rows of the open-requisitions sheet that carry no dispatched timestamp; one item per requisition number; a number already on the queue is skipped and counted; queued and skipped rows are both marked with the dispatched timestamp |
| Consumed by | Steps 5–13 (entry point B) on three unattended robots from 06:30; any robot takes the next item in queue order |
| Item store | Orchestrator queue `PR_Requisitions`; per item the status, and as output the Coupa requisition number or the rejection reason |
| Coordination | The dispatched-timestamp column keeps a row from being queued on a second run; nothing joins items to one another |
| Item kinds | One kind |
| Step groups | once per run: steps 5–6; per item: steps 7–12; at the end: step 13 (steps 1–4 are the producer's own) |

| Outcome | When | Effect |
|---|---|---|
| Success | every per-item step completed | item recorded as done with the Coupa requisition number, which the requester is emailed |
| Business exception | Step 8 rules: supplier not approved, cost centre unknown, cost centre closed, mandatory field empty, delivery date in the past; Step 9 rule: already created | no retry; item recorded with the reason and the requester emailed it; nothing created in the portal; run continues |
| System exception | every other failure — Step 6 and Steps 9-11 handlers: portal unreachable or sign-in refused, portal timeout, lost session, element not found (the step 12 mail handler retries the send only and records `notification-not-sent`, so a created requisition is never entered twice) | portal closed and signed in again, item retried 2× (Configuration Question 8), then recorded as failed with the reason; run stops after 3 consecutive (Configuration Question 9) and purchasing operations are alerted |

**Split options** — none asserted; runner counts are deployment settings:

| Unit of work | Option | Processes | Item store | Requires | Changes against as-is |
|---|---|---|---|---|---|
| one requisition row | A — one process, both roles | one RPA process that reads the open rows and keys them in the same job | in-process list | excluded: three robots share the items and an item must survive a failed run | the queue and the 06:30 start disappear; one robot keys all 300 requisitions |
| one requisition row | B — a producer process and a consumer process | two processes — entry point A (queue the open rows, 06:00) and entry point B (key the requisitions on the REFramework in queue mode, three robots from 06:30), published from one project (the as-is) or from two projects | `PR_Requisitions` | entry point A triggered once at 06:00; the dispatched timestamp keeps a second dispatch harmless | none as one project — the as-is; as two projects, two packages and the workbook location and mailbox settings held twice or in a shared library |
| one requisition row | C — one process, both roles, with a queue | one RPA process with one entry point, started on the three robots at 06:00: every job first queues the open rows behind a once-guard, then keys requisitions from the queue on the REFramework in queue mode | `PR_Requisitions` | a once-guard for the dispatch, since all three robots run it — the dispatched timestamp plus the requisition number the queue refuses twice; both roles on the same robots and schedule | one entry point and one trigger instead of two; keying starts right after the dispatch instead of at 06:30; whichever robot dispatches first writes the dispatched column, the other two find no undispatched rows or wait on the locked workbook (step 2's retry) |
| one requisition line | A — one process, both roles | one RPA process whose items are lines; the first line of a requisition creates its header | in-process list of lines | excluded: as for one requisition row | the requester mail and the total check run after a requisition's last line in the same job |
| one requisition line | B — a producer process and a consumer process | producer and consumer processes over a queue of lines | one queue of lines | Coupa accepting lines added to an open requisition | header creation guarded when several robots take lines of one requisition; the requester mail and the total check need all lines of a requisition to be final |
| one requisition line | C — one process, both roles, with a queue | one RPA process that queues the lines behind a once-guard and then works them, in every job | one queue of lines | as for B, plus the once-guard for the dispatch on every robot | as for B, with one entry point and one trigger |

**Evidence:** three unattended robots share the queue from 06:30; the rows are dispatched once per business day at 06:00; an item must survive a failed run and be retried in a later one; Coupa submits a requisition with all its lines at once; purchasing operations need per-item visibility.
**Configuration:** settings — questions 1-7 and 10 (workbook location, sheet names, queue name, portal address, sending mailbox, operations address, schedules and robot count, supplier lookup source); constants — questions 8, 9, 11 and 12 (item retries, consecutive-failure threshold, submit wait, same-day delivery date); assets — every Credential and Text row of Platform Dependencies, read at the start of the run.
**Traceability:** the queue item's status and history per requisition number, carrying the Coupa requisition number or the rejection reason; a screenshot on every system exception; the dispatched-timestamp column in the workbook for what was queued; one run-summary row (taken, created, rejected by reason, failed) on the summary sheet plus the same figures emailed to purchasing operations.

## Acceptance Criteria

- [ ] Given 300 open rows with no dispatched timestamp, entry point A creates 300 items on `PR_Requisitions`, one per requisition number, and writes the run timestamp on each row.
- [ ] Given a row whose requisition number already has an item on the queue, entry point A creates no second item, counts the row as skipped, and still marks it dispatched.
- [ ] Given the open-requisitions sheet has no undispatched rows, entry point A ends the run with zero items created and sends no alert.
- [ ] Given the workbook is locked by another user, entry point A retries three times, dispatches nothing, and alerts purchasing operations with the reason.
- [ ] Given a signed-in portal session, entry point B reads the approved-supplier list and the cost-centre list once for the whole run rather than per requisition.
- [ ] Given a requisition whose supplier is not on the approved-supplier list, entry point B creates nothing in the portal, records the item with reason `supplier-not-approved`, and emails the requester that reason.
- [ ] Given a cost centre that is closed on the run date, the item is recorded with reason `cost-centre-closed` and the requester is emailed, while the next item is still worked.
- [ ] Given a requisition with an empty delivery date, the item is recorded with reason `mandatory-field-empty` naming the delivery date.
- [ ] Given a delivery date one day before the run date, the item is recorded with reason `delivery-date-past`.
- [ ] Given a requisition number that already carries a Coupa requisition, entry point B creates no second requisition and records `already-created` with the existing Coupa requisition number.
- [ ] Given a valid requisition with three line items, entry point B creates a Coupa requisition with three lines matching description, quantity and unit price, submits it, and records the Coupa requisition number.
- [ ] Given a submitted requisition, the requester receives an email naming both the requisition number and the Coupa requisition number.
- [ ] Given the portal session is lost while a requisition is being entered, entry point B captures a screenshot, signs in again, retries the same requisition at most twice, and then records it as failed with the reason.
- [ ] Given a third consecutive system exception, entry point B stops the run, leaves the untaken items on the queue, and alerts purchasing operations with the three reasons.
- [ ] Given the mail server is unavailable after a requisition was created, the item keeps its Coupa requisition number, is recorded as failed with reason `notification-not-sent`, and no second requisition is created.
- [ ] Given a completed run, the summary sheet gains one row with items taken, created, rejected by reason and failed, and purchasing operations receives the same figures by email.
- [ ] Given three robots taking items at the same time, each requisition is worked exactly once.

## Complexity

medium

## Tags

purchasing, requisition, coupa, excel, queues, producer-consumer, transactional, email
