# Get Outlook Mail Messages — Shared Mailbox / Account Omission (Branch 1)

Runtime troubleshooting scenario for `UiPath.Mail.Outlook.Activities` `Get Outlook Mail Messages`
(`GetOutlookMailMessages`), covering the **shared-mailbox / `Account` omission** sub-cause of
`get-outlook-mail-failures.md` **Branch 1 (Folder not resolved)**.

## What this scenario exercises

An unattended job faults with `UiPath.Mail.Exception: The specified folder does not exist`. The
`MailFolder` (`Invoices`) is a plain, correct folder name — but it lives in a **shared mailbox**
(`accounts-payable@test.com`), and the activity's **`Account` field is blank**, so the lookup is scoped
to the Robot's default profile store where `Invoices` does not exist. The agent must attribute the
failure to the missing `Account` (shared-mailbox scope) and prescribe setting
`Account = "accounts-payable@test.com"` — NOT changing the folder string, and NOT a COM/session,
timeout, or filter cause.

## The discriminator vs the folder-not-found sibling

Branch 1 (Folder not resolved) has multiple sub-causes. This scenario is distinguished from
`mail-get-outlook-mail-folder-not-found` (which pins the **nested backslash path** `Inbox\Invoices`) by:

- `MailFolder` is a **plain top-level name** (`Invoices`) — no backslash, no localization; the folder
  genuinely exists.
- Source has `Account=""`, and the job logs show `No Account specified; resolving folder 'Invoices'
  against the default profile store (robotuser1@test.com)` → `Could not find folder ...; stores available
  to this profile: robotuser1@test.com, accounts-payable@test.com`.

The smoking gun is that the shared `accounts-payable@test.com` store IS attached to the profile but was
never searched, because `Account` was blank — the fix is `Account`, not the folder string.

## Sibling comparison (same playbook, Branch 1)

| Sub-cause | Signature | This scenario? |
|---|---|---|
| Nested backslash path (`Inbox\Invoices`) | `folder does not exist`; resolved against default profile | No — `mail-get-outlook-mail-folder-not-found` |
| **Shared mailbox, `Account` blank** | **`folder does not exist`; folder is in a shared store the lookup never searched** | **Yes** |
| Localized folder name (e.g. `Posteingang`) | `folder does not exist`; name mismatches UI language | Not yet covered |

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` | shared manifest-driven mock dispatcher from `../../_shared/mock_template/` |
| `process/` | hand-authored UiPath project; `GetOutlookMailMessages` with `Account=""`, `MailFolder="Invoices"`, no `Filter` |
| `data/m/r/` | synthetic canned `uip` responses; the smoking gun is in `job-logs.json` (No Account specified → resolving against default profile → folder not found there, shared store listed among available stores); `docsai ask` passthrough |

Diagnosis is not leaked in any agent-visible name (project `PayablesInvoiceReader`, activity "Get
Outlook Mail Messages"). The prompt states observed symptoms only: the read fails saying the folder does
not exist, yet the folder is definitely present — in the Accounts Payable **shared** mailbox the user
has open alongside their own inbox.

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent attributed the failure to the shared-mailbox folder being read with a blank `Account` (default-
  profile-only scope), and prescribed setting `Account` to the shared mailbox's SMTP address — not a
  folder-string edit, COM/session, timeout, or filter fix.

Playbook: `references/activity-packages/mail-activities/playbooks/get-outlook-mail-failures.md`
(Branch 1 — shared-mailbox / `Account` omission sub-cause).
