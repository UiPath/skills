# Final Resolution

Root Cause: The `Broadcast Message` activity **Broadcast Control Signal** in `Main.xaml` (`UiPath.IPC.Activities.BroadcastMessage`, `Channel = "ControlChannel"`) faulted with `System.UnauthorizedAccessException: Access to the path '\\.\pipe\UiPath.Ipc.ControlChannel' is denied.` while opening the channel's **local named-pipe endpoint**. IPC is confined to the **same robot, same Windows user, same session, same machine**; the named-pipe ACL denied the connection because the sender and the receiver are separated by a session / user / elevation boundary (e.g. an unattended Session 0 robot vs an attended user session, two different robot accounts, or one process elevated and the other not). This is a permission/boundary fault at the pipe — not a timing / no-receiver timeout.

Evidence:

### Orchestrator
- Process **SessionBridge**, release version **10012**, folder **Shared**, job key `c1d2e3f4-9012-4abc-9def-000000000012` ended `Faulted`.
- Host **MOCK-ROBOT-22**, ErrorCode `Robot`, RuntimeType `Unattended`. Job `InputArguments = {}`.
- `EntryPointPath = Main.xaml`.

### IPC Activities (Root Cause)
- `System.UnauthorizedAccessException` — "Access to the path '\\.\pipe\UiPath.Ipc.ControlChannel' is denied.".
- Faulted activity: `Broadcast Message` **Broadcast Control Signal** inside `Sequence "Main Sequence"` in `Main.xaml`.
- Stack frames `System.IO.Pipes.NamedPipeClientStream.Connect` → `UiPath.IPC.Activities.BroadcastMessage.ExecuteAsync` — the connection to the channel's named pipe was refused by its ACL, i.e. a session/user/elevation boundary, not a missing receiver.

Immediate fix:

1. Run the sender and receiver on the **same robot, same Windows user, same session, and same elevation level**. `UiPath.IPC.Activities` does not support communication across machines or across Windows user sessions; a peer in a different session/account, or at a mismatched elevation (one elevated / "Run as administrator", the other not), is denied by the pipe ACL. Launch the receiver in the same session (e.g. via `Run Parallel Process` under the same robot account) so both share the pipe namespace.
  - Where: deployment/session topology of the **SessionBridge** sender and its Message Receiver Trigger process; `Main.xaml` `Broadcast Message` **Broadcast Control Signal** (`Channel = "ControlChannel"`).
  - Who: RPA developer / robot administrator.
  - Source: `references/activity-packages/ipc-activities/playbooks/broadcast-message-unauthorized-access.md` § Resolution.

Investigation summary:

| # | Hypothesis | Confidence | Status | Root Cause? |
|---|---|---|---|---|
| H1 | Named-pipe endpoint denied the connection — sender/receiver split across session / user / elevation boundary | High | Confirmed | Yes |
| H2 | No live receiver on the channel within the timeout (`System.TimeoutException`) | Low | Rejected | No — the exception is `System.UnauthorizedAccessException` (access denied on the pipe), not a timeout |
| H3 | Fault originates in user workflow expression code (not the IPC package) | Low | Rejected | No — deepest frames are `NamedPipeClientStream.Connect` → `UiPath.IPC.Activities.BroadcastMessage.ExecuteAsync`, inside the activity |
