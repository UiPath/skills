---
confidence: medium
---

# Terminal — Terminal Session connection failed

## Context

`TerminalSession` faults while opening (or attaching to) the terminal connection — before any child screen-interaction activity runs. The failure originates in the connection step: `provider.CreateConnection(...)` → `connection.Start(...)` → `connection.WaitConnected(timeout)`. The emulator host is external (a separate process / client DLL / remote host), so this is where unreachable hosts, wrong provider/port, missing provider runtime, and slow negotiation surface.

What this looks like — a `UiPath.Terminal.Data.TerminalConnectionException` (a plain `System.Exception`) whose message is formatted `<message> | ResultCode=<TerminalResultCode> | ConnectionStatus=<ConnectionStatus>`. The leading `<message>` is one of:

- `Error initiating connection` — `connection.Start(...)` returned false. The provider could not begin the session (host unreachable, wrong port, provider/host process problem).
- `Error waiting for connection` — `Start` succeeded but `WaitConnected(timeout)` expired before the session became ready. Slow host/negotiation, or `TimeoutMS` too low.
- `No connection specified` — neither a `ConnectionString` nor an `ExistingConnection` was supplied at runtime (`ResultCode=InvalidConnectionData`).
- `The specified existing connection is disconnected` — a reused `ExistingConnection` is no longer `Connected` (`ResultCode=NotConnected`).

It may instead surface as a provider-level message thrown from `CreateConnection`/`Start` (for IBM EHLLAPI and similar providers):

- `There was an error connecting to terminal. Error code: {0}` — provider connect failure; the `{0}` code is provider-specific.
- `Terminal host process path not found: {0}` — the provider host executable is missing at `{0}` (the emulator client / provider runtime is not installed on the robot machine).
- `Error waiting for terminal host service. Timeout: {0}` — the provider's host service did not start in time.
- `Service unavailable` — the terminal service is not available.
- `Error attaching to session` / `Error initializing EHLLL library` — IBM EHLLAPI could not attach to / initialize the configured session.

**Async-wrapped form:** the same fault can surface as `System.AggregateException: One or more errors occurred.` The aggregate is only the wrapper for the connect task — read `InnerExceptions[0]` (the `TerminalConnectionException` or provider exception above) for the real cause. Do not attribute the failure to `AggregateException` itself.

What can cause it:
- **Host unreachable / wrong host or port.** The configured host name/IP or port does not accept the connection (host down, firewall, wrong port for the terminal type). → `Error initiating connection`.
- **Provider runtime not installed on the robot.** The emulator client / provider DLL the connection string selects is not present on the execution machine. → `Terminal host process path not found`, `Error initializing EHLLL library`, `Error attaching to session`. Common when a workflow validated on a developer machine runs on a robot without the emulator installed.
- **Connect/wait timeout.** The host is reachable but negotiation is slow, or `TimeoutMS` is set too low for this host. → `Error waiting for connection`.
- **Reused connection already closed.** `ExistingConnection` points at a session a prior `TerminalSession` already shut down. → `The specified existing connection is disconnected`.
- **No connection configured at runtime.** The `ConnectionString` expression evaluated to null/empty and no `ExistingConnection` was provided. → `No connection specified`.
- **Terminal service unavailable.** The provider's backing service is down. → `Service unavailable` / `Error waiting for terminal host service`.

> **Different cause — do not apply this playbook:**
> - `System.NullReferenceException` from `TerminalSession` → use [terminal-session-null-reference.md](./terminal-session-null-reference.md) (it is usually a *masked* connect failure, but it is investigated differently). When that NRE hides one of the connect messages above, the connect message is the real cause.
> - Design-time/validation errors raised from the activity configuration, not the host — `Invalid connection string`, `Cannot use the ExistingConnection property with the ConnectionString or the OutputConnection property`, `The UiPath Internal Provider is now deprecated. Please use Direct Connection.` — fix the activity configuration; they are not host-connectivity failures.
> - A fault from a child activity that runs *after* the session is connected (screen read/write/wait) is not a connection failure.

## Investigation

1. **Read the full exception including the trailer.** Capture `<message>`, `ResultCode`, and `ConnectionStatus`. If the type is `System.AggregateException`, unwrap to `InnerExceptions[0]` first.
2. **Map the message to the failing step:** `Error initiating connection` → open failed (reachability/provider); `Error waiting for connection` → ready-timeout; `Terminal host process path not found` / `Error initializing EHLLL library` / `Error attaching to session` → provider runtime missing/misconfigured on the robot; `The specified existing connection is disconnected` → stale reused connection; `No connection specified` → no input.
3. **Capture the connection config** from the connection string or workflow source: provider type, terminal type, host, port, and the configured `TimeoutMS`.
4. **Check host reachability from the robot machine** (not the developer machine) — host/port open, and the emulator/provider runtime installed there.
5. **For reused connections,** confirm the upstream `TerminalSession` that produced the `ExistingConnection` kept it alive (output connection / `CloseConnection` unchecked) and that it didn't already close.

## Resolution

- **If `Error initiating connection` / `There was an error connecting to terminal`:** correct the host/port/provider in the connection string and confirm the terminal host is reachable from the robot machine (firewall, DNS, port). Verify the provider/terminal type matches the host.
- **If `Terminal host process path not found` / `Error initializing EHLLL library` / `Error attaching to session`:** install/repair the emulator client / provider runtime on the robot machine and confirm the configured session/profile exists for the EHLLAPI provider.
- **If `Error waiting for connection` / `Error waiting for terminal host service`:** raise `TimeoutMS` if the host is legitimately slow, and confirm the host completes session negotiation; investigate host/network latency.
- **If `The specified existing connection is disconnected`:** open a fresh `TerminalSession` instead of reusing the stale connection, or keep the upstream connection alive (emit `OutputConnection` / leave `CloseConnection` unchecked) for the lifetime it is reused.
- **If `No connection specified`:** provide a non-empty `ConnectionString` or a valid `ExistingConnection`.
- **If `Service unavailable`:** restore/restart the terminal service the provider depends on, then re-run.

If the host is demonstrably reachable, the provider runtime is installed, and the connection string is correct yet the open still fails, the cause is outside the activity — escalate to the terminal host / emulator administrator.
