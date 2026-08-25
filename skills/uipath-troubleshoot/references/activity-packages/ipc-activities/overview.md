# IPC Activities

Activities from the `UiPath.IPC.Activities` package for **inter-process communication** between UiPath processes running at the same time. One process broadcasts or sends a message on a named **channel**; another process, running a **Message Receiver Trigger** on the same channel, receives it. The transport is a local **named pipe** — communication is confined to the **same robot, same Windows user, same session, same machine**. It is not a network / cross-machine / cross-user bus.

Do NOT confuse this package with the internal `UiPath.Ipc` / `UiPath.CoreIpc` transport that Integration Service connector activities use under the hood (`RemoteException`, `DAP-*` codes) — that is a different concern documented under Integration Service.

## How Broadcast Message Executes

`Broadcast Message` (`UiPath.IPC.Activities.BroadcastMessage`) publishes a message to every active listener on a channel. Behaviour chain:

1. Open / connect to the local named-pipe endpoint for the configured `Channel` string.
2. Search for an active **Message Receiver Trigger** listening on that exact channel, up to the `Timeout` (milliseconds).
3. Deliver the `Message` payload to the receiver(s) found.

Failures originate at distinct layers — **no receiver found within the timeout** (step 2, `System.TimeoutException`), **the pipe / session boundary denies the connection** (step 1, `System.UnauthorizedAccessException`), a **channel-string mismatch** (the receiver is up but on a different channel name — surfaces as a timeout, or silently drops when `Timeout = 0`), or a **package-version mismatch** between sender and receiver (protocol incompatibility). Knowing which layer produced the error narrows the investigation.

## Key Activities

- **Broadcast Message** (`BroadcastMessage`, display name "Broadcast Message") — publish a `Message` to all listeners on `Channel`, waiting up to `Timeout` ms for a receiver. Key properties: `Channel` (exact, case-sensitive string), `Message` (payload), `Timeout` (Int32 ms — `0` = drop immediately if no receiver, no exception).
- **Send Message** (`SendMessage`, display name "Send Message") — send a `Message` to a single receiver on `Channel`, optionally awaiting a response. Same channel / timeout / session model as Broadcast Message.
- **Message Receiver Trigger** (`MessageReceiverTrigger`, display name "Message Receiver Trigger") — the listener side. Runs in the receiver process and fires when a message arrives on its `Channel`. Must be **running in parallel** before the sender broadcasts.
- **Get Messages** (`GetMessages`) — retrieve queued messages received on a channel.

## Common Failure Patterns

- **`System.TimeoutException` — no channel / receiver found** — `Broadcast Message` (or `Send Message`) faults with `Timeout of <N> ms has passed and no channel was found to send the message to.`. The activity searched for a live Message Receiver Trigger on the channel but the timeout expired first. Causes: the receiver process was **not running in parallel** (not launched, launched too late, still initializing its listener loop, or already exited), the **channel string does not match** (case-sensitive) between sender and receiver, or the `Timeout` is set **too low** for the receiver to come up. See [broadcast-message-timeout.md](./playbooks/broadcast-message-timeout.md).
- **`System.UnauthorizedAccessException` — pipe / session boundary denies the connection** — `Broadcast Message` faults with `Access to the path is denied.` / a named-pipe access-denied while opening the channel endpoint. IPC is confined to the same robot, user, and session; the named-pipe ACL rejects a peer in a **different Windows user session**, under a **different user account**, or at a **different elevation level** (one process elevated / "Run as administrator", the other not). Causes: sender and receiver split across sessions (e.g. attended user session vs unattended Session 0), different robot accounts, or an elevation mismatch. See [broadcast-message-unauthorized-access.md](./playbooks/broadcast-message-unauthorized-access.md).
- **Messages silently dropped (`Timeout = 0`)** — no exception, but the receiver never gets the message because `Timeout` is `0` and no listener was active at the instant of the broadcast. Trace the receiver's actual receipt, not just the absence of an exception on the sender.
- **Package-version mismatch** — sender and receiver reference **different `UiPath.IPC.Activities` versions**, so the wire protocol is incompatible even when the channel and session match. Align the package version in both projects (Manage Packages → same version).

## Package

NuGet: `UiPath.IPC.Activities`

Version-specific behaviour is documented in the relevant playbooks.
