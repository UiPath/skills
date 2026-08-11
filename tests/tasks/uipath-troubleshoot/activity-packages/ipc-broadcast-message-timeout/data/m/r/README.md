# Broadcast Message Timeout — Faithful Replay

This scenario replays a UiPath diagnostic investigation where an Orchestrator
job faulted with `System.TimeoutException` thrown by a **`Broadcast Message`**
activity (`UiPath.IPC.Activities`) in `Main.xaml`. The agent runs the
`uipath-troubleshoot` skill against a `uip` CLI mock and must reach the same
root cause as `RESOLUTION.md`.

## What the original session uncovered

The `Broadcast Message` activity **Broadcast Order Ready** broadcasts on channel
`OrderReadyChannel` with `TimeoutMS = 3000`. No **Message Receiver Trigger** was
listening on that channel in parallel at the broadcast instant, so the channel
search expired and the activity threw
`System.TimeoutException: Timeout of 3000 ms has passed and no channel was found
to send the message to.`. The fix is to run the receiver in parallel on the exact
same channel before broadcasting, match the channel string, and raise the timeout.

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
- Agent matched the correct playbook (`references/activity-packages/ipc-activities/playbooks/broadcast-message-timeout.md`) AND reached the same root cause as `RESOLUTION.md`
