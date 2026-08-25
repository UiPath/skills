---
confidence: high
---

# O365 Get Newest Email — no email matched the filter criteria

## Context

What this looks like:
- Activity `Get Newest Email` (UiPath.MicrosoftOffice365.Activities, `GetNewestEmail`) throws `Office365Exception`
- Error message: `No email matching the filter criteria, received in the last 1 hour has been found. Please generate a new email that fits the criteria and run the workflow again`
- Job faults synchronously the moment the activity runs — no retry, no wait

What can cause it:
- The target mailbox contains zero messages matching the configured filter at the moment the activity executes. This is the only cause — the activity issues a single Microsoft Graph query and throws when the result is empty.

What to look for:
- The exact filter the activity was configured with: `MailFolder` (Inbox or selected folder), `FreeTextFilter` (free-text search), `QueryFilter` (raw OData `$filter` expression), `Importance` (Any/Low/Normal/High), `Mailbox` (shared mailbox address, when `UseSharedMailbox = true`)
- Boolean modifiers tightening the search: `UnreadOnly`, `WithAttachmentsOnly`
- The job run timestamp — only emails received at or before this moment are eligible

> The same exception can also surface from `WaitForEmailReceived` (persistence) and the `NewEmailReceived` trigger when their debug/healing sample lookup returns empty. The diagnostic is the same — verify the mailbox against the filter — but those activities are async by design, so do not apply this playbook's "synchronous fault on first run" framing to them.

## Investigation

1. From the job logs or workflow, capture the exact values of every filter property listed above and the job start timestamp.
2. Confirm the activity is `GetNewestEmail` (display name "Get Newest Email") in `UiPath.MicrosoftOffice365.Activities` — not a trigger or persistence activity, which have different semantics.
3. There is nothing further to verify programmatically; the Microsoft Graph API has already authoritatively returned zero matches for that query. Proceed to Resolution.

## Resolution

- **In all cases:** Report the captured filter values and job timestamp to the user and ask them to sign in to the target mailbox (or shared mailbox, if `UseSharedMailbox = true`) and confirm whether any message matching those filters was received **at or before** the job run timestamp. Then:
  - **If no matching email existed in the mailbox at that time:** This is expected behavior, not a defect. Recommend either (a) loosening the filter (clear `UnreadOnly`/`WithAttachmentsOnly`, broaden `FreeTextFilter`, simplify the `QueryFilter` OData expression, set `Importance` to `Any`, switch `MailFolder` to a broader folder such as Inbox), or (b) wrapping the activity in a Try/Catch so the workflow handles the empty-result case explicitly, or (c) scheduling the job to run after the expected email arrives.
  - **If a matching email did exist in the mailbox at that time:** Ask the user to copy the matching message's relevant headers (From, To, Subject, ReceivedDateTime, Importance, IsRead, HasAttachments, parent folder) and compare them against the activity's configured filter to identify the mismatch (common culprits: `MailFolder` set to a subfolder that excludes the message, OData `$filter` syntax error or wrong property name in `QueryFilter`, `FreeTextFilter` case/punctuation expectations Graph search does not honor, `Importance` set to a specific level when the email is `Normal`, time-zone offset on date predicates).
