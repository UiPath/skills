# Delete Outlook Mail Message Failure - Shared-Mailbox Permission Denied (Branch 5)

This scenario reproduces a runtime `Delete Outlook Mail Message`
(`DeleteOutlookMailMessage`, `UiPath.Mail.Outlook.Activities`) failure caused
by a **mailbox-permission / access-denied** error on a **shared mailbox**.
The shared mailbox `ap-shared@contoso.com` opens and the target message is
found, but the delete is denied because the Robot account has **Send-As** but
**not Full Access (delete)** rights. The COM layer surfaces it as
`You do not have sufficient permission to perform this operation on this
object.` / `Access is denied. (Exception from HRESULT: 0x80070005
(E_ACCESSDENIED))`.

## What this scenario uncovers

**Root Cause:** The `Delete Outlook Mail Message` activity in `Main.xaml`
targets a message in the shared mailbox `ap-shared@contoso.com` with that
address set in `Account`. The read (`Get Outlook Mail Messages`) succeeds and
the message resolves, but the delete is denied: the Robot account
`UIPATH\ROBOTUSER1` has Send-As but not Full Access on the shared mailbox, so
it cannot delete. Send-As does not grant delete rights — only Full Access
does.

This maps to:
`references/activity-packages/mail-activities/playbooks/delete-outlook-mail-failures.md`
Branch 5 (Mailbox permission / access denied).

The user is framed as **off-host and not an Exchange admin**, so the correct
agent behavior is to hand an IT / Exchange check list (keep `Account` as the
shared address; request Full Access for the Robot's AD account from the
Exchange admin) rather than fabricate an Exchange change it cannot make.

## Sibling-branch comparison (delete-outlook-mail-failures)

| Branch | Signature | Why NOT this scenario |
|---|---|---|
| 1 — Stale message reference | `An object could not be found` after a fetch/delete gap | The target message WAS resolved/found right before the delete |
| 2 — Collection modified in loop | `Collection was modified; enumeration operation may not execute` inside a `For Each` | Single delete after Get; no loop mutating the live collection |
| 3 — New Outlook | Worked, then broke completely after an update; COM-bind failure | COM call reaches Outlook, opens the mailbox, and is rejected with an access error |
| 4 — COM session blocked / privilege | `The operation has timed out` / freeze, no clean exception | Fast, clean access-denied exception — not a hang |
| **5 — Mailbox permission / access denied** | **`insufficient permission` / `Access is denied (0x80070005 E_ACCESSDENIED)` on a shared mailbox** | **This scenario: Send-As but not Full Access on `ap-shared@contoso.com`** |

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project: `Get Outlook Mail Messages` then `Delete Outlook Mail Message`, both with `Account="ap-shared@contoso.com"` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the Branch 5 playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature (Branch 5) rather than captured from a real
> `.local/investigations/` session.

## Success criteria

This scenario **scores the conclusion, not the trajectory**. The only graded
outcomes are:

- Agent invoked the `uipath-troubleshoot` skill (`skill_triggered`).
- Agent matched `delete-outlook-mail-failures.md` Branch 5 and reached the
  same conclusion as `RESOLUTION.md`: the delete was denied because the Robot
  account lacks Full Access (delete) on the shared mailbox (Send-As is not
  enough), the folder/`Account` are fine and the message was found, and the
  fix is to keep `Account` as the shared address and have the Exchange admin
  grant Full Access — handed as an IT check list, with no fabricated Exchange
  or host action (`llm_judge`).
