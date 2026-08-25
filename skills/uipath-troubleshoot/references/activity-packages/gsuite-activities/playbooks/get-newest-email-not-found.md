---
confidence: high
---

# GSuite Gmail — no email matched the filter (Get Newest Email or trigger debug run)

## Context

What this looks like — a `GmailException` with one of these messages:
- `No email matching the search criteria has been found` — **Get Newest Email** (`GetNewestEmailConnections`). Faults synchronously the moment the activity runs — no retry, no wait.
- `No email matching the filter criteria, received in the last 1 hour has been found. Please generate a new email that fits the criteria and run the workflow again` — **New Email Received** trigger (`Gmail.Triggers.NewEmailReceived`) executed in **debug / test mode**.
- `No email matching the filter criteria, sent in the last 1 hour has been found. Please generate a new email that fits the criteria and run the workflow again` — **Email Sent** trigger (`Gmail.Triggers.EmailSent`) executed in **debug / test mode**.

What can cause it:
- The Gmail mailbox contains zero messages matching the configured filter at the moment the activity executes. For `GetNewestEmailConnections`, the activity issues a single Gmail API query with `MaxResults = 1` and throws when the result is empty.
- For the **triggers**: this only occurs in debug/test mode, where the trigger fetches a *sample* event by querying the mailbox for a matching message **received/sent in the last 1 hour**. At production runtime the trigger is driven by an Orchestrator event id and waits for real events instead of throwing — so this message means a test run found no qualifying recent email, not that the production trigger is broken.

What to look for:
- The exact filter the activity was configured with: `Folder`, `FilterSelectionMode` (ConditionBuilder vs Query), `QueryFilter` (raw Gmail query), or the structured `Filter` collection (`From`, `To`, `Subject`, `Body`, `DateAndTime`, `Cc`, `Bcc`, `Categories`, `Filename`, `Labels`)
- Boolean modifiers tightening the search: `UnreadOnly`, `WithAttachmentsOnly`, `ImportantOnly`, `StarredOnly`
- The job run timestamp — only emails received at or before this moment are eligible

## Investigation

1. From the job logs or workflow, capture the exact values of every filter property listed above and the job start timestamp.
2. Identify which activity threw: `GetNewestEmailConnections` (one-shot query, message text `No email matching the search criteria has been found`) or a trigger run in debug/test mode (message text mentions `received/sent in the last 1 hour`). For a trigger, also confirm this was a test/debug execution, not production — at production runtime the trigger waits for events and does not throw this.
3. There is nothing further to verify programmatically; the Gmail API has already authoritatively returned zero matches for that query. Proceed to Resolution.

## Resolution

- **In all cases:** Report the captured filter values and job timestamp to the user and ask them to sign in to the target Gmail mailbox and confirm whether any message matching those filters was present at or before the job run time. Then:
  - **If no matching email existed:** This is expected behavior, not a defect. Recommend either (a) loosening the filter (remove `UnreadOnly`/`WithAttachmentsOnly`/`ImportantOnly`/`StarredOnly`, broaden `Subject`/`From`/`DateAndTime`, switch `FilterSelectionMode` to a less restrictive `QueryFilter`), or (b) wrapping the activity in a Try/Catch so the workflow handles the empty-mailbox case explicitly, or (c) scheduling the job to run after the expected email arrives. **For a trigger debug run:** send/receive an email matching the filter within the last hour, then re-run the test — the message says as much (`generate a new email that fits the criteria and run the workflow again`).
  - **If a matching email did exist in the mailbox at that time:** Ask the user to copy the matching message's raw Gmail search query (e.g., `from:foo@bar.com subject:"X" has:attachment`) and compare it against the activity's configured filter to identify the mismatch (common culprits: label scoping, `Folder` set to a label that excludes Inbox, time-zone offset on `DateAndTime`, case-sensitivity expectations that Gmail does not honor).
