---
confidence: medium
---

# Move Outlook Mail Message Failures

## Context

A `UiPath.Mail.Outlook.Activities` `Move Outlook Mail Message` (`MoveOutlookMessage`) activity moves a `MailMessage` into a destination `MailFolder` of the **locally installed Outlook desktop application** through COM interop — it does not call a mail API. It runs under the Outlook profile of the Windows user the Robot runs as, resolves the destination folder (and optional `Account`), and moves the supplied message item. Failures cluster around the **COM session** (Outlook running/synced, especially unattended), the **destination folder path / `Account`**, a **modern-vs-classic type mismatch** after a package update, and the **New Outlook** client removing the desktop COM API the activity depends on.

Move shares the desktop-COM surface with the other Outlook activities — Outlook-not-running / session-drop is diagnosed like [get-outlook-mail-failures.md](./get-outlook-mail-failures.md) branch 3 and [send-outlook-mail-failures.md](./send-outlook-mail-failures.md) branch 1, and the folder-resolution rules match [get-outlook-mail-failures.md](./get-outlook-mail-failures.md) branch 1. What is distinctive here is the **classic-vs-modern Move activity type mismatch** and the **New Outlook** regression. For unattended / server-side mail with no desktop Outlook, prefer the modern Graph **o365-activities** Move Email.

What this looks like — Move Outlook Mail Message faults surface as one of these signatures:

- `The operation failed.` or `The specified folder does not exist` that is **intermittent**, or fails 100% on **unattended/Production** robots — branch 1.
- `The folder does not exist` that fails **immediately, every run**, in attended testing — branch 2.
- `Cannot convert type 'String' to 'IResource'` / `... to 'Office365Message'` (a design-time/binding/cast error) after a dependency update — branch 3.
- The automation **broke completely after a system/Office update**, with COM-bind / "Outlook is not running" style errors on a machine that now runs **New Outlook** — branch 4.

What can cause it (cause-branches — pick the right one from evidence):

1. **COM session loss (Outlook not running / not synced).** The Robot's COM session cannot reach a live local Outlook instance, so the folder tree cannot be indexed. Causes: Outlook is closed, asleep, or running on a **detached unattended Windows profile**; the connection drops intermittently mid-run. Hallmark: the same workflow that works attended fails on unattended/Production, or fails only on *some* runs.
2. **Destination folder path / `Account` mismatch.** The `MailFolder` string does not resolve. Causes: a **nested** destination addressed by a bare leaf name (`Archive`) instead of a path (`Inbox\Archive`); a **shared / secondary mailbox** destination without the mailbox's address in the `Account` field. Hallmark: fails immediately and deterministically, every run, even attended.
3. **Modern-vs-classic type mismatch.** After updating dependencies, the workflow mixes the **modern** Move Email activity (newer `UiPath.Mail.Activities` / `UiPath.MicrosoftOffice365.Activities`) — which expects an object reference (`IResource` / `Office365Message`) for the message and/or folder — with a **string** message-ID or folder-path variable wired in from the classic design. Surfaces as a `Cannot convert type 'String' to 'IResource' / 'Office365Message'` binding/cast error.
4. **New Outlook (desktop COM API removed).** The host updated to Microsoft's **New Outlook** (the web-hybrid client), which **removes the Outlook Desktop COM API** that all `UiPath.Mail.Outlook.Activities` rely on. The classic activity can no longer bind to an Outlook COM server. Hallmark: the automation worked, then broke **completely** right after a Windows/Office update flipped the machine to New Outlook.

What to look for:

- **The exception text and timing** — intermittent / unattended-only "operation failed" / "folder does not exist" → branch 1; immediate-and-deterministic "folder does not exist" → branch 2; a `String`→`IResource`/`Office365Message` cast/binding error → branch 3; "broke completely after an update" with COM-bind failures → branch 4.
- **Session type and Outlook state** — attended vs unattended/RDP, and whether a desktop Outlook is running/synced for the Robot's user. Load-bearing for branches 1 and 4.
- **The destination `MailFolder` + `Account`** (literal values from `Main.xaml`) — nested path? shared mailbox? Load-bearing for branch 2.
- **Which Move activity and how its inputs are typed** — classic `Move Outlook Mail Message` (`MoveOutlookMessage`, string/`MailMessage` inputs) vs the modern Move Email (`IResource`/`Office365Message`), and whether a `String` is wired where a resource object is expected. Load-bearing for branch 3.
- **Outlook client variant on the host** — Classic Outlook vs New Outlook, and whether a recent update flipped it. Load-bearing for branch 4 (only verifiable on the host).

## Investigation

Go in this order — cheaper checks first.

1. **Capture the exact error, activity, host, and timing.** From `uip or jobs get <job-key> --output json` → `Info`: the exception class and message. From workflow source (`.xaml`): the Move activity — classic `MoveOutlookMessage` vs the modern Move Email, the destination `MailFolder` / `Account`, and how the message and folder inputs are typed (string vs resource). From the job: the Robot **host**, whether the run is **attended or unattended**, and whether failures are **intermittent or 100%**.

2. **Branch the diagnostic on the signature + timing.**
   - Intermittent, or unattended-only, "operation failed" / "folder does not exist" → branch 1; go to step 3.
   - Immediate, deterministic "folder does not exist" → branch 2; go to step 4.
   - `Cannot convert type 'String' to 'IResource' / 'Office365Message'` → branch 3; go to step 5.
   - "Broke completely after an update", COM-bind failure → branch 4; go to step 6.

3. **Confirm branch 1 (COM session loss).** Confirm the run is unattended/RDP and whether a desktop Outlook is running and synced for the Robot's Windows user. Intermittency, or works-attended-fails-unattended, with no folder-path problem, confirms the branch. (Install/registration/bitness is the same surface as [send-outlook-mail-failures.md](./send-outlook-mail-failures.md) branch 1.)

4. **Confirm branch 2 (folder path / `Account`).** Read the literal destination `MailFolder`. A bare nested-folder leaf name (`Archive` instead of `Inbox\Archive`), or a shared-mailbox destination with an empty `Account`, confirms the branch — especially when it fails deterministically on every run, attended included.

5. **Confirm branch 3 (type mismatch).** Identify which Move activity is used and how its message/folder inputs are bound. A `String` variable wired into a modern activity input that expects an `IResource` / `Office365Message` object — surfacing as the cast/convert error after a recent dependency update — confirms the branch.

6. **Confirm branch 4 (New Outlook).** Determine the Outlook client variant on the host and whether a recent update flipped it to **New Outlook**. A complete, post-update break with COM-bind failures on a host now running New Outlook confirms the branch (the desktop COM API the activity needs is gone).

The root cause must name **which of the four surfaces** the failure maps to, with the specific evidence: the exception text and its timing/determinism, the session type and Outlook state, the destination `MailFolder`/`Account`, the activity variant and input typing, and the Outlook client variant. A generic "move failed" is not a confirmed finding.

## Resolution

Map the branch identified in Investigation to the fix:

- **Branch 1 — COM session loss:**
  - Keep a live Outlook instance available to the Robot: leave a foreground Classic Outlook window open on the target machine during the run, and add Outlook to the **Startup apps** for the Robot's Windows user so it launches and syncs on logon.
  - Wrap the move in a **Retry Scope** with a short (2–3 s) delay — intermittent COM sync losses often clear on the second attempt.
  - For unattended/Production reliability, prefer the modern Graph **o365-activities** Move Email (no desktop dependency).

- **Branch 2 — Folder path / `Account`:**
  - Address a nested destination by its path, not a bare leaf name: `Inbox\Archive` (or `Inbox/Archive`), not `Archive`.
  - For a shared / secondary mailbox destination, set the mailbox's full email address in the activity's **`Account`** field.

- **Branch 3 — Modern-vs-classic type mismatch:**
  - In a **modern** Move Email activity, do not hardcode a string message-ID / folder path. Use the **`+` (plus) button** next to the folder/message property to map the target via the directory picker so it resolves to the expected `IResource` / `Office365Message` object.
  - Or, if your variables are explicit `String` / `MailMessage` types, use the **classic** `Move Outlook Mail Message` (`MoveOutlookMessage`) activity, which accepts them directly. Do not mix classic string inputs into modern resource-typed properties.

- **Branch 4 — New Outlook:**
  - Toggle the host's Outlook back to **Classic Outlook** (the switch in the upper-right corner of the Outlook window) so the desktop COM API the activity needs is present again.
  - If the machine must stay on **New Outlook**, stop using the `UiPath.Mail.Outlook.Activities` desktop activities entirely and migrate the workflow to the modern Microsoft 365 Integration activities (**`UiPath.MicrosoftOffice365.Activities`**, covered by [o365-activities](../../o365-activities/overview.md)), which use the Graph API over a web connection rather than local desktop COM.

## Anti-patterns (what NOT to do)

- **"Add a longer Delay / more Retry Scope passes until it works."** Retry helps a genuinely intermittent COM sync loss (branch 1). It will never fix a wrong folder path (branch 2), a type mismatch (branch 3), or a host on New Outlook (branch 4) — it just burns time and masks the real cause.
- **"Wrap Move in a Try Catch and continue."** Swallowing the failure leaves the message unmoved while downstream logic assumes it was filed — a silent data-handling bug. Use Try-Catch only with a real recovery path (retry the transient COM state, route the item, or re-throw).
- **"Force-fit a string into the modern Move Email property."** Hardcoding a string where an `IResource` / `Office365Message` is expected is exactly branch 3 — map the resource with the `+` picker, or use the classic activity.
- **"Reinstall Office / downgrade the package to fix the post-update break."** If the host flipped to New Outlook (branch 4), neither helps — toggle back to Classic Outlook or move to the Graph activities.

## Prevention (cross-branch)

- For unattended / server-side mail moves, default to the modern Graph **o365-activities** Move Email; reserve the classic desktop Move for attended automations with a live, synced Outlook.
- Provision Robot hosts with a running, logged-in Classic Outlook (Startup apps) and pin the machine to **Classic Outlook** so a New-Outlook flip cannot silently break the COM activities.
- Address destination folders by path (`Inbox\Archive`) and set `Account` for shared-mailbox destinations at design time.
- Keep classic and modern Move activities separate — match input types (string/`MailMessage` for classic; `IResource`/`Office365Message` for modern) and re-validate bindings after any `UiPath.Mail.Activities` upgrade.

## Related

- [get-outlook-mail-failures.md](./get-outlook-mail-failures.md) — the inbound read activity; shares the COM-session (branch 3 there) and folder-resolution (branch 1 there) surfaces.
- [send-outlook-mail-failures.md](./send-outlook-mail-failures.md) — the outbound activity; shares the COM-install / not-running / privilege surface (branch 1 there).
- [o365-activities overview](../../o365-activities/overview.md) — modern Microsoft Graph / OAuth mail (Move Email and folder-scoped ops); the required path when the host runs New Outlook and the preferred path for unattended moves.
- [mail-activities overview](../overview.md) — the package's connection model (Outlook desktop COM vs SMTP/protocol).
