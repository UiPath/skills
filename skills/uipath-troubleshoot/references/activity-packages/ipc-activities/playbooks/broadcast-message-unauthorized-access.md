---
confidence: medium
---

# Broadcast Message — System.UnauthorizedAccessException (Pipe / Session Boundary)

## Context

What this looks like:
- Activity `Broadcast Message` / `Send Message` (`UiPath.IPC.Activities.BroadcastMessage` / `SendMessage`) faults with `System.UnauthorizedAccessException`
- Message: `Access to the path is denied.` (or a named-pipe access-denied while opening the channel endpoint)
- Often reproduces **consistently** for a given deployment topology (unlike the timing-dependent timeout case)

What can cause it:
- IPC runs over a **local named pipe** confined to the **same robot, same Windows user, same session, same machine**. The pipe's ACL rejects a peer that lives across a boundary:
  - **Different Windows user session** — sender and receiver split across sessions (e.g. an attended user session on one side, an unattended **Session 0** robot on the other).
  - **Different user account** — the two processes run under different robot / Windows accounts, so neither can open the other's session-scoped pipe.
  - **Elevation mismatch** — one process runs **elevated** ("Run as administrator" / high integrity) and the other does not; the integrity-level boundary denies the connection.

What to look for:
- The Windows session, user account, and elevation level of **both** the sender and receiver processes.
- Whether the deployment split the two processes across attended vs unattended, or across two robot accounts.
- That this is a boundary/permission fault, not a timing fault — the receiver may be perfectly alive on the right channel.

## Investigation

1. Confirm the faulted activity is `Broadcast Message` / `Send Message` and the exception is `System.UnauthorizedAccessException` (access-denied on the channel endpoint) — not `TimeoutException`.
2. Establish where the receiver process runs: which robot / Windows user, which session, and at what elevation, versus the sender.
3. Ask the user (or someone with robot/host access) to confirm both processes are intended to run on the **same** robot, user, session, and elevation — this is a host-level fact not visible in the sender's job log.

## Resolution

- **Co-locate both processes** — run the sender and receiver on the **same robot, same Windows user, same session, same machine**. `UiPath.IPC.Activities` does **not** support communication across machines or across Windows user sessions.
- **Match elevation** — ensure both processes run at the **same integrity level**: either both elevated or both non-elevated. A single elevated peer will be denied by the other's pipe ACL.
- **Align the robot account** — if the two processes run under different robot accounts, reconfigure so they execute under the **same** account in the same session (e.g. both as the same unattended robot, launched via `Run Parallel Process` so they share the session).
- **Do not treat as a timeout** — raising `Timeout` will not fix an access-denied fault; the connection is refused at the pipe, not lost to timing.

> Related: a receiver that is simply absent / on a mismatched channel / not up in time throws `System.TimeoutException` instead → [broadcast-message-timeout.md](./broadcast-message-timeout.md).
