# Move Outlook Mail Failure - Modern-vs-Classic Type Mismatch (Branch 3)

This scenario reproduces a Move Outlook Mail Message failure caused by
a **modern-vs-classic type mismatch**. After a mail-package update the
`InboxAutoFiler` workflow uses the **modern Move Email** activity
(`MoveEmailConnections`, from `UiPath.MicrosoftOffice365.Activities`),
whose message input expects an `Office365Message` / `IResource` object
reference -- but a **`String`** message-ID variable (`messageId`) is
wired into that input, left over from the classic design. The job
faults with
`Cannot convert type 'System.String' to
'UiPath.MicrosoftOffice365.Models.Office365Message'`
(`System.InvalidCastException`).

## What this scenario uncovers

**Root Cause:** A `String` is bound to a modern Move Email property
that expects an `Office365Message` / `IResource` object. The cause is
the classic-vs-modern mix introduced when the team updated the mail
packages -- `project.json` now carries **both**
`UiPath.Mail.Activities` (classic) and
`UiPath.MicrosoftOffice365.Activities` (modern), and a classic string
binding was carried into the modern resource-typed property. It is the
**TYPE** that is wrong, not the message-ID value.

This maps to:
`references/activity-packages/mail-activities/playbooks/move-outlook-mail-failures.md`
-- **Branch 3 (modern-vs-classic type mismatch)**.

**Fix:** Map the message (and folder) with the **`+` (plus)** resource
picker so the binding resolves to the expected `Office365Message` /
`IResource` object, OR switch to the **classic**
`Move Outlook Mail Message` (`MoveOutlookMessage`) activity, which
accepts string / `MailMessage` inputs directly.

The user is framed plainly ("investigate why it faults") -- this is a
workflow-fixable design/typing bug, so there is no off-host /
remote-user framing.

## Sibling-branch comparison

| Branch | Signature | Cause | This scenario? |
|---|---|---|---|
| 1 -- COM session loss | "operation failed" / "folder does not exist", intermittent or unattended-only | Outlook not running/synced for the Robot user | No |
| 2 -- Folder path / `Account` | "folder does not exist", immediate, every run | Bare nested leaf name, or shared-mailbox destination with empty `Account` | No |
| **3 -- Type mismatch** | **`Cannot convert type 'String' to '...Office365Message' / 'IResource'`** | **`String` wired into a modern resource-typed input after a package update** | **Yes** |
| 4 -- New Outlook | COM-bind / "Outlook is not running", broke completely after an OS/Office update | Host flipped to New Outlook; desktop COM API removed | No |

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project: modern Move Email activity with a `String` message-ID variable on its `Message` input; `project.json` carries both classic and modern mail packages |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook Branch 3 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched `move-outlook-mail-failures.md` **Branch 3** and reached
  the same conclusion as `RESOLUTION.md`: a `String` was wired into the
  modern Move Email's resource-typed message input (classic/modern mix
  after the package update), throwing the `String`-to-`Office365Message`
  cast error -- and recommended the `+` resource picker OR the classic
  `Move Outlook Mail Message` activity with string / `MailMessage`
  inputs.

This scenario **scores the conclusion, not the trajectory** -- the
`llm_judge` grades the agent's final response and tool calls against
`RESOLUTION.md`, never internal investigation state.
