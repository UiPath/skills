# Final Resolution

---

**Root Cause:** The `Send Outlook Mail Message` (`SendOutlookMail`,
`UiPath.Mail.Outlook.Activities`) activity in `Main.xaml` cannot bind
the Outlook COM server. The activity drives the locally installed
**Outlook desktop application** through COM interop; on the Robot host
that bind fails and surfaces as
`System.InvalidCastException: Unable to cast COM object of type
'Microsoft.Office.Interop.Outlook.ApplicationClass' to interface type
'Microsoft.Office.Interop.Outlook._Application'` with an inner
`COMException: Library not registered. (Exception from HRESULT:
0x8002801D (TYPE_E_LIBNOTREGISTERED))`. The cause is a
**process-vs-Outlook bitness mismatch** - the Robot executor process
is **64-bit** (`targetFramework: "Windows"` in `project.json`) while
the desktop Outlook installed on MOCK-HOST is 32-bit - or a
**corrupted Office registration / type library** (common after a
botched Office update). This is the COM-layer branch (Branch 1) of the
Send Outlook Mail Message failures playbook.

**What went wrong:** The `InvoiceMailer` job (started
2026-06-02T06:15:00Z) faulted ~3 seconds after launch when the
`Send Outlook Mail Message` activity tried to launch / attach to
`OUTLOOK.EXE` and cast the application object to the Outlook Object
Model interface. The cast failed because the Outlook type library is
not registered for the architecture the Robot process runs as.

**Why:** A `SendOutlookMail` activity does not call a mail API - it
binds the Outlook COM server (`OUTLOOK.EXE`) under the Robot's Windows
user and composes the message through the Outlook Object Model. That
bind requires a desktop Outlook whose **bitness matches the Robot
process** and whose type library is correctly registered. A 64-bit
process against a 32-bit-only Outlook (or a corrupted type library)
fails the `QueryInterface` for IID `{00063001-0000-0000-C000-000000000046}`
with `Library not registered` and raises the cast exception. The
`To` / `Subject` / `Body` inputs are all valid literals - they are
**not** the cause; the failure happens before any input is consumed,
while the COM object is being bound.

**Not a sibling branch:** This is NOT Branch 2 (the activity does not
time out or hang on a security prompt / Work Offline state - it fails
fast with a cast exception, not a `TimeoutMS` elapse). This is NOT
Branch 3 (no `NullReferenceException`; `To`, `Subject`, and `Body` are
initialized literals in `Main.xaml`). It is NOT a generic SMTP /
network / credentials error and NOT an invalid mailbox / recipient -
the failure is at the local COM binding, before any message is sent.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: InvoiceMailer -- Faulted at 2026-06-02T06:15:03.470Z (ran ~3.3 seconds)
- Job type: Unattended, triggered by a scheduled trigger on machine MOCK-HOST
- Account: `UIPATH\ROBOTUSER1` / `RobotUser1`
- Folder: RPA Production (key `e1a2b3c4-5d6e-4f7a-8b9c-0d1e2f3a4b5c`)
- Job key / TraceId: `f2b3c4d5-6e7f-4a8b-9c0d-1e2f3a4b5c6d`
- Final error (`jobs get` Info): `Send Outlook Mail Message: Unable to cast COM object of type 'Microsoft.Office.Interop.Outlook.ApplicationClass' to interface type 'Microsoft.Office.Interop.Outlook._Application'. ... Library not registered. (Exception from HRESULT: 0x8002801D (TYPE_E_LIBNOTREGISTERED))` -> `Main.xaml` -> `SendOutlookMail "Send Outlook Mail Message"` -> `Sequence "Main Sequence"` -> `Main "Main"`

### Mail Activities (Root Cause)
- Activity: `SendOutlookMail` (DisplayName: "Send Outlook Mail Message"), package `UiPath.Mail.Outlook.Activities` (dependency `UiPath.Mail.Activities [1.18.3]`)
- Inputs in `Main.xaml`: `To="ap-team@example.com"`, `Subject="Daily Invoice Digest"`, `Body="See attached."` - all valid literals (not the cause)
- `project.json` `targetFramework: "Windows"` -> the Robot executor runs **64-bit**; the job-logs Trace confirms a 64-bit executor process
- Error class `InvalidCastException` to `Microsoft.Office.Interop.Outlook._Application` with inner `COMException: Library not registered` (`0x8002801D TYPE_E_LIBNOTREGISTERED`; `REGDB_E_CLASSNOTREG` is the sibling class-not-registered signature) is the COM dispatcher's signature for "the Outlook type library is not registered for this process architecture." On unattended Robots this is a bitness mismatch or a corrupted Office registration on the host.

---

**Immediate fix:**

The agent cannot verify the host's Outlook install or repair Office
from Orchestrator alone, and the user is off-host. Hand the user this
host-side check list to run the next time they are in front of
MOCK-HOST, under the Robot's Windows user (`UIPATH\ROBOTUSER1`).

### Host-side check list (RPA Production / MOCK-HOST)

1. **Confirm desktop Outlook is installed and note its bitness.**
   - **What:** On MOCK-HOST, open Outlook as `UIPATH\ROBOTUSER1` and
     check `File > Office Account > About Outlook` - it shows "32-bit"
     or "64-bit". Confirm the **desktop** client is installed (a
     webmail-only / account-only setup is not enough).
   - **Why:** The Robot executor is 64-bit. A 32-bit-only Outlook
     against the 64-bit process produces the `Library not registered`
     cast failure.

2. **Match bitness.**
   - **What:** Install (or reinstall) the desktop Office / Outlook whose
     bitness matches the Robot process (64-bit), OR set the project
     compatibility so the process matches the installed Outlook.
   - **Why:** The activity can only bind an Outlook COM server of the
     same architecture as the process.

3. **Run an Office Quick Repair.**
   - **What:** Close BOTH UiPath (Studio/Robot) and Outlook, then
     `Windows Settings > Installed apps > Microsoft Office > Modify >
     Quick Repair`. Restart the host.
   - **Why:** Repairs a corrupted / unregistered Outlook type library
     (common after a botched Office update), which also raises
     `Library not registered`.

4. **Clear orphaned OUTLOOK.EXE.**
   - **What:** In Task Manager (or `Stop-Process -Name OUTLOOK -Force`
     in PowerShell as the Robot's Windows user), kill any `OUTLOOK.EXE`
     instances with no visible window before re-running.
   - **Why:** A prior run that crashed can leave Outlook holding the
     COM server in a bad state, so subsequent runs land on the wedged
     process.

5. **(Recommended) Move off the Outlook desktop dependency for unattended.**
   - **What:** For this unattended process, switch to
     **Send SMTP Mail Message** (`UiPath.Mail.SMTP.Activities`, e.g.
     `smtp.office365.com:587` STARTTLS) or the modern Microsoft Graph
     **o365-activities** (`UiPath.MicrosoftOffice365.Activities`).
   - **Why:** Neither needs a desktop Outlook install or profile, so
     the whole COM/bitness/registration failure class disappears for
     server-side / unattended automation.

Come back with the bitness you found in step 1 (and whether step 3
cleared it). That confirms the specific sub-cause and the final fix.

---

**Preventive fix:**

1. **Robot host provisioning** -- provision every Robot host that uses
   the Outlook activities with a **matching-bitness desktop Outlook**
   and a configured profile for the Robot's Windows user; verify at
   provisioning, not at first failure.
   - **Why:** Bitness mismatch and missing desktop Outlook are the
     top causes of the `Library not registered` cast failure.
   - **Who:** Platform / Robot host team.

2. **Studio** -- for unattended / server-side mail, default to
   **Send SMTP Mail Message** or the modern Graph **o365-activities**;
   reserve the Outlook COM activities for attended desktop automations
   that genuinely need the user's Outlook.
   - **Why:** Removes the desktop Outlook dependency from the failure
     funnel entirely.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `SendOutlookMail` cannot bind the Outlook COM server - bitness mismatch (64-bit process vs 32-bit Outlook) or corrupted Office registration on MOCK-HOST | High | Confirmed (matches Branch 1 signature; needs host-side bitness/repair verification) | Yes (class) | `InvalidCastException` to `_Application` + inner `COMException: Library not registered` `0x8002801D TYPE_E_LIBNOTREGISTERED` + `project.json` `targetFramework "Windows"` (64-bit) | Match Outlook bitness, Quick Repair Office, clear orphan OUTLOOK.EXE; or move to SMTP/Graph |
| H2 | Uninitialized `To`/`Subject`/`Body` input (Branch 3) | Low | Eliminated | No | `To`/`Subject`/`Body` are valid literals in `Main.xaml`; error is a cast, not a `NullReferenceException` | n/a |
| H3 | Security prompt / timeout / Work Offline (Branch 2) | Low | Eliminated | No | Job fails fast (~3s) with a cast exception, not a `TimeoutMS` elapse or hang | n/a |

This maps to the Send Outlook Mail Message failures playbook, Branch 1
(COM cast / library not registered):
`references/activity-packages/mail-activities/playbooks/send-outlook-mail-failures.md`

---

Would you like me to draft the host-check note as a single document you
can hand off, or sketch the Send SMTP Mail Message replacement for the
unattended run?
