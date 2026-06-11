# Move Outlook Mail Message Failure - Bare Nested-Folder Leaf Name (Branch 2)

This scenario reproduces a runtime `Move Outlook Mail Message`
(`MoveOutlookMessage`, `UiPath.Mail.Outlook.Activities`) failure that
faults **deterministically, on every run**, with
`The specified folder does not exist.` The destination `MailFolder` is set
to the bare leaf name `"Processed"` instead of the nested path
`Inbox\Processed`, so Outlook resolves it against the mailbox root, finds
no top-level folder by that name, and throws. The Outlook desktop COM
session is fine -- it attaches and resolves the source message before the
destination folder fails.

## What this scenario uncovers

**Root Cause:** The `Move Outlook Mail Message` activity in `Main.xaml`
has `MailFolder="Processed"`. `Processed` actually lives under `Inbox`, so
the bare leaf name does not resolve. The fix is to address the destination
by path -- `MailFolder="Inbox\Processed"` (or `Inbox/Processed`); for a
shared-mailbox destination, also set the activity's `Account` field.

This maps to:
`references/activity-packages/mail-activities/playbooks/move-outlook-mail-failures.md`
(Branch 2 -- destination folder path / `Account`).

This is a **workflow-fixable configuration bug** -- the agent can diagnose
and fix it entirely from the project source and Orchestrator evidence. No
host-side action is required, so the prompt is a plain "investigate why it
faults" with no off-host / host-command framing.

## How this scenario reproduces Branch 2

The Branch 2 hallmark is "fails immediately and deterministically, every
run, even attended." This scenario encodes exactly that:

| Branch 2 signal | Where it appears in this scenario |
|---|---|
| `The specified folder does not exist` | `jobs get` `Info` + the `jobs logs` error line |
| Bare nested-folder leaf name | `Main.xaml` `MailFolder="Processed"` |
| Deterministic, every run | job faulted ~2s after start; user reports "every run" |
| COM session is healthy (not Branch 1) | job log: Outlook attached + source message resolved in Inbox |
| Smoking-gun resolution line | `destination folder 'Processed' not found at the mailbox root; no such top-level folder` |

## Sibling-branch comparison (why this is Branch 2, not 1/3/4)

| Branch | Signature | Timing | This scenario? |
|---|---|---|---|
| 1 - COM session loss | "operation failed" / "folder does not exist" | **intermittent** or unattended-only | No -- COM attached fine; deterministic |
| **2 - Folder path / Account** | **"The specified folder does not exist"** | **immediate, every run** | **Yes** |
| 3 - Modern-vs-classic type mismatch | `Cannot convert type 'String' to 'IResource' / 'Office365Message'` | design-time / after dependency update | No -- no cast error; classic activity |
| 4 - New Outlook | COM-bind failure, "Outlook is not running" | broke completely after an OS/Office update | No -- no post-update break |

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with `MailFolder="Processed"` on the Move activity |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook Branch 2 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table (quoted + unquoted arg variants) |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

This test **scores the conclusion, not the trajectory.** The `llm_judge`
grades the agent's final response and tool calls against `RESOLUTION.md`;
it does not require a specific investigation path or any
`.local/investigations/` internal state.

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched `move-outlook-mail-failures.md` Branch 2 (named the
  playbook and Read a file under
  `references/activity-packages/mail-activities/playbooks/`).
- Agent reached the same conclusion as `RESOLUTION.md`: the bare leaf
  `MailFolder="Processed"` does not resolve (the folder lives under Inbox),
  the Outlook COM session is fine, and the fix is the nested path
  `Inbox\Processed` (or `Account` for a shared mailbox).
