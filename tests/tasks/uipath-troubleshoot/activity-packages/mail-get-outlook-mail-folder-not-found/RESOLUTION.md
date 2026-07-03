# Final Resolution

---

**Root Cause:** The `Get Outlook Mail Messages` activity in `Main.xaml`
is configured with `MailFolder="Inbox\Invoices"` -- a backslash nested
folder path. That syntax does not resolve to a real Outlook folder on
the project's Mail-package version (`UiPath.Mail.Activities [1.18.3]`),
so the activity raises `The specified folder does not exist.` and the
job faults. The Outlook COM session itself is healthy: the activity
attached to the running Outlook instance and the default profile before
it ever tried to resolve the folder. Only the folder string is wrong.

This maps to:
`references/activity-packages/mail-activities/playbooks/get-outlook-mail-failures.md`
-- Branch 1 (Folder not resolved).

**What went wrong:** The `InvoiceMailReader` job (started
2026-06-03T07:10:00Z) faulted ~2 seconds after launch. The job logs
show the activity attached to Outlook successfully, then logged
`resolving folder path 'Inbox\Invoices' against the default profile`,
then `could not resolve folder 'Inbox\Invoices' under the default
profile`, and finally `The specified folder does not exist.` The
failure is deterministic -- it fires on every run because the folder
string is statically wrong, not because of any transient runtime
condition.

**Why -- and why it is NOT the other branches:**

- **Not Branch 2 (timeout on a large folder).** The job ran for ~2
  seconds and the error is `specified folder does not exist`, not `The
  operation has timed out`. The activity never began enumerating
  messages.
- **Not Branch 3 (Outlook not running / COM cast / privilege).** The
  logs show the activity attached to a running Outlook instance for the
  default profile. There is no `Outlook is not running` message, no COM
  cast failure, and no hang -- the COM session is fine.
- **Not Branch 4 (malformed Filter).** No `Filter` is set on the
  activity, and the error is a folder-resolution failure, not a DASL/Jet
  syntax error or a zero-results-with-a-filter symptom.
- **Not Branch 5 (Cached Exchange Mode desync).** That branch produces
  *no error* with missing results; here the job faults with an explicit
  exception.
- **Not a COM / connectivity issue and not "the mailbox/account is
  wrong."** The mailbox attached cleanly under the default profile; the
  fault is purely the `MailFolder` string.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: InvoiceMailReader -- Faulted at 2026-06-03T07:10:02.260Z (ran for ~2.1 seconds)
- Job type: Unattended, triggered by a scheduled trigger on machine MOCK-HOST
- Robot identity: `UIPATH\ROBOTUSER1` / `RobotUser1`
- Folder: RPA Production (key `e7f8a9b0-1c2d-4e3f-8a4b-5c6d7e8f9012`)
- Job key / TraceId: `f8a9b0c1-2d3e-4f4a-9b5c-6d7e8f901234`
- Final error: `Get Outlook Mail Messages: The specified folder does not exist.` -> `UiPath.Mail.Exception` -> `Main.xaml` -> `GetOutlookMailMessages "Get Outlook Mail Messages"` -> `Sequence "Main Sequence"` -> `Main "Main"`

### Mail Activities (Root Cause)
- Activity: `GetOutlookMailMessages` (DisplayName: "Get Outlook Mail Messages"), package `UiPath.Mail.Activities [1.18.3]`
- `MailFolder` (from `Main.xaml`): `Inbox\Invoices` -- a **backslash nested folder path**
- `Account`: empty (default Outlook profile)
- `Top`: `50`; `OnlyUnreadMessages`: `False`
- Job logs show the COM attach succeeded, then folder resolution of
  `'Inbox\Invoices'` against the default profile failed:
  `[Get Outlook Mail Messages] could not resolve folder 'Inbox\Invoices' under the default profile`.
- The backslash nested-path syntax does not resolve on this Mail-package
  version. Branch 1 of the playbook documents this exact failure mode.

---

**Immediate fix:**

Change how the nested folder is addressed in `Main.xaml`. Pick one:

1. **Use the absolute path form (recommended).** Set
   `MailFolder` to `\\<account>\Inbox\Invoices` -- e.g.
   `\\robotuser1@your-domain.com\Inbox\Invoices` using the mailbox's
   primary SMTP address. The absolute form resolves reliably where the
   bare `Inbox\Invoices` backslash path does not.
2. **Target the top-level folder.** If the messages can be read from
   `Inbox` directly, set `MailFolder="Inbox"` and narrow the result with
   a `Filter` / `Top` instead of descending into the subfolder.
3. **If `Invoices` lives under a shared / generic mailbox**, set that
   mailbox's primary address in the **`Account`** field (leaving
   `Account` blank uses only the default profile, which does not see the
   shared box's subfolders).

Then rebuild, republish, and re-run the process from Orchestrator to
confirm the job no longer faults.

---

**Preventive fix:**

1. **Studio** -- address Outlook subfolders with the absolute
   `\\account\Inbox\Sub` form (and set `Account` for shared mailboxes)
   at design time, rather than the bare backslash path. Keep folder
   names in the exact Outlook UI language.
   - **Why:** The bare nested-path syntax silently fails on some
     Mail-package versions; the absolute form is version-stable.
   - **Who:** RPA developer.

2. **Validation** -- before shipping, run the activity once against the
   target profile to confirm the folder resolves, instead of discovering
   the mismatch at first production run.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `MailFolder="Inbox\Invoices"` (backslash nested path) does not resolve, so Get Outlook Mail Messages raises "The specified folder does not exist." (Branch 1) | High | Confirmed | Yes | Job `Info` + job logs: `could not resolve folder 'Inbox\Invoices' under the default profile` -> `The specified folder does not exist.`; `MailFolder="Inbox\Invoices"` in `Main.xaml` | Use absolute path `\\<account>\Inbox\Invoices`, or target top-level `Inbox`, or set `Account` for a shared mailbox |
| H2 | Outlook COM session broken / Outlook not running (Branch 3) | Low | Eliminated | No | Logs show successful attach to the running Outlook instance for the default profile; no COM cast error, no hang | n/a |

---

Would you like me to apply the absolute-path fix to `Main.xaml`, or
draft the change as a hand-off note for the RPA developer?
