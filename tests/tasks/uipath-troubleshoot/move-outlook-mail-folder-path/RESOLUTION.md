# Final Resolution

---

**Root Cause:** The `Move Outlook Mail Message` activity in `Main.xaml`
has its destination `MailFolder` set to the bare leaf name `"Processed"`.
`Processed` is not a top-level Outlook folder -- it lives **under Inbox**.
The activity resolves `"Processed"` against the mailbox root, finds no
top-level folder by that name, and raises
`The specified folder does not exist.` (`UiPath.Mail.Exception` ->
`System.Exception`). Because the folder string is wrong at design time,
this fails **deterministically, on every run**.

**What went wrong:** The `OrderMailFiler` job (started
2026-06-04T07:20:00Z) faulted ~2 seconds after launch when the
`Move Outlook Mail Message` activity tried to move the source message
into the destination folder. The Outlook desktop COM session attached
cleanly and the source message was resolved in Inbox -- only the
destination folder string failed to resolve.

**Why:** A nested Outlook folder must be addressed by its **path**, not by
its leaf name. `"Processed"` only matches a folder named `Processed`
directly off the mailbox root; the real folder is `Inbox\Processed`. The
job logs make this explicit: the activity logged
`Resolving destination folder 'Processed' against the default profile
root` and then
`destination folder 'Processed' not found at the mailbox root; no such
top-level folder.` The bare leaf name is visible in both `Main.xaml`
(`MailFolder="Processed"`) and the destination-not-found log line.

**This is NOT the other Move Outlook branches:**

- **NOT Branch 1 (COM session loss / Outlook not running).** The COM
  session is fine -- the activity attached to the running Outlook desktop
  session and resolved the source message in Inbox before failing. The
  failure is **deterministic on every run**, not intermittent and not
  unattended-only. Branch 1 hallmarks (works-attended-fails-unattended,
  intermittent drop) are absent.
- **NOT Branch 3 (modern-vs-classic type mismatch).** There is no
  `Cannot convert type 'String' to 'IResource' / 'Office365Message'` cast
  or binding error. The activity is the classic `MoveOutlookMessage` with
  a `MailMessage` input -- no string-into-resource-property mismatch.
- **NOT Branch 4 (New Outlook).** The automation did not "break completely
  after a Windows/Office update," and there is no COM-bind failure. Outlook
  is present and the desktop COM API is working.
- **NOT a missing-message issue.** The source message resolved fine; the
  failure is on the **destination folder** only.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: OrderMailFiler -- Faulted at 2026-06-04T07:20:02.260Z (ran ~2.1 seconds)
- Job type: Unattended, triggered by a scheduled trigger on machine MOCK-HOST
- Folder: RPA Production (key `d9e0f1a2-3b4c-4d5e-8f6a-7b8c9d0e1f2a`)
- Final error: `Move Outlook Mail Message: The specified folder does not exist.` -> `Main.xaml` -> `MoveOutlookMessage "Move Outlook Mail Message"` -> `Sequence "Main Sequence"` -> `Main "Main"`
- Exception: `UiPath.Mail.Exception: The specified folder does not exist. ---> System.Exception`

### Mail Activities (Root Cause)
- Activity: `MoveOutlookMessage` (DisplayName: "Move Outlook Mail Message"), package `UiPath.Mail.Outlook.Activities`
- Destination `MailFolder` (from `Main.xaml`): **`"Processed"`** -- a bare nested-folder leaf name, not a path
- `Account` (from `Main.xaml`): empty (default profile)
- Message input: `mailToFile` (a `MailMessage` variable)
- Job logs confirm the COM session is fine and isolate the failure to the destination folder:
  - `[Move Outlook Mail Message] Attached to the running Outlook desktop session for profile UIPATH\ROBOTUSER1`
  - `[Move Outlook Mail Message] Source message resolved (Subject: 'Order #48217 confirmation') in Inbox`
  - `[Move Outlook Mail Message] Resolving destination folder 'Processed' against the default profile root`
  - `[Move Outlook Mail Message] destination folder 'Processed' not found at the mailbox root; no such top-level folder. The specified folder does not exist.`

---

**Immediate fix:**

In `Main.xaml`, address the destination folder by its **path**, not its
leaf name. The `Processed` folder lives under `Inbox`, so set the
`Move Outlook Mail Message` activity's `MailFolder` property to:

```
Inbox\Processed
```

(`Inbox/Processed` is also accepted.) Save, rebuild, and re-run.

If the destination is actually in a **shared / secondary mailbox** rather
than the default profile, set the activity's **`Account`** field to that
mailbox's primary email address as well, so the path resolves against the
right mailbox root.

No host-side action is required -- this is a workflow configuration bug
fixable entirely in the project source.

---

**Preventive fix:**

1. **Studio** -- address every Outlook destination/source folder by its
   full path (`Inbox\Processed`), never by a bare leaf name, and set
   `Account` for any shared-mailbox target at design time. Validate folder
   strings against the real Outlook folder tree before publishing.
   - **Why:** A bare leaf name silently resolves against the mailbox root
     and fails deterministically once the target is a nested folder.
   - **Who:** RPA developer

2. **Code review / test** -- add a smoke test that runs the mail-filing
   step against a known mailbox so a wrong folder string is caught before
   it reaches Production, rather than at first scheduled run.
   - **Why:** This failure is deterministic and would have been caught by
     a single attended run.
   - **Who:** RPA developer / QA

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Destination `MailFolder="Processed"` is a bare nested-folder leaf name that does not resolve against the mailbox root (move-outlook-mail-failures Branch 2) | High | Confirmed | Yes | `MailFolder="Processed"` in `Main.xaml` + job-log line `destination folder 'Processed' not found at the mailbox root; no such top-level folder` + deterministic fault every run | Set `MailFolder="Inbox\Processed"` (or set `Account` for a shared-mailbox destination) |
| H2 | COM session loss / Outlook not running (Branch 1) | Low | Eliminated | No | Job log shows Outlook attached and the source message resolved before the failure; the fault is deterministic, not intermittent | n/a |

---

Reference playbook:
`references/activity-packages/mail-activities/playbooks/move-outlook-mail-failures.md`
(Branch 2 -- destination folder path / `Account`).

Would you like me to apply the `MailFolder="Inbox\Processed"` change to
`Main.xaml`, or clean up the `.local/investigations/` folder?
