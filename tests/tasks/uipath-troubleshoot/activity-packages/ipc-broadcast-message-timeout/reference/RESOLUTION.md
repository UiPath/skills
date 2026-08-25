# Final Resolution

Root Cause: The `Broadcast Message` activity **Broadcast Order Ready** in `Main.xaml` (`UiPath.IPC.Activities.BroadcastMessage`, `Channel = "OrderReadyChannel"`, `TimeoutMS = 3000`) searched for a live **Message Receiver Trigger** listening on channel `OrderReadyChannel`, but no receiver was found before the 3000 ms timeout expired, so it threw `System.TimeoutException: Timeout of 3000 ms has passed and no channel was found to send the message to.`. IPC delivery requires a receiver process actively listening on the **exact same channel, in parallel, on the same host** at the moment of the broadcast — none was.

Evidence:

### Orchestrator
- Process **OrderNotifier**, release version **10011**, folder **Shared**, job key `c1d2e3f4-9011-4abc-9def-000000000011` ended `Faulted`.
- Host **MOCK-ROBOT-22**, ErrorCode `Robot`, RuntimeType `Unattended`. Job `InputArguments = {}`.
- `EntryPointPath = Main.xaml`.

### IPC Activities (Root Cause)
- `System.TimeoutException` — "Timeout of 3000 ms has passed and no channel was found to send the message to.".
- Faulted activity: `Broadcast Message` **Broadcast Order Ready** inside `Sequence "Main Sequence"` in `Main.xaml`.
- Deepest frame `UiPath.IPC.Activities.BroadcastMessage.ExecuteAsync` — the fault is inside the IPC activity's channel-search, not user expression code. `Channel = "OrderReadyChannel"`, `TimeoutMS = 3000`.

Immediate fix:

1. Ensure a **Message Receiver Trigger** on the **exact same channel** (`OrderReadyChannel`, case-sensitive) is **running in parallel** and past listener initialization **before** the broadcast — e.g. launch the receiver process via `Run Parallel Process` / a background job first. Raise `TimeoutMS` to at least **5000–10000 ms** so the receiver has time to come up, and confirm the sender and receiver channel strings match exactly. Optionally wrap `Broadcast Message` in a Try Catch if a receiver may legitimately be absent.
  - Where: `Main.xaml`, `Sequence "Main Sequence"` → `Broadcast Message` **Broadcast Order Ready** (`Channel` / `TimeoutMS`), plus the receiver-process launch ordering.
  - Who: RPA developer.
  - Source: `references/activity-packages/ipc-activities/playbooks/broadcast-message-timeout.md` § Resolution.

Investigation summary:

| # | Hypothesis | Confidence | Status | Root Cause? |
|---|---|---|---|---|
| H1 | `Broadcast Message` found no live Message Receiver Trigger on the channel within `TimeoutMS` (receiver not running in parallel / channel mismatch / timeout too low) | High | Confirmed | Yes |
| H2 | Access denied at the pipe endpoint (`System.UnauthorizedAccessException`, cross session/user/elevation) | Low | Rejected | No — the exception is `System.TimeoutException` ("no channel was found"), not an access-denied fault |
| H3 | Fault originates in user workflow expression code (not the IPC package) | Low | Rejected | No — deepest frame is `UiPath.IPC.Activities.BroadcastMessage.ExecuteAsync`, inside the activity |
