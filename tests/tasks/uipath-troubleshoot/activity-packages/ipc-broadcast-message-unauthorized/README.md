# Broadcast Message Unauthorized Access — Faithful Replay

This scenario replays a UiPath diagnostic investigation where an Orchestrator
job faulted with `System.UnauthorizedAccessException` thrown by a
**`Broadcast Message`** activity (`UiPath.IPC.Activities`) in `Main.xaml`. The
agent runs the `uipath-troubleshoot` skill against a `uip` CLI mock and must
reach the same root cause as `RESOLUTION.md`.

## What the original session uncovered

The `Broadcast Message` activity **Broadcast Control Signal** broadcasts on
channel `ControlChannel`. Opening the channel's local named-pipe endpoint
(`\\.\pipe\UiPath.Ipc.ControlChannel`) was refused by the pipe ACL, throwing
`System.UnauthorizedAccessException: Access to the path ... is denied.`. IPC is
confined to the same robot, user, session, and machine; the sender and receiver
were separated by a session / user / elevation boundary. The fix is to co-locate
both processes on the same robot / user / session / elevation.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../../../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | frozen snapshot of the failing UiPath project (`Main.xaml`) |
| `fixtures/mocks/responses/*.json` | recorded `uip or` stdout: folder list, faulted job, error logs |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook (`references/activity-packages/ipc-activities/playbooks/broadcast-message-unauthorized-access.md`) AND reached the same root cause as `RESOLUTION.md`
