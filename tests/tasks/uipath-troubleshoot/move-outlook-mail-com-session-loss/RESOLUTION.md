# Final Resolution

---

**Root Cause:** The `Move Outlook Mail Message` (`MoveOutlookMessage`)
activity in `Main.xaml` moves a `MailMessage` through the locally
installed Classic Outlook desktop application over COM interop. On the
unattended robot (`MOCK-HOST`, running as `UIPATH\ROBOTUSER1`), there
was no live local Outlook instance running and synced for that Windows
profile, so the activity could not bind to a running Outlook COM
server and could not index the destination folder tree. The move
faulted with `Move Outlook Mail Message: The operation failed.` backed
by a `System.Runtime.InteropServices.COMException` indicating the
Outlook COM server was unreachable (`0x800706BA RPC_S_SERVER_UNAVAILABLE`).

This is **Branch 1 (COM session loss)** of the
move-outlook-mail-failures playbook.

**What went wrong:** The `MailboxTriageMover` job (started
2026-06-04T03:00:00Z by a scheduled trigger) faulted ~5 seconds after
launch, on every unattended run. The configured destination
`MailFolder` is `Inbox\Processed` - a well-formed nested path. The job
log shows the run is unattended with no interactive desktop session,
and that the activity could not bind to a running Outlook instance for
`UIPATH\ROBOTUSER1` (no live COM session), so the folder tree could
not be indexed.

**Why:** `UiPath.Mail.Outlook.Activities` activities are desktop COM
clients - they require a live, logged-in, synced Classic Outlook for
the robot's Windows user. An unattended robot on a detached Windows
profile with Outlook closed (or not yet synced) has no COM server to
attach to. The same workflow typically works attended (where a person
has Outlook open) and fails on unattended/Production.

**This is NOT:**

- **NOT Branch 2 (folder path / `Account`).** The destination
  `MailFolder` `Inbox\Processed` is a valid, well-formed nested path,
  and the failure is not a deterministic "folder does not exist" caused
  by a bare leaf name or a shared-mailbox `Account` gap. The smoking
  gun is the COM-bind failure, not folder resolution.
- **NOT Branch 3 (modern-vs-classic type mismatch).** There is no
  `Cannot convert type 'String' to 'IResource' / 'Office365Message'`
  cast/binding error. The classic `MoveOutlookMessage` activity is wired
  to a `MailMessage` variable (`mailToMove`) - the correct input type.
- **NOT Branch 4 (New Outlook).** The host has Classic Outlook
  installed - it simply was not running for the robot user. There is no
  "broke completely after an Office/Windows update flipped to New
  Outlook" signal; this fails because Outlook is not running, not
  because the desktop COM API was removed.
- **NOT a COM library-not-registered / bitness install error**, and
  **NOT a generic SMTP / network error** - the activity uses desktop
  COM, not SMTP, and the binding failure is "no running instance," not
  "class not registered."

---

**Evidence:**

### Orchestrator (Propagation)
- Job: MailboxTriageMover -- Faulted at 2026-06-04T03:00:05.260Z (ran for ~5.1 seconds)
- Job type: Unattended, triggered by a scheduled trigger on machine MOCK-HOST
- Folder: RPA Production (key `b7c8d9e0-1f2a-4b3c-8d4e-5f6a7b8c9d0e`)
- Account: `UIPATH\ROBOTUSER1` / `RobotUser1`
- Final error: `Move Outlook Mail Message: The operation failed.` ->
  `System.Runtime.InteropServices.COMException ... (0x800706BA
  RPC_S_SERVER_UNAVAILABLE) The Outlook COM server could not be reached`
  -> `Main.xaml` -> `MoveOutlookMessage "Move Outlook Mail Message"` ->
  `Sequence "Main Sequence"` -> `Main "Main"`

### Mail Activities (Root Cause)
- Activity: `MoveOutlookMessage` (DisplayName: "Move Outlook Mail Message"), `UiPath.Mail.Activities [1.18.3]`
- Destination `MailFolder` (from `Main.xaml`): `Inbox\Processed` -- a
  valid, well-formed nested path. **Not** the cause.
- `Account`: empty (default profile); `Mail`: `[mailToMove]` (a
  `MailMessage` variable - correct classic input type).
- Job log (smoking gun): `[Move Outlook Mail Message] could not bind to
  a running Outlook instance for UIPATH\ROBOTUSER1 (no live COM
  session); the destination folder tree could not be indexed`, preceded
  by `Running unattended on MOCK-HOST as UIPATH\ROBOTUSER1 (no
  interactive desktop session)`.
- The COM server unreachable on an unattended run with no live Outlook
  is the Branch 1 signature.

---

**Immediate fix:**

The agent could not verify the host's live Outlook state from
Orchestrator alone. Hand the user this host-side check list to run the
next time they are in front of MOCK-HOST under the robot's Windows
user.

### Host-side check list (RPA Production / MOCK-HOST)

1. **Confirm Classic Outlook is running and synced for the robot user.**
   - **What:** Log on to MOCK-HOST as `UIPATH\ROBOTUSER1` (or RDP into
     the unattended session) and check whether Classic Outlook is open,
     signed in, and finished its initial sync. Open it and let it sync
     fully if it is not.
   - **Why:** The move activity binds to a running Outlook COM server.
     No running Outlook = no COM session = "The operation failed."

2. **Keep a live Outlook available to the robot during runs.**
   - **What:** Add Classic Outlook to the **Startup apps** for the
     robot's Windows user so it launches and syncs on logon, and leave a
     foreground Outlook window open on the unattended session.
   - **Why:** Guarantees a live COM server is present when the scheduled
     job runs at 03:00.

3. **Wrap the move in a Retry Scope.**
   - **What:** In `Main.xaml`, wrap `Move Outlook Mail Message` in a
     Retry Scope with a short (2-3 s) delay between attempts.
   - **Why:** Clears intermittent COM sync losses where Outlook is up
     but the session briefly drops mid-run. (This alone will not fix a
     permanently-closed Outlook - pair it with steps 1-2.)

4. **For unattended reliability, migrate to the Graph o365 activities.**
   - **What:** Replace the desktop `Move Outlook Mail Message` with the
     modern Microsoft 365 **Move Email** activity
     (`UiPath.MicrosoftOffice365.Activities`), which uses the Graph API
     over a web connection - no local Outlook or desktop COM required.
   - **Why:** Removes the live-Outlook dependency entirely, which is the
     robust answer for unattended/Production mail moves.

Come back with whether Classic Outlook was running for the robot user
(step 1). If it was closed, steps 1-2 are the fix; if it was open but
the session dropped, step 3; for a permanent unattended fix, step 4.

---

**Preventive fix:**

1. **Studio / Solution design** -- for unattended / server-side mail
   moves, default to the Graph **o365-activities** Move Email; reserve
   the classic desktop `Move Outlook Mail Message` for attended
   automations with a live, synced Outlook.
   - **Why:** Desktop COM has no live Outlook on detached unattended
     profiles - the #1 cause of "works attended, fails unattended."
   - **Who:** RPA developer.

2. **Robot host provisioning** -- provision unattended hosts with a
   running, logged-in Classic Outlook (Startup apps) and pin the machine
   to Classic Outlook so a New-Outlook flip cannot silently break the
   COM activities.
   - **Why:** Guarantees a COM server is present for any desktop Outlook
     activity.
   - **Who:** Platform / robot host team.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | No live local Outlook COM session on the unattended robot (Classic Outlook not running/synced for UIPATH\ROBOTUSER1), so the folder tree could not be indexed (Branch 1) | High | Confirmed (matches playbook signature; needs host-side verification of Outlook state) | Yes (class) | Unattended job, COMException `0x800706BA` "Outlook COM server could not be reached" + job-log "could not bind to a running Outlook instance ... no live COM session" | Keep Outlook running (Startup apps) / Retry Scope / migrate to Graph o365 Move Email |
| H2 | Destination folder path / `Account` mismatch (Branch 2) | Low | Eliminated | No | `MailFolder` is a valid nested path `Inbox\Processed`; error is a COM-bind failure, not "folder does not exist" | n/a |
| H3 | Modern-vs-classic type mismatch (Branch 3) | Low | Eliminated | No | Classic `MoveOutlookMessage` wired to a `MailMessage` var; no `String`->`IResource` cast error | n/a |
| H4 | New Outlook removed the desktop COM API (Branch 4) | Low | Eliminated | No | No post-update "broke completely" signal; Classic Outlook is installed, just not running | n/a |

---

This maps to **Branch 1 (COM session loss)** of
`references/activity-packages/mail-activities/playbooks/move-outlook-mail-failures.md`.

Would you like me to draft the host-check note as a single document you
can hand off, or clean up the `.local/investigations/` folder?
