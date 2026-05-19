---
confidence: high
---

# GSuite Get Newest Email — no email matched the filter

## Context

What this looks like:
- Activity `Get Newest Email` (UiPath.GSuite.Activities, GetNewestEmailConnections) throws `GmailException`
- Error message: `No email matching the search criteria has been found`
- Job faults synchronously the moment the activity runs — no retry, no wait

What can cause it:
- The Gmail mailbox contains zero messages matching the configured filter at the moment the activity executes. This is the only cause — the activity issues a single Gmail API query with `MaxResults = 1` and throws when the result is empty.

What to look for:
- The exact filter the activity was configured with: `Folder`, `FilterSelectionMode` (ConditionBuilder vs Query), `QueryFilter` (raw Gmail query), or the structured `Filter` collection (`From`, `To`, `Subject`, `Body`, `DateAndTime`, `Cc`, `Bcc`, `Categories`, `Filename`, `Labels`)
- Boolean modifiers tightening the search: `UnreadOnly`, `WithAttachmentsOnly`, `ImportantOnly`, `StarredOnly`
- The job run timestamp — only emails received at or before this moment are eligible

## Investigation

1. From the job logs or workflow, capture the exact values of every filter property listed above and the job start timestamp.
2. Confirm the activity is `GetNewestEmailConnections` (display name "Get Newest Email") and not a long-running trigger — this activity does not poll or wait.
3. There is nothing further to verify programmatically; the Gmail API has already authoritatively returned zero matches for that query. Proceed to Resolution.

## Resolution

- **In all cases:** Report the captured filter values and job timestamp to the user and ask them to sign in to the target Gmail mailbox and confirm whether any message matching those filters was present at or before the job run time. Then:
  - **If no matching email existed:** This is expected behavior, not a defect. Recommend either (a) loosening the filter (remove `UnreadOnly`/`WithAttachmentsOnly`/`ImportantOnly`/`StarredOnly`, broaden `Subject`/`From`/`DateAndTime`, switch `FilterSelectionMode` to a less restrictive `QueryFilter`), or (b) wrapping the activity in a Try/Catch so the workflow handles the empty-mailbox case explicitly, or (c) scheduling the job to run after the expected email arrives.
  - **If a matching email did exist in the mailbox at that time:** Ask the user to copy the matching message's raw Gmail search query (e.g., `from:foo@bar.com subject:"X" has:attachment`) and compare it against the activity's configured filter to identify the mismatch (common culprits: label scoping, `Folder` set to a label that excludes Inbox, time-zone offset on `DateAndTime`, case-sensitivity expectations that Gmail does not honor).
