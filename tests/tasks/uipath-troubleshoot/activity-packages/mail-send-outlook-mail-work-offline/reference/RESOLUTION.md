# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** **Outlook is in Work Offline mode under the Robot's profile, so `Send Outlook Mail
Message` queues the item into the Outbox but the send never completes — the COM call blocks until
`TimeoutMS` (30000 ms) elapses and the job faults with `System.TimeoutException`.** This is the **Work
Offline** sub-cause of `send-outlook-mail-failures.md` **Branch 2 ("Activity times out or hangs")** —
NOT the hidden Object Model Guard security-prompt sub-cause, and NOT a genuinely slow send to be fixed
by raising the timeout.

The `Send Outlook Mail Message` activity drives the desktop Outlook client through COM under the
Robot's Windows user (`UIPATH\ROBOTUSER1` on `MOCK-HOST`). When Outlook is set to Work Offline, `Send`
deposits the message in the Outbox and returns nothing to transmit against; the activity waits for a
completion that never comes and times out.

**What went wrong:** The `NightlyStatementMailer` unattended job launched Outlook, loaded the profile,
composed the message, and **placed it in the Outbox** — then hung. Job logs show `item placed in the
Outbox for sending`, then a Warn at ~+26 s: `The item is still in the Outbox and has not been
transmitted; Outlook connectivity state reports Disconnected ... (no dialog or prompt was raised)`, then
a timeout Error at exactly `TimeoutMS`. The user's attended re-run on the same host confirms it: **no
prompt or dialog appeared**, and the email was **left sitting unsent in the Outbox**.

**Why this is NOT another branch / sub-cause:**

- **NOT the security-prompt sub-cause (the sibling of this branch).** The Object Model Guard prompt
  fingerprint is a modal awaiting input; here **no dialog or prompt was raised** (log Warn + the user's
  attended test), and the message is **queued in the Outbox** — the offline signature, not a blocked
  prompt. Registering AV / setting the programmatic-access GPO would not fix an offline mailbox.
- **NOT Branch 1 (COM cast / library not registered).** There is no `InvalidCastException` /
  `COMException` / `Library not registered`. Outlook launched and the profile loaded, so the COM server
  bound fine — it is a clean timeout after the item reached the Outbox.
- **NOT Branch 3 (uninitialized input).** `To` / `Subject` / `Body` are literals in `Main.xaml`
  (`statements-dl@test.com`, "Nightly Account Statement", a literal body). There is no
  `NullReferenceException`.
- **NOT merely a timeout to bump.** Raising `TimeoutMS` only makes the Robot hang longer — an offline
  Outlook never transmits the Outbox item during the activity call.

**Evidence:**
- Job `d1e2f3a4-5b6c-4d7e-9f80-1a2b3c4d5e6f` (folder RPA Production, machine `MOCK-HOST`, account
  `UIPATH\ROBOTUSER1`) `State = Faulted` after ~30.5 s (the full `TimeoutMS` window); Unattended,
  Schedule-triggered. Final error: `Send Outlook Mail Message: Timeout reached. (30000 ms) ... item into
  the Outbox but did not transmit it` / `System.TimeoutException: The operation has timed out.`
- Job logs: Info `item placed in the Outbox for sending`; Warn `still in the Outbox and has not been
  transmitted; Outlook connectivity state reports Disconnected ... (no dialog or prompt was raised)`.
- User's attended test on the host: no popup appeared; the email ended up unsent in the Outbox.
- Source: `SendOutlookMail` with literal `To`/`Subject`/`Body` and `TimeoutMS=30000` — rules out
  Branch 1 and Branch 3.

**Immediate fix:**

The Robot's interactive desktop / Outlook state is not visible from Orchestrator. Hand the user this
host-side check list (run on `MOCK-HOST`, under `UIPATH\ROBOTUSER1`):

1. **Turn off Work Offline.** In Outlook, `Send/Receive > Work Offline` — ensure the toggle is OFF and
   the status bar reads **Connected**, not "Working Offline". This is the direct fix: an offline profile
   queues to the Outbox and never sends during the activity call.
2. **Confirm the profile actually connects.** Verify the Robot user's Outlook profile signs in and
   reaches the mail server (not stuck "Disconnected / Trying to connect"). A profile that cannot connect
   behaves the same as an explicit Work Offline toggle.
3. **Flush the Outbox** once online — the queued nightly messages will send; delete duplicates if the
   job retried.
4. **Durable unattended fix (recommended):** replace `Send Outlook Mail Message` with **Send SMTP Mail
   Message** (`UiPath.Mail.SMTP.Activities`; e.g. `smtp.office365.com:587` STARTTLS) or the modern Graph
   **o365-activities** (`UiPath.MicrosoftOffice365.Activities`, OAuth). Both bypass the desktop Outlook
   client entirely — no profile, no online/offline state, no Outbox — which is the right model for an
   unattended nightly process.

> Note: these are checks for you to run on the host — the agent did not and cannot perform them from
> Orchestrator. Do NOT simply raise `TimeoutMS`; an offline mailbox will not transmit within the call.

**Preventive fix:**
- For unattended / server-side mail, default to **Send SMTP Mail Message** or Graph **o365-activities**;
  reserve the Outlook COM activities for attended desktop automations that genuinely need the user's
  Outlook. (Outlook-desktop dependence is the top cause of timeout/hang faults on unattended Robots.)
- If desktop Outlook must be used, provision the Robot user's profile to stay Online (no Work Offline,
  cached-mode connectivity verified) as part of host provisioning, and monitor the Outbox depth.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Outlook is in Work Offline mode under the Robot's profile, so the send is queued to the Outbox but never transmitted, blocking the COM call until `TimeoutMS`. | High | Confirmed (Branch 2, Work Offline sub-cause; host-side verification of the toggle recommended) | Yes | `System.TimeoutException` at `SendOutlookMail` + ~30 s hang matching `TimeoutMS=30000` + log `item placed in the Outbox` / `still in the Outbox ... Disconnected ... no dialog or prompt was raised` + user's attended test (no popup, mail left in Outbox). | Turn off `Send/Receive > Work Offline`, confirm the profile connects Online, flush the Outbox; move to SMTP/Graph for the unattended schedule. |
| H2 | A hidden Object Model Guard security prompt is blocking the send (the sibling sub-cause). | Medium | Eliminated | No | Log explicitly notes **no dialog or prompt was raised**, and the attended test showed no popup; the item sits in the Outbox — the offline signature, not a blocked modal. | N/A — AV/Security-Center registration or programmatic-access GPO would not fix an offline mailbox. |
| H3 | COM cast / library not registered (Branch 1). | Low | Eliminated | No | Outlook launched and the profile loaded; no `InvalidCastException`/`COMException`/`Library not registered`. | N/A |
| H4 | Uninitialized `To`/`Subject`/`Body` (Branch 3). | Low | Eliminated | No | All three are literals in `Main.xaml`; no `NullReferenceException`. | N/A |
