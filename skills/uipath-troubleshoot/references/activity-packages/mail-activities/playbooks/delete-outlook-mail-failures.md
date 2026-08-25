---
confidence: medium
---

# Delete Outlook Mail Message Failures

## Context

A `UiPath.Mail.Outlook.Activities` `Delete Outlook Mail Message` (`DeleteOutlookMailMessage`) activity deletes a `MailMessage` from the **locally installed Outlook desktop application** through COM interop. It takes a `MailMessage` (typically an item from a preceding `Get Outlook Mail Messages`) plus an optional `Account`, and removes that item under the Outlook profile of the Windows user the Robot runs as. Failures cluster around a **stale message reference** (the item moved/deleted between fetch and delete), **mutating the message collection inside a loop**, the **New Outlook** client removing the desktop COM API, the **COM session being blocked** (modal dialog / privilege mismatch), and **mailbox permissions** (the Robot account lacking delete rights, especially on shared mailboxes).

Delete shares the desktop-COM surface with the other Outlook activities — the New-Outlook and COM-blocked/privilege failures are diagnosed like [move-outlook-mail-failures.md](./move-outlook-mail-failures.md) branch 4 and [send-outlook-mail-failures.md](./send-outlook-mail-failures.md) branch 2, and `Account`/shared-mailbox handling matches [get-outlook-mail-failures.md](./get-outlook-mail-failures.md) branch 1. What is distinctive to Delete is the **stale-reference** fault and the **collection-modified-in-loop** error. For unattended / server-side deletes with no desktop Outlook, prefer the modern Graph **o365-activities**.

What this looks like — Delete Outlook Mail Message faults surface as one of these signatures:

- `The operation failed. An object could not be found.` — the target message no longer exists at that location — branch 1.
- `Collection was modified; enumeration operation may not execute.` raised inside a `For Each` over the message list — branch 2.
- The automation **broke completely after a system/Office update** that flipped the host to **New Outlook** — branch 3.
- `The operation has timed out` / an intermittent **freeze** with no clean exception — branch 4.
- A **permission / access-denied** error (or a folder that resolves but cannot be modified), commonly on a **shared mailbox** — branch 5.

What can cause it (cause-branches — pick the right one from evidence):

1. **Stale message reference.** The `MailMessage` passed to Delete no longer exists in that exact location: a human user, another automation, or an Outlook rule moved or deleted the item **after** `Get Outlook Mail Messages` retrieved it. Surfaces as `The operation failed. An object could not be found.` Hallmark: large time gap (or concurrent processing) between fetch and delete.
2. **Collection modified inside the loop.** A `For Each` iterates the `List<MailMessage>` from Get, and Delete runs **directly inside** that loop. Deleting an item mutates the live collection mid-enumeration, invalidating the loop pointer — `Collection was modified; enumeration operation may not execute.`
3. **New Outlook (desktop COM API removed).** The host updated to Microsoft's **New Outlook** (web-hybrid client), which removes the Outlook Desktop COM API the classic activities rely on. The activity can no longer bind to an Outlook COM server. Hallmark: worked, then broke completely right after an update.
4. **COM session blocked (modal dialog / privilege).** The local Outlook COM interop is blocked: a **modal dialog** is foregrounded (notably the programmatic-access / "a program is trying to access email" warning), or UiPath and Outlook run at **mismatched privilege levels** (one elevated/Administrator, the other standard), so Windows blocks the cross-process call. Surfaces as a timeout or a hang.
5. **Mailbox permission / access denied.** The Robot account lacks the read/write/**delete** rights on the target folder — most common on a **shared mailbox** where the account has Send-As but not Full Access, and/or the shared mailbox address is not set in `Account`.

What to look for:

- **The exception text and the fetch→delete gap.** `An object could not be found` with a delay/concurrency between Get and Delete → branch 1; `Collection was modified` inside a loop → branch 2; "broke after an update" → branch 3; a timeout/freeze → branch 4; an access/permission error → branch 5.
- **The workflow structure** — whether Delete sits **inside a `For Each`** over the Get output (branch 2), and how long/much runs between Get and Delete (branch 1). From `Main.xaml`.
- **Outlook client variant + session/privilege** — Classic vs New Outlook (branch 3), and whether a modal dialog or a UiPath-vs-Outlook elevation mismatch could block COM (branch 4). Host-verifiable.
- **`Account` + mailbox rights** — whether the target is a shared mailbox, whether its address is in `Account`, and whether the Robot account has **Full Access** (not just Send-As). Load-bearing for branch 5.

## Investigation

Go in this order — cheaper checks first.

1. **Capture the exact error, the workflow structure, and the host.** From `uip or jobs get <job-key> --output json` → `Info`: the exception class and message. From workflow source (`.xaml`): whether `Delete Outlook Mail Message` runs inside a `For Each` over the Get output, the gap between Get and Delete, and the `Account`. From the job: the Robot **host**, attended vs unattended, and the Outlook client variant if known.

2. **Branch the diagnostic on the signature.**
   - `The operation failed. An object could not be found.` → branch 1; go to step 3.
   - `Collection was modified; enumeration operation may not execute.` → branch 2; go to step 4.
   - "Broke completely after an update" / New Outlook on the host → branch 3; go to step 5.
   - Timeout / freeze, no clean exception → branch 4; go to step 6.
   - Permission / access-denied error → branch 5; go to step 7.

3. **Confirm branch 1 (stale reference).** Confirm the failing item is one Delete tried to remove and that something could have moved/deleted it between fetch and delete — a long delay, a parallel job, a user, or an Outlook rule on the same folder. An `object could not be found` with that gap confirms the branch.
4. **Confirm branch 2 (collection modified in loop).** In the source, confirm Delete (or a Move/modify) runs **inside** a `For Each` iterating the live `MailMessage` collection from Get. The `Collection was modified` error from inside the loop confirms the branch — it is a workflow-structure bug, not an Outlook problem.
5. **Confirm branch 3 (New Outlook).** Determine the Outlook client variant on the host and whether a recent update flipped it to **New Outlook**. A complete post-update break with COM-bind failures confirms the branch. (Same surface as [move-outlook-mail-failures.md](./move-outlook-mail-failures.md) branch 4.)
6. **Confirm branch 4 (COM blocked / privilege).** Check whether a modal dialog (programmatic-access warning) could be foregrounded and whether UiPath and Outlook run at the **same privilege level**. A timeout/freeze on an unattended host, or an elevation mismatch, confirms the branch. (Same surface as [send-outlook-mail-failures.md](./send-outlook-mail-failures.md) branch 2 / [get-outlook-mail-failures.md](./get-outlook-mail-failures.md) branch 3.)
7. **Confirm branch 5 (permission / access).** Check whether the target is a **shared mailbox**, whether its address is set in `Account`, and whether the Robot account has **Full Access** (not just Send-As). A delete-denied / access error on a shared folder confirms the branch.

The root cause must name **which of the five surfaces** the failure maps to, with the specific evidence: the exception text, the fetch→delete gap, whether Delete is inside a loop, the Outlook client/session/privilege state, and the `Account` + mailbox rights. A generic "delete failed" is not a confirmed finding.

## Resolution

Map the branch identified in Investigation to the fix:

- **Branch 1 — Stale message reference:**
  - Minimize the time and work between `Get Outlook Mail Messages` and the delete so the item cannot move out from under you; fetch immediately before deleting.
  - Wrap the delete in a `Try Catch` that tolerates an already-moved/already-deleted item (the work is effectively done) rather than faulting the job.
  - If another job/user/rule legitimately competes for the same folder, re-fetch and re-confirm the item before deleting.

- **Branch 2 — Collection modified inside the loop:**
  - Do **not** delete (or otherwise mutate the collection) directly inside a `For Each` over the live `MailMessage` list. Either:
    - iterate over a **copy** — `mailMessages.ToList()` — so deletes do not disturb the enumerator, or
    - loop **backwards by index** so removing an item does not shift the positions still to visit, or
    - inside the loop use **Move Outlook Mail Message** to shift targeted items to `Deleted Items` (or a temp subfolder) and delete them in a second pass after the loop.

- **Branch 3 — New Outlook:**
  - Revert the host's Outlook to **Classic Outlook** so the desktop COM API the activity needs is present again, or
  - migrate the workflow to the modern Microsoft 365 / Graph activities ([o365-activities](../../o365-activities/overview.md)), which delete over a web connection rather than local desktop COM. (Same fix as [move-outlook-mail-failures.md](./move-outlook-mail-failures.md) branch 4.)

- **Branch 4 — COM session blocked / privilege:**
  - Run UiPath (Studio/Robot) and Outlook at the **same privilege level** — ideally both standard user, not Administrator.
  - Resolve the programmatic-access dialog at its source: `Outlook > File > Options > Trust Center > Trust Center Settings > Programmatic Access`, and confirm antivirus is current and registered with Windows Security Center so the "a program is trying to access email" warning does not fire unattended. (Same surface/fix as [send-outlook-mail-failures.md](./send-outlook-mail-failures.md) branch 2.)

- **Branch 5 — Mailbox permission / access:**
  - Set the **shared mailbox address explicitly in the `Account`** property of the mail activities.
  - Have the Exchange administrator grant the Robot's Active Directory account **Full Access** permission (not just Send-As) on the target shared mailbox / folder, so it can read, write, and delete there.

## Anti-patterns (what NOT to do)

- **"Add a Delay before the delete to let things settle."** A delay makes branch 1 *worse* — the longer the gap between fetch and delete, the more likely the item moved. Fetch-then-delete promptly, and handle the already-gone case in a catch.
- **"Wrap the loop-delete in a Try Catch and keep going."** Swallowing the `Collection was modified` error does not fix branch 2 — the enumeration is already broken and remaining items are skipped. Iterate a copy / backwards, or Move-then-delete.
- **"Run UiPath as Administrator so it can delete."** Elevation does not grant mailbox delete rights and usually *breaks* COM via a privilege mismatch (branch 4). Match privilege levels; fix mailbox rights via Exchange (branch 5).
- **"Reinstall Office / downgrade the package after the post-update break."** If the host flipped to New Outlook (branch 3), neither helps — revert to Classic Outlook or move to the Graph activities.

## Prevention (cross-branch)

- Fetch immediately before deleting and guard the delete with a Try Catch for already-moved/deleted items; avoid long gaps and concurrent processing of the same folder (branch 1).
- Never mutate the live `MailMessage` collection inside its own `For Each` — iterate a `.ToList()` copy or backwards by index, or Move-then-delete in a second pass (branch 2).
- Pin Robot hosts to **Classic Outlook** (or move deletes to the Graph o365 activities) so a New-Outlook flip cannot break the COM activities (branch 3).
- Keep UiPath and Outlook at the same privilege level and pre-configure programmatic access / antivirus so no modal dialog blocks unattended runs (branch 4).
- Provision the Robot account with **Full Access** on every shared mailbox it must delete from, and set `Account` to the shared address at design time (branch 5).

## Related

- [get-outlook-mail-failures.md](./get-outlook-mail-failures.md) — the read activity that produces the `MailMessage` items; shares the `Account`/shared-mailbox and COM-session surfaces, and is where the stale-reference window opens.
- [move-outlook-mail-failures.md](./move-outlook-mail-failures.md) — the Move activity (the recommended in-loop alternative to deleting); shares the COM-session and New-Outlook surfaces.
- [send-outlook-mail-failures.md](./send-outlook-mail-failures.md) — shares the COM-blocked / programmatic-access / privilege surface (branch 4 here).
- [o365-activities overview](../../o365-activities/overview.md) — modern Microsoft Graph / OAuth mail delete; the required path on New Outlook and the preferred path for unattended deletes.
- [mail-activities overview](../overview.md) — the package's connection model (Outlook desktop COM vs SMTP/protocol).
