# Final Resolution

---

**Root Cause:** The `Delete Outlook Mail Message` activity in `Main.xaml`
was handed a `MailMessage` (`mailToDelete`) that had been retrieved much
earlier by the upstream `Get Outlook Mail Messages`. Between the fetch and
the delete, the workflow ran a long per-item processing loop. By the time
the delete fired, the target item had been moved or deleted out of `Inbox`
(by a user, another automation, or an Outlook rule competing for the same
folder), so the activity could no longer find it at its original location
and faulted with:

`Delete Outlook Mail Message: The operation failed. An object could not be
found.` (`UiPath.Mail.Exception` wrapping
`System.Runtime.InteropServices.COMException ... (0x8004010F)`).

This is **Branch 1 (stale message reference)** of the
`delete-outlook-mail-failures` playbook.

**What went wrong:** The `InboxCleanupBot` job (started
2026-06-04T11:00:00Z) faulted ~8 seconds after launch. `Get Outlook Mail
Messages` retrieved 24 messages from `Inbox` at 11:00:03 and the oldest was
selected for deletion (EntryID `0000004A...112233`). The workflow then
processed all 24 messages in a `For Each` loop with a per-item delay
(downstream API call + attachment save) lasting ~4.7 seconds. At delete
time (~11:00:08), the activity logged that the target message was no longer
in `Inbox` ("it appears to have been moved or deleted since retrieval at
11:00:03"), then faulted. The visible **fetch -> delete gap** is the
hallmark of the branch.

**Why:** A `MailMessage` reference is only valid while the underlying item
stays put. The longer the gap between fetching and acting on it -- and the
more concurrent activity there is on the same folder -- the higher the
chance another actor moves or deletes the item first. Once the item leaves
its original location, the desktop COM delete cannot resolve it and reports
"An object could not be found."

---

**Not the other branches.** This is **not** Branch 2 (collection modified
in a loop) -- the `Delete` runs *after* the `For Each`, not inside it, and
the error is "object could not be found", not "Collection was modified;
enumeration operation may not execute." It is **not** Branch 3 (New Outlook
/ desktop COM API removed) -- the activity bound to Outlook fine and the
failure is item-specific, not a complete post-update break. It is **not**
Branch 4 (COM session blocked / modal dialog / timeout / privilege
mismatch) -- there is a clean, specific exception, not a timeout or freeze.
It is **not** Branch 5 (mailbox permission / access denied) -- the error is
**"not found"**, not "access denied", and there is no shared-mailbox /
Full-Access signal. It is **not** a missing folder or a folder-path typo --
`Inbox` resolved and `Get` returned 24 messages from it. And it is **not**
fixed by **adding a Delay before the delete** -- a longer gap makes Branch 1
*worse*.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: InboxCleanupBot -- Faulted at 2026-06-04T11:00:08.220Z (ran for ~8.1 seconds)
- Job type: Unattended, triggered by a scheduled trigger on machine MOCK-HOST
- Folder: RPA Production (key `b3c4d5e6-7f80-4a1b-8c2d-3e4f5a6b7c8d`)
- Robot account: `UIPATH\ROBOTUSER1` / `RobotUser1`
- Final error: `Delete Outlook Mail Message: The operation failed. An object could not be found.` -> `Main.xaml` -> `DeleteOutlookMailMessage "Delete Outlook Mail Message"` -> `Sequence "Main Sequence"` -> `Main "Main"`

### Mail Activities (Root Cause)
- `Main.xaml` structure: `Get Outlook Mail Messages` (Inbox -> `mailList`) -> select `mailList[0]` as `mailToDelete` -> a `For Each` over `mailList` doing per-item work with a `Delay` -> `Delete Outlook Mail Message` (`mailToDelete`) **after** the loop. The delete target is fetched once, then acted on seconds later.
- Smoking-gun job log:
  - `11:00:03` -- `[Get Outlook Mail Messages] retrieved 24 messages from 'Inbox'`
  - `11:00:03` -- target for deletion selected (EntryID `0000004A...112233`, location `Inbox`)
  - `11:00:03 -> 11:00:07` -- `[Process each message]` loop (per-item delay, ~4.7s total)
  - `11:00:08` -- `[Delete Outlook Mail Message] target message ... not found in 'Inbox'; it appears to have been moved or deleted since retrieval at 11:00:03`
  - `11:00:08` -- `The operation failed. An object could not be found.`
- The ~5-second fetch -> delete gap, plus the explicit "moved or deleted since retrieval" log line, confirm the stale reference.

---

**Immediate fix:**

1. **Fetch immediately before deleting.** Restructure `Main.xaml` so the
   `Delete Outlook Mail Message` runs as close as possible to the `Get`
   that produced its target -- do not hold a `MailMessage` reference across
   the long per-item processing loop. Either move the delete to run right
   after a fresh fetch of just that item, or re-fetch the target by a
   stable key (Subject + received time, or EntryID) immediately before
   deleting.

2. **Wrap the delete in a Try Catch that tolerates an already-gone item.**
   Surround `Delete Outlook Mail Message` with a `Try Catch`. In the
   `Catch` for the "object could not be found" / `UiPath.Mail.Exception`
   case, treat the work as effectively done (the item is already gone) and
   log + continue rather than faulting the job.

3. **Re-confirm under contention.** If another job, user, or Outlook rule
   legitimately competes for `Inbox`, re-fetch and re-confirm the item
   exists right before deleting it.

> Do **not** "add a Delay before the delete to let things settle." A longer
> gap makes this failure *more* likely, not less -- it is the opposite of
> the fix.

---

**Preventive fix:**

1. **Studio / workflow design** -- never carry a `MailMessage` reference
   across long-running work. Fetch-then-act promptly, and guard every
   destructive mail activity (Delete / Move) with a Try Catch for
   already-moved / already-deleted items.
   - **Why:** Mail item references go stale the moment another actor
     touches the folder.
   - **Who:** RPA developer.

2. **Folder concurrency** -- avoid running multiple jobs / rules against the
   same mailbox folder at once, or partition the work so each item is owned
   by exactly one actor; for unattended server-side mailbox cleanup, prefer
   the modern Microsoft 365 / Graph o365 activities over desktop COM.
   - **Why:** Removes the concurrency window that lets items move out from
     under a pending delete.
   - **Who:** Platform / RPA team.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Stale message reference: the target `MailMessage` was moved/deleted between `Get` (11:00:03) and `Delete` (11:00:08), so the delete could not find it | High | Confirmed | Yes | `"An object could not be found"` + `Main.xaml` (Get, long loop, then Delete) + job-log "moved or deleted since retrieval at 11:00:03" | Fetch-then-delete promptly; Try Catch the already-gone item; re-confirm under contention |
| H2 | Collection modified inside a `For Each` over the live list (Branch 2) | Low | Eliminated | No | Delete runs *after* the loop, not inside it; error is "object could not be found", not "Collection was modified" | n/a |
| H3 | Mailbox permission / access denied on a shared mailbox (Branch 5) | Low | Eliminated | No | Error is "not found", not "access denied"; no shared-mailbox / Full-Access signal | n/a |

---

This maps to
`references/activity-packages/mail-activities/playbooks/delete-outlook-mail-failures.md`
(Branch 1 -- stale message reference).

Would you like me to draft the `Main.xaml` change (move the delete next to
a fresh fetch and add the Try Catch) as a diff you can apply, or clean up
the `.local/investigations/` folder?
