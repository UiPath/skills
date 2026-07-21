# Terminal Activities

Activities from the `UiPath.Terminal.Activities` package for automating terminal/mainframe emulators (IBM 3270/5250 via EHLLAPI, VT, and other providers). All work happens inside a **Terminal Session** (`TerminalSession`) scope: it opens a connection, runs its child activities against the live screen, then closes the connection.

## How Terminal Session Works

`TerminalSession` is an `AsyncNativeActivity`. On execute it:

1. Resolves the connection — either a new connection from a serialized **connection string** (provider type, terminal type, host, port, SSH credentials) or a passed-in **existing connection** (`ExistingConnection`).
2. Opens it on a background task: `provider.CreateConnection(...)` → `connection.Start(...)` → `connection.WaitConnected(timeout)`. The provider launches/attaches the emulator host process and negotiates the session.
3. Runs the child `Body` against the connected session, then closes the connection (unless it is kept alive via `OutputConnection` or an un-checked `CloseConnection`).

The connection step is where almost all faults originate — the emulator host is external (a separate process / DLL / remote host), so an unreachable host, wrong provider/port, missing provider DLL, or a slow negotiation all surface here, before any screen interaction runs.

## Key Properties

- **ConnectionString** — serialized connection config (provider type, terminal type, host, port). Mutually exclusive with `ExistingConnection`/`OutputConnection`.
- **ExistingConnection** — reuse a `TerminalConnection` opened by an earlier session. Must still be `Connected`.
- **OutputConnection** — emit the opened connection for reuse; keeps it alive after the scope.
- **TimeoutMS** — connect / wait-connected timeout. **DelayMS** — post-connect settle delay.
- **ContinueOnError** — when true, swallows the fault and continues.

## Common Failure Patterns

- **Connection failed** — the session cannot open or attach the terminal: unreachable host / wrong port, invalid connection string, the provider host process/DLL is missing, the terminal service is unavailable, or the connect/wait times out. Surfaces as a `TerminalConnectionException` (a `System.Exception`) carrying `... | ResultCode=<code> | ConnectionStatus=<status>`, or its async-wrapped `System.AggregateException` form. See [terminal-session-connection-failed.md](./playbooks/terminal-session-connection-failed.md).
- **NullReferenceException on a never-opened session** — a `System.NullReferenceException` raised while the scope cleans up a connection that was never established (the real connect error is masked by the cleanup NRE), or because a passed `ExistingConnection` is null/disposed. See [terminal-session-null-reference.md](./playbooks/terminal-session-null-reference.md).

## Package

NuGet: `UiPath.Terminal.Activities`
