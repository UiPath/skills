# Move Outlook Mail Message Failure - COM Session Loss (Branch 1)

This scenario reproduces a `Move Outlook Mail Message`
(`MoveOutlookMessage`, `UiPath.Mail.Outlook.Activities`) failure that
faults 100% on an unattended robot with `The operation failed`
(`System.Runtime.InteropServices.COMException`, RPC server unavailable
`0x800706BA`). The robot has no live local Outlook COM session - Classic
Outlook is installed but is not running/synced for the unattended
Windows profile - so the destination folder tree cannot be indexed.

## What this scenario uncovers

**Root Cause:** The move activity is a desktop COM client. On the
unattended robot (`MOCK-HOST`, `UIPATH\ROBOTUSER1`) there is no running,
synced Outlook for the robot's Windows user, so the activity cannot bind
to an Outlook COM server and cannot index the destination folder tree.
The configured destination `MailFolder` `Inbox\Processed` is a **valid**
nested path - the path is not the bug. The COM bind failure surfaces as
`The operation failed`.

This maps to **Branch 1 (COM session loss)** of:
`references/activity-packages/mail-activities/playbooks/move-outlook-mail-failures.md`

The user is framed as **off-host**, so correct agent behavior is to
diagnose from Orchestrator + the project source and then hand a
host-side check list (keep Outlook running / Startup apps / Retry Scope
/ migrate to Graph o365 for unattended) without fabricating host
actions.

## Sibling-branch comparison

The move-outlook-mail-failures playbook has four cause-branches. This
scenario isolates Branch 1 and is constructed so the other three are
visibly ruled out:

| Branch | Cause | Signature | Why NOT this scenario |
|---|---|---|---|
| **1 (this)** | COM session loss - no live Outlook on unattended robot | "The operation failed" / COM server unreachable, 100% on unattended | This IS the scenario |
| 2 | Destination folder path / `Account` mismatch | Deterministic "folder does not exist" - bare leaf name or shared-mailbox `Account` gap | Destination `Inbox\Processed` is a valid nested path; error is a COM-bind failure, not folder resolution |
| 3 | Modern-vs-classic type mismatch | `Cannot convert type 'String' to 'IResource' / 'Office365Message'` | Classic `MoveOutlookMessage` wired to a `MailMessage` var (correct type); no cast error |
| 4 | New Outlook removed the desktop COM API | "Broke completely after an Office/Windows update" flipped host to New Outlook | Classic Outlook IS installed - it just was not running; no post-update break |

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project: classic `MoveOutlookMessage` with a valid `Inbox\Processed` destination and a `MailMessage` input |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook Branch 1 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table (folders list; jobs list --state Faulted; jobs get; jobs logs --level Error; jobs logs; docsai passthrough) |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

The smoking-gun job-log line:

```
[Move Outlook Mail Message] could not bind to a running Outlook instance
for UIPATH\ROBOTUSER1 (no live COM session); the destination folder tree
could not be indexed
```

preceded by `Running unattended on MOCK-HOST as UIPATH\ROBOTUSER1 (no
interactive desktop session)`, steers toward COM session loss and away
from a folder-path typo or a registration/bitness error.

## Success criteria

This scenario **scores the conclusion, not the trajectory** - the
`llm_judge` grades the agent's final response and tool calls against
`RESOLUTION.md`, not its internal investigation state.

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched the move-outlook-mail-failures playbook / **Branch 1**
  (COM session loss) and read the playbook under
  `references/.../mail-activities/playbooks/`.
- Agent attributed `The operation failed` to no live/synced Outlook COM
  session on the unattended robot (NOT a folder-path typo, type
  mismatch, registration/bitness error, New Outlook, or SMTP issue).
- Agent handed a host-side check list (keep Outlook running / add to
  Startup apps / Retry Scope / migrate to Graph o365 Move Email for
  unattended) without fabricating host actions it could not run.
