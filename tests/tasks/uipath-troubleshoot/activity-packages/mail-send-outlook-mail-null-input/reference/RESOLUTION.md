# Final Resolution

---

**Root Cause:** The `Send Outlook Mail Message` activity in `Main.xaml`
binds its `To` field to the variable `recipient` (`To="[recipient]"`).
`recipient` is declared on the Main Sequence but is **never assigned** -
the upstream step that should have populated it (a config read) is
missing - so it is `Nothing`/null at runtime. When the activity composes
the message it dereferences the null input and raises
`System.NullReferenceException: Object reference not set to an instance
of an object` at `SendOutlookMail`. The empty input is visible in the
job log: a Trace just before the fault records `To='' (empty);
Subject='Welcome'`.

**What went wrong:** The `OnboardingMailer` job (started
2026-06-02T08:45:00Z) faulted ~2 seconds after launch when the
`Send Outlook Mail Message` activity ran with an empty/null `To`. It
fails on every run because the variable is never populated - the
failure is deterministic, not transient.

**Why:** A UiPath String variable that is declared but never assigned
defaults to `Nothing`. The Send Outlook Mail activity dereferences the
recipient input while building the Outlook message item, and a null
recipient produces the `NullReferenceException`. The Log Message
immediately before the Send already shows the empty value
("Preparing welcome mail for recipient: " with nothing after the
colon), and the activity's own Trace shows `To=''`.

**This is NOT the other failure classes for this activity:**

- **NOT Branch 1 (COM cast / library not registered).** The signature
  is a `NullReferenceException`, not
  `System.InvalidCastException`/`COMException` with
  `REGDB_E_CLASSNOTREG` / `TYPE_E_LIBNOTREGISTERED`. Outlook
  install/bitness on the host is irrelevant here.
- **NOT Branch 2 (timeout / hang / security prompt / Work Offline).**
  The job did not hang and did not time out - it faulted cleanly in
  ~2 seconds with an exception, so no Outlook security prompt or
  Work Offline state is involved.
- **NOT an SMTP / network / credentials problem.** This activity drives
  the Outlook desktop client via COM, not an SMTP server; nothing
  network-bound failed.
- **NOT an invalid-recipient problem.** The address is empty/null, not
  malformed or pointing at a non-existent mailbox. "The recipient
  mailbox does not exist" is the wrong conclusion.
- **NOT a host-side fix.** This is a workflow bug in `Main.xaml`,
  fixable in Studio. Nothing on MOCK-HOST needs to change.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: OnboardingMailer -- Faulted at 2026-06-02T08:45:02.190Z (ran for ~2.1 seconds)
- Job type: Unattended, triggered by a scheduled trigger on machine MOCK-HOST
- Account: `UIPATH\ROBOTUSER1` / `RobotUser1`
- Folder: RPA Production (key `c5e6f7a8-9012-4d1e-8f2a-4b5c6d7e8f90`)
- Final error: `System.NullReferenceException: Object reference not set to an instance of an object.` -> `Main.xaml` -> `SendOutlookMail "Send Outlook Mail Message"` -> `Sequence "Main Sequence"` -> `Main "Main"`

### Mail Activities (Root Cause)
- Activity: `SendOutlookMail` (DisplayName: "Send Outlook Mail Message", `UiPath.Mail.Outlook.Activities`)
- `To` (from `Main.xaml`): `[recipient]` - bound to a variable
- `recipient` variable: declared on the Main Sequence (`x:String`), **never assigned** anywhere upstream (no Assign, no config read populates it)
- `Subject`: literal `"Welcome"`; `Body`: bound to `welcomeBody` (which has a default, so it is not the null one)
- Job-log Trace just before the fault: `[Send Outlook Mail Message] preparing message: To='' (empty); Subject='Welcome'; Attachments=0` - the empty `To` is the smoking gun
- The preceding `Log Message` prints `Preparing welcome mail for recipient: ` with nothing after the colon, confirming `recipient` is empty at runtime

---

**Immediate fix (workflow / Studio):**

1. **Populate the `recipient` variable before the Send.**
   - **What:** In `Main.xaml`, add the missing step that assigns
     `recipient` (the intended config read, an Assign, or an input
     argument) so it holds a real email address before the
     `Send Outlook Mail Message` activity runs.
   - **Why:** The activity throws `NullReferenceException` because `To`
     dereferences a null variable. Giving it a value removes the null.

2. **Validate by hardcoding a literal address first.**
   - **What:** Temporarily set the `To` field to a literal address
     (e.g. `"someone@test.com"`), rebuild, and re-run. If the
     `NullReferenceException` disappears, the null `To` input is
     confirmed as the cause.
   - **Revert:** Restore the expression-bound `To` once the upstream
     assignment is in place.

3. **Guard the inputs.**
   - **What:** Before the Send, add a guard (an If / validation) that
     fails fast with a clear message when `recipient` (or Subject/Body)
     is empty, rather than letting the activity throw an opaque
     `NullReferenceException`.
   - **Why:** Turns a cryptic null dereference into an actionable error.

---

**Preventive fix:**

1. **Studio** -- initialize and validate every variable bound to `To`,
   `Subject`, and `Body` before the Send Outlook Mail Message activity;
   never bind an input field to a variable that has no guaranteed
   producer.
   - **Why:** A null `To` is the most common Branch 3 cause.
   - **Who:** RPA developer.

2. **Studio** -- when a value comes from config/an upstream read, assert
   it is non-empty right after the read so the failure points at the
   missing config, not at the mail activity 30 lines later.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `Send Outlook Mail Message` threw `NullReferenceException` because `To` is bound to `recipient`, a variable declared but never assigned (null input) | High | Confirmed | Yes | `NullReferenceException` at `SendOutlookMail` in job Info; `Main.xaml` `To="[recipient]"` with `recipient` never assigned; job-log Trace `To='' (empty)` | Assign/populate `recipient` (or guard) before the Send; validate by hardcoding a literal address |
| H2 | COM cast / Outlook-not-registered or bitness mismatch (Branch 1) | Low | Eliminated | No | Signature is `NullReferenceException`, not `InvalidCastException`/`COMException` | n/a |
| H3 | Timeout / hidden security prompt / Work Offline (Branch 2) | Low | Eliminated | No | Job faulted cleanly in ~2s with an exception; no hang or timeout | n/a |

---

This maps to
`references/activity-packages/mail-activities/playbooks/send-outlook-mail-failures.md`
(Branch 3 - Uninitialized input).

Would you like me to draft the Studio fix as a single change note you
can hand to the developer, or clean up the `.local/investigations/`
folder?
