# Final Resolution

---

**Root Cause:** The `Send Outlook Mail Message` activity in `Main.xaml`
drives the Outlook desktop client through COM interop. On the
unattended Robot session (machine `MOCK-HOST`, account
`UIPATH\ROBOTUSER1`), the send call triggered the Outlook Object Model
Guard security prompt -- "A program is trying to send an email message
on your behalf" -- which was foregrounded but invisible and awaiting
input. With no interactive user present on the unattended session to
dismiss it, the COM call blocked until the activity's `TimeoutMS`
(30000 ms) elapsed, and the job faulted with
`System.TimeoutException: The operation has timed out.`

This maps to:
`references/activity-packages/mail-activities/playbooks/send-outlook-mail-failures.md`
-- specifically **Branch 2 ("Activity times out or hangs")**, the
hidden-security-prompt sub-cause. **Work Offline** on the Robot's
Outlook profile is the sibling sub-cause that produces the same
signature and is ruled in/out by the same host-side checks below.

**What went wrong:** The `NightlyReportMailer` job (started
2026-06-02T02:30:00Z) launched Outlook, loaded the profile, began
composing the message, then hung. The job-logs show a `Warn` at
~+26 s -- "Outlook is not responding to the send request; the call has
been pending for >25s (an interactive prompt may be awaiting input on a
non-interactive session)" -- and faulted ~30 s after the Send step
started, exactly at `TimeoutMS`.

**Why this is NOT another branch:**

- **NOT Branch 1 (COM cast / library not registered).** There is no
  `InvalidCastException` / `COMException` / `Library not registered`
  (`REGDB_E_CLASSNOTREG` / `TYPE_E_LIBNOTREGISTERED`). Outlook launched
  and the profile loaded (Info logs confirm), so the COM server bound
  fine. The failure is a clean timeout, not a cast.
- **NOT Branch 3 (uninitialized input).** `To`, `Subject`, and `Body`
  are literals in `Main.xaml` (`reports-dl@test.com`, "Nightly Report
  Summary", a literal body). There is no `NullReferenceException`.
- **NOT merely a timeout to be bumped.** Raising `TimeoutMS` does not
  clear a blocking security prompt -- it only makes the Robot hang
  longer before failing. The send was blocked on input that will never
  arrive on an unattended session, not on a legitimately slow send.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: NightlyReportMailer -- Faulted at 2026-06-02T02:30:30.620Z (ran
  ~30.5 seconds, the full `TimeoutMS` window)
- Job type: Unattended, triggered by a scheduled (nightly) trigger on
  machine `MOCK-HOST`, account `UIPATH\ROBOTUSER1`
- Folder: RPA Production (key `a3c4d5e6-7f80-4b9c-8d0e-2f3a4b5c6d7e`)
- Job key / TraceId: `b4d5e6f7-8091-4c0d-9e1f-3a4b5c6d7e8f`
- Final error: `Send Outlook Mail Message: Timeout reached. (30000 ms)`
  / `System.TimeoutException: The operation has timed out.` ->
  `Main.xaml` -> `SendOutlookMail "Send Outlook Mail Message"` ->
  `Sequence "Main Sequence"` -> `Main "Main"`

### Job logs (smoking gun)
- Info: Outlook launched under `UIPATH\ROBOTUSER1`; profile loaded;
  message composing to `reports-dl@test.com`.
- **Warn (~+26 s):** "[Send Outlook Mail Message] Outlook is not
  responding to the send request; the call has been pending for >25s
  (an interactive prompt may be awaiting input on a non-interactive
  session)" -- the call blocked while something off-screen waited for
  input.
- Error (~+30 s): timeout reached at exactly `TimeoutMS`.

### Mail Activities (Root Cause)
- Activity: `SendOutlookMail` (DisplayName: "Send Outlook Mail
  Message", `UiPath.Mail.Outlook.Activities`)
- `To` / `Subject` / `Body` (from `Main.xaml`): literals -- inputs are
  fine, ruling out Branch 3.
- `TimeoutMS` (from `Main.xaml`): `30000` (30 s) -- matches the observed
  ~30 s hang-to-fault exactly.
- Outlook COM activities drive the desktop client through the Outlook
  Object Model. The Object Model Guard prompt fires when antivirus is
  out of date / not registered with Windows Security Center, or
  programmatic access is not policy-allowed. On an unattended session
  the prompt is invisible and unanswerable -> the call blocks until
  `TimeoutMS`.

---

**Immediate fix:**

The agent could not see the Robot's interactive desktop or Outlook
state from Orchestrator alone. Hand the user this host-side check list
to run the next time they are in front of `MOCK-HOST`, under the
Robot's Windows user (`UIPATH\ROBOTUSER1`).

### Host-side check list (RPA Production / MOCK-HOST)

1. **Confirm a configured Outlook profile exists for the Robot user.**
   - **What:** Log in (or run an attended test) as `UIPATH\ROBOTUSER1`,
     open Outlook, and confirm a mail profile is configured and signed
     in.
   - **Why:** The COM activity composes through the Robot user's own
     profile. No profile -> the send never completes.

2. **Turn off Work Offline.**
   - **What:** In Outlook (as the Robot user), check
     `Send/Receive > Work Offline`. Ensure Outlook is **Online**.
   - **Why:** In Work Offline the message is queued but never sent, so
     the activity blocks until `TimeoutMS` -- the same signature as the
     security prompt. This is the sibling sub-cause to rule out first.

3. **Stop the Object Model Guard security prompt at its source.**
   - **What:** Keep antivirus current and **registered with Windows
     Security Center** (this is what normally suppresses the "a program
     is trying to send an email on your behalf" prompt). If AV cannot be
     registered, set the Outlook **programmatic-access / Trust Center**
     policy via Group Policy for the Robot's Windows user.
   - **Why:** The Object Model Guard fires this modal prompt; on an
     unattended session no one dismisses it and the send blocks until
     timeout. Do NOT rely on a human clicking the prompt.
   - **Do NOT** manually set Programmatic Access to "Never warn me" on
     each host -- it is brittle and a security regression; the supported
     path is up-to-date registered AV or the GPO.

4. **Switch to SMTP or modern Graph for unattended mail (recommended).**
   - **What:** Replace `Send Outlook Mail Message` with
     **Send SMTP Mail Message** (`UiPath.Mail.SMTP.Activities`; e.g.
     `smtp.office365.com` port `587` STARTTLS) or the modern Graph
     **o365-activities** (`UiPath.MicrosoftOffice365.Activities`,
     OAuth).
   - **Why:** Both bypass the Outlook desktop dependency entirely -- no
     profile, no Object Model Guard, no interactive prompt. This is the
     durable fix for an unattended nightly process.

Come back with the results of steps 1-3 (does a profile exist, is
Outlook Online, did the prompt appear in an attended test run). That
confirms which sub-cause was blocking the send. For a permanent
unattended fix, step 4 is preferred.

> Note: these are checks for you to run on the host -- the agent did not
> and cannot perform them from Orchestrator.

---

**Preventive fix:**

1. **Studio / design** -- for unattended / server-side mail, default to
   **Send SMTP Mail Message** or the Graph **o365-activities**. Reserve
   the Outlook COM activities for attended desktop automations that
   genuinely need the user's Outlook.
   - **Why:** Outlook COM activities are fragile on unattended Robots --
     hidden prompts and missing profiles are the #1 cause of timeout/
     hang faults.
   - **Who:** RPA developer.

2. **Robot host provisioning** -- keep antivirus current and registered
   with Windows Security Center (or set the programmatic-access Group
   Policy), and provision a configured Outlook profile for the Robot's
   Windows user, before first run.
   - **Why:** Removes the Object Model Guard prompt and the missing-
     profile failures from the funnel.
   - **Who:** Platform / robot host team.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | A hidden Outlook Object Model Guard security prompt ("a program is trying to send an email on your behalf") is awaiting input on the unattended session, blocking the COM send until `TimeoutMS` | High | Confirmed (matches Branch 2 signature; needs host-side verification of the specific blocker) | Yes (class) | `System.TimeoutException` at `SendOutlookMail` + ~30 s hang matching `TimeoutMS=30000` + job-log Warn "an interactive prompt may be awaiting input on a non-interactive session" + Unattended job type | Stop the prompt at its source (AV registered with Security Center / programmatic-access GPO); ensure Outlook Online; switch to SMTP/Graph for unattended |
| H2 | Outlook is in Work Offline mode under the Robot's profile, so the send is queued but never completes | Medium | Pending - needs host check | Possible (sibling) | Same timeout signature; no Orchestrator evidence either way (host not accessible) | Turn off `Send/Receive > Work Offline` under the Robot user |

---

Would you like me to draft the host-check note as a single document you
can hand off, or sketch the swap from `Send Outlook Mail Message` to
`Send SMTP Mail Message` for the unattended schedule?
