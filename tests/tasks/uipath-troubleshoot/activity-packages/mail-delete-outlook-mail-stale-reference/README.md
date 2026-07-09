# Delete Outlook Mail Message Failure - Stale Message Reference (Branch 1)

This scenario reproduces a runtime `Delete Outlook Mail Message`
(`DeleteOutlookMailMessage`, `UiPath.Mail.Outlook.Activities`) failure
caused by a **stale message reference**: the `MailMessage` retrieved by an
upstream `Get Outlook Mail Messages` is moved or deleted out of its folder
before the delete fires, so the activity can no longer find it and faults
with `The operation failed. An object could not be found.`

It validates **Branch 1** of
`references/activity-packages/mail-activities/playbooks/delete-outlook-mail-failures.md`.

## What this scenario uncovers

**Root Cause:** In `Main.xaml`, `Get Outlook Mail Messages` reads `Inbox`
into `mailList`, the oldest item is selected as `mailToDelete`, the workflow
then runs a long per-item `For Each` processing loop (with a `Delay`), and
only **after** the loop does `Delete Outlook Mail Message` try to delete
`mailToDelete`. The item was valid at fetch time (11:00:03) but had been
moved/deleted by the time the delete ran (~11:00:08). The visible
**fetch -> delete gap** plus the job-log line "target message ... not found
in 'Inbox'; it appears to have been moved or deleted since retrieval at
11:00:03" are the smoking gun.

**Fix (per the playbook):** fetch-then-delete promptly (do not hold a
`MailMessage` across long work), and wrap the delete in a `Try Catch` that
tolerates an already-moved / already-deleted item; re-confirm under folder
contention. **Adding a Delay before the delete is the wrong answer** -- it
widens the gap and makes the failure more likely.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project: Get -> select -> long `For Each` loop -> Delete (after the loop) |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

The job key / TraceId is `c4d5e6f7-8091-4b2c-9d3e-4f5a6b7c8d9e` (short key
`c4d5e6f7`); the `RPA Production` folder key is
`b3c4d5e6-7f80-4a1b-8c2d-3e4f5a6b7c8d`. The failing job is Unattended on
`MOCK-HOST` under `UIPATH\ROBOTUSER1`, faulting ~8s after start.

## Sibling-branch comparison (why this is Branch 1, not 2-5)

| Branch | Signature | Distinguishing evidence here |
|--------|-----------|------------------------------|
| **B1 (this)** Stale message reference | `An object could not be found` + fetch->delete gap | Get at 11:00:03, Delete at 11:00:08 after a loop; "moved or deleted since retrieval" log line |
| B2 Collection modified in loop | `Collection was modified; enumeration operation may not execute.` | Delete runs **after** the `For Each`, not inside it; no enumeration error |
| B3 New Outlook (COM API removed) | Complete post-update break, COM-bind failure | Activity bound to Outlook fine; failure is item-specific, not total |
| B4 COM session blocked / privilege | Timeout / freeze, no clean exception | Clean, specific exception; no timeout or hang |
| B5 Mailbox permission / access | Access-denied / delete-denied (often shared mailbox) | Error is **"not found"**, not "access denied"; no shared-mailbox signal |

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched `delete-outlook-mail-failures.md` / Branch 1 (stale message
  reference) and read the playbook under
  `references/.../mail-activities/playbooks/`.
- Agent attributed the fault to the item being moved/deleted between Get and
  Delete (the gap/concurrency window) and recommended fetch-then-delete
  promptly + a Try Catch tolerating the already-gone item -- **not** adding
  a Delay, and **not** a sibling branch (collection-modified, New Outlook,
  COM-blocked, or access-denied).

This scenario **scores the conclusion, not the trajectory**: the LLM judge
grades only the agent's final response and tool calls against
`RESOLUTION.md`, not any intermediate `.local/investigations/` state.
