# Final Resolution

---

**Root Cause:** The `Get Outlook Mail Messages` activity in `Main.xaml`
reads the desktop Outlook through COM interop, but the job runs
**unattended** on MOCK-HOST as `UIPATH\ROBOTUSER1` and there is **no
running OUTLOOK.EXE** instance in that Windows session for the activity to
attach to (and/or UiPath and Outlook run at mismatched privilege levels,
so Windows blocks the cross-process COM call). The activity cannot bind to
the Outlook COM server and surfaces as
`The Outlook application is not running.` -> inner
`System.Runtime.InteropServices.COMException: The RPC server is
unavailable. (Exception from HRESULT: 0x800706BA)`.

This maps to
`references/activity-packages/mail-activities/playbooks/get-outlook-mail-failures.md`,
**Branch 3 (Outlook not running / COM session broken / privilege
mismatch)**.

**What this is NOT.** This is not Branch 1 (folder not resolved) -- the
`MailFolder="Inbox"` resolves fine and there is no "specified folder does
not exist" error. It is not Branch 2 (timeout on a large folder) -- the
job faulted ~4 s after start with an explicit COM error, not a
`TimeoutMS` elapsed. It is not Branch 4 (malformed `Filter`) -- no
`Filter` is set and there is no filter / zero-results signature. It is not
Branch 5 (Cached Exchange Mode desync) -- that produces missing results
with **no** exception, whereas here the job faulted with a hard error. And
it is **not** a COM **library-not-registered / bitness** install error
(the `Send Outlook Mail` surface, that playbook's Branch 1): Outlook **is**
installed -- it is simply **not running** / blocked for the Robot user.
This is also not an SMTP / network error -- the Outlook COM activity never
touches SMTP.

**What went wrong:** The `QueueMailIntake` job (started
2026-06-03T04:00:00Z) faulted ~4 seconds after launch when the
`Get Outlook Mail Messages` activity tried to attach to Outlook. The run
is **Unattended** (scheduled trigger, no interactive desktop). On an
unattended Robot there is no signed-in user keeping Outlook open, so
unless the automation starts Outlook itself there is no COM server to
attach to.

**Why:** The Outlook desktop COM activities require a **running,
initialized** Outlook in the Robot's own Windows session, at the **same
privilege level** as the Robot process. On unattended hosts this is
fragile: no Outlook is running, or UiPath runs elevated while Outlook (if
started) runs normal (or vice versa) and Windows blocks the two processes
from talking. Either way the bind fails as "Outlook is not running" /
`RPC server unavailable`.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: QueueMailIntake -- Faulted at 2026-06-03T04:00:04.220Z (ran for ~4.1 seconds)
- Job type: **Unattended**, triggered by a **scheduled** trigger on machine MOCK-HOST
- Robot identity: `UIPATH\ROBOTUSER1` (`RobotUser1`)
- Folder: RPA Production (key `e3f4a5b6-7c8d-4e9f-8a0b-1c2d3e4f5a6b`)
- Final error: `Get Outlook Mail Messages: The Outlook application is not running.` -> `Main.xaml` -> `GetOutlookMailMessages "Get Outlook Mail Messages"` -> `Sequence "Main Sequence"` -> `Main "Main"`; inner `System.Runtime.InteropServices.COMException: The RPC server is unavailable. (Exception from HRESULT: 0x800706BA)`

### Mail Activities (Root Cause)
- Activity: `GetOutlookMailMessages` (DisplayName: "Get Outlook Mail Messages"), package `UiPath.Mail.Outlook.Activities`
- Config (from `Main.xaml`): `MailFolder="Inbox"` (valid), `Account=""`, `Top="50"`, `OnlyUnreadMessages="True"`, no `Filter`. The folder string and filter are fine -- the failure is the COM session.
- Job logs (full) carry the smoking gun:
  - Info: `Robot session is running Unattended (no interactive desktop) as UIPATH\ROBOTUSER1 on MOCK-HOST`
  - Info: `[Get Outlook Mail Messages] no running Outlook instance detected for the current Windows session; attempting to attach failed`
  - Warn: `[Get Outlook Mail Messages] could not bind to the Outlook COM server (OUTLOOK.EXE not running for UIPATH\ROBOTUSER1); verify Outlook is started and runs at the same privilege level as the Robot`

---

**Immediate fix:**

The agent could not verify the host Outlook / privilege state from
Orchestrator alone, and the user is off-host. Hand the user this
host-side check list to run the next time they are in front of MOCK-HOST
under the Robot's Windows user.

### Host-side check list (RPA Production / MOCK-HOST, as UIPATH\ROBOTUSER1)

1. **Confirm whether Outlook is running for the Robot's user.**
   - **What:** Sign in as the unattended Robot's Windows user
     (`UIPATH\ROBOTUSER1`) and check Task Manager for a running
     `OUTLOOK.EXE`. On a freshly started unattended session there will be
     none.
   - **Why:** The activity attaches to an existing Outlook COM server; if
     none is running, it fails with "Outlook is not running."

2. **Start Outlook before the activity.**
   - **What:** In the workflow, add a `Start Process` on `outlook.exe`
     (or `Open Application`) immediately before the
     `Get Outlook Mail Messages` activity so a foreground Outlook instance
     and profile exist when the read runs. Confirm the Robot's Windows
     user has a configured Outlook **profile**.
   - **Why:** Guarantees a valid Outlook COM server in the Robot's session.

3. **Match privilege levels (UiPath vs Outlook).**
   - **What:** Verify whether the Robot/Studio process runs **elevated**
     (as Administrator) and whether Outlook runs **normal** (or vice
     versa). Run **both at the same privilege level** -- both elevated or
     both normal.
   - **Why:** A privilege mismatch makes Windows (UIPI) block the
     cross-process COM call, surfacing as "Outlook is not running" /
     `RPC server unavailable`. Do **not** "fix" this by running UiPath as
     Administrator -- that usually creates the mismatch.

4. **Prefer the modern Graph o365-activities for unattended reads.**
   - **What:** Migrate the unattended mail read to the
     `UiPath.MicrosoftOffice365.Activities` (e.g. `Get Newest Email`,
     folder-scoped reads) authenticated via OAuth / Microsoft Graph.
   - **Why:** Graph has **no desktop Outlook dependency** -- no running
     OUTLOOK.EXE, no profile, no privilege coupling -- so it is the
     reliable path for headless / unattended automation.

Come back with whether Outlook was running for the Robot user (step 1)
and the privilege levels of UiPath vs Outlook (step 3). That confirms
whether the fix is "start Outlook first / match privilege" or a migration
to Graph.

---

**Preventive fix:**

1. **Studio** -- for unattended automation, default to the modern Graph
   **o365-activities**; reserve the Outlook desktop COM read for
   **attended** desktop automations that genuinely need the user's
   Outlook.
   - **Why:** Removes the running-Outlook + profile + privilege coupling
     that makes the COM read fragile on unattended Robots.
   - **Who:** RPA developer

2. **Robot host provisioning** -- if the Outlook COM read must stay, keep
   a desktop Outlook **started and signed in** in the Robot's unattended
   session (or have the workflow start it), and keep UiPath and Outlook at
   the **same privilege level**.
   - **Why:** Ensures a valid COM server and an unblocked cross-process
     call at run time.
   - **Who:** Platform / Robot host team.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The unattended Robot has no running Outlook COM session for `UIPATH\ROBOTUSER1` (and/or a UiPath-vs-Outlook privilege mismatch), so `Get Outlook Mail Messages` cannot bind -- Branch 3 | High | Confirmed (matches playbook signature; specific dialog/privilege state needs host verification) | Yes (class) | `The Outlook application is not running.` + inner `COMException RPC server unavailable (0x800706BA)`; Unattended job; job-log "no running Outlook instance detected" / "OUTLOOK.EXE not running for UIPATH\ROBOTUSER1" | Start Outlook before the activity / match privilege levels / migrate to Graph o365 |
| H2 | Folder string / `Filter` problem (Branch 1 / 4) | Low | Eliminated | No | `MailFolder="Inbox"` resolves; no `Filter`; error is COM-session, not "folder does not exist" or a filter error | n/a |
| H3 | COM library-not-registered / bitness install error (Send Outlook Mail surface) | Low | Eliminated | No | Error is "not running" + `RPC server unavailable`, not `REGDB_E_CLASSNOTREG` / cast failure; Outlook is installed | n/a |

> Cross-reference: the COM **install / registration / bitness** surface
> (library not registered, cast failure) is documented in
> `references/activity-packages/mail-activities/playbooks/send-outlook-mail-failures.md`
> Branch 1. This scenario is distinct -- Outlook is installed but the
> **session is not running** / is blocked by privilege.

---

Would you like me to draft the host-check note as a single document you
can hand off, or sketch the Start Process / Graph o365 change for the
workflow?
