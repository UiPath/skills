# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** **The `Get Outlook Mail Messages` activity reads the `Invoices` folder that lives in a
shared mailbox (`accounts-payable@test.com`), but its `Account` field is blank — so the activity
resolves the folder against the Robot's default profile store only, where `Invoices` does not exist, and
raises `The specified folder does not exist`.** This is the **shared-mailbox / `Account` omission**
sub-cause of `get-outlook-mail-failures.md` **Branch 1 (Folder not resolved)** — NOT a folder typo,
nested-path syntax, or localized-name problem, and NOT a COM/session, timeout, or filter fault.

The `MailFolder` name is correct and the folder genuinely exists — just not in the default mailbox. With
`Account` empty, `Get Outlook Mail Messages` only searches the default profile store; to read a folder
in a secondary/shared mailbox you must name that mailbox's primary SMTP address in `Account`.

**What went wrong:** The `PayablesInvoiceReader` job faulted ~2 s after launch. The job logs show the
activity attached to a running Outlook instance, then `No Account specified; resolving folder 'Invoices'
against the default profile store (robotuser1@test.com)`, then `Could not find folder 'Invoices' under
the default profile store ...; stores available to this profile: robotuser1@test.com,
accounts-payable@test.com`, then `The specified folder does not exist`. The shared
`accounts-payable@test.com` store IS attached to the profile — but the activity never looked in it
because `Account` was blank.

**Why — and why it is NOT another branch / sub-cause:**

- **NOT the nested-path / folder-name sub-cause of Branch 1.** `MailFolder` is a plain top-level name
  (`Invoices`), not a backslash path (`Inbox\Invoices`) and not a localized name. The folder exists; it
  is simply in a different store. The fix is `Account`, not the folder string.
- **NOT Branch 2 (timeout on a large folder).** The job ran ~2 s and the error is `specified folder does
  not exist`, not `The operation has timed out`; enumeration never began.
- **NOT Branch 3 (Outlook not running / COM / privilege).** The logs show the activity attached to a
  running Outlook instance; no `Outlook is not running`, no COM cast, no hang.
- **NOT Branch 4 (malformed `Filter`).** No `Filter` is set; the error is folder resolution, not DASL/Jet
  syntax or a zero-results-with-filter symptom.
- **NOT Branch 5 (Cached Exchange Mode desync).** That is a no-error / missing-results symptom; here the
  activity throws a hard `folder does not exist`.

**Evidence:**
- Job `c3d4e5f6-7081-4a92-9b3c-4d5e6f708293` (folder RPA Production, machine `MOCK-HOST`, account
  `UIPATH\ROBOTUSER1`) `State = Faulted`; `Info` / Error: `UiPath.Mail.Exception: The specified folder
  does not exist.` at `GetOutlookMailMessages`.
- Job logs: `No Account specified; resolving folder 'Invoices' against the default profile store
  (robotuser1@test.com)` → `Could not find folder 'Invoices' under the default profile store ...; stores
  available to this profile: robotuser1@test.com, accounts-payable@test.com`.
- Source (`Main.xaml`): `GetOutlookMailMessages` with `Account=""` and `MailFolder="Invoices"` (a plain
  name, no backslash, no `Filter`).

**Immediate fix:**
1. Set the shared mailbox's primary SMTP address in the activity's **`Account`** property:
   `Account = "accounts-payable@test.com"`. This scopes the folder lookup to the shared store where
   `Invoices` actually lives.
2. Confirm the Robot's Outlook profile has the shared mailbox added and that the Robot user has at least
   Reviewer/Read permission on the `Invoices` folder (the logs show the store is attached; verify folder
   access).
3. Re-run — with `Account` set, the activity resolves `accounts-payable@test.com\Invoices` and reads the
   messages.

**Do NOT** change the `MailFolder` string, add a backslash path, or "recreate" the folder — the folder
name is correct; only the mailbox scope (`Account`) is missing. Do NOT chase a COM/session, timeout, or
filter cause.

**Preventive fix:**
- Whenever a workflow reads from a shared/secondary mailbox, always set `Account` to that mailbox's SMTP
  address; leaving it blank silently scopes every folder lookup to the default profile.
- For unattended runs against a shared mailbox, prefer the modern Graph **o365-activities** (application
  permissions on the shared mailbox) over desktop Outlook COM — no profile / attached-store dependency.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The `Invoices` folder is in the shared `accounts-payable@test.com` mailbox, but `Account` is blank, so the activity resolves it against the default profile store and cannot find it. | High | Confirmed | Yes | `Account=""` + `MailFolder="Invoices"` in source; logs `No Account specified; resolving ... default profile store` / `stores available: robotuser1@test.com, accounts-payable@test.com`; `The specified folder does not exist`. | Set `Account = "accounts-payable@test.com"`; verify shared-mailbox folder permission. |
| H2 | Nested-path / typo / localized folder name (the other Branch-1 sub-cause). | Low | Eliminated | No | `MailFolder` is a plain `Invoices` (no backslash, no localization); the folder exists in the shared store — the string is correct. | N/A |
| H3 | Timeout / COM-session / filter (Branches 2–4). | Low | Eliminated | No | ~2 s run; attached to Outlook; no timeout, no COM cast, no `Filter`. | N/A |
