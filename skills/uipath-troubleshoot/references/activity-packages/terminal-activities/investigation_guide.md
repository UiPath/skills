# Terminal Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity is `UiPath.Terminal.Activities.TerminalSession` (or a child running inside it). A fault attributed to a child activity that runs *after* connect is a different problem from a connect-time fault.
- **Connection target** — the host/port/provider in evidence (from the connection string or the workflow source) matches the terminal the user is asking about. Different host/provider = unrelated failure.
- **Connection mode** — distinguish a **new connection** (`ConnectionString`) from a reused **existing connection** (`ExistingConnection`). They fail for different reasons (open/attach vs. already-disconnected).
- **Workflow file** — the error originates from the workflow the user references, not another `.xaml`/`.cs` that also opens a terminal session.
- **Timestamp** — the failure occurred in the reported window; a transient host/network outage at that time is load-bearing.

If the data doesn't match: discard it. Do NOT use an unrelated session as a proxy.

## Domain-Specific Data Gathering

1. **Read the full exception, including the trailer.** `TerminalConnectionException` formats its message as `<message> | ResultCode=<TerminalResultCode> | ConnectionStatus=<ConnectionStatus>`. The `ResultCode` and `ConnectionStatus` are the discriminator — capture them, not just the leading sentence.
2. **Unwrap `System.AggregateException`.** A connect fault raised on the session's background task can surface as `System.AggregateException: One or more errors occurred.` The aggregate is only the async wrapper — the inner exception (typically a `TerminalConnectionException` or a provider exception) carries the real cause. Always read `InnerException`/`InnerExceptions[0]`.
3. **Treat a `System.NullReferenceException` from `TerminalSession` as a masked connect failure first.** The scope's cleanup calls `Shutdown()` on the connection object; when the connection was never created (the open threw) that object is null, so an NRE can surface *instead of* the underlying connect error. Look for the original connect failure in the same job's earlier logs/traces before concluding the workflow has a null-variable bug.
4. **Separate design-time validation from runtime faults.** `Invalid connection string`, `Cannot use the ExistingConnection property with the ConnectionString or the OutputConnection property`, and `The UiPath Internal Provider is now deprecated. Please use Direct Connection.` are validation errors raised before/at execution from the activity configuration — not from the remote host.

## Testing Prerequisites

1. **Activity identity** — confirm the faulted activity is `TerminalSession` and capture its display name.
2. **Exception detail** — capture the full message plus `ResultCode` and `ConnectionStatus`, and whether the type is the bare `TerminalConnectionException`, a `System.AggregateException`, or a `System.NullReferenceException`.
3. **Connection config** — provider type, terminal type, host, port (from the connection string or workflow source); whether `ExistingConnection` is used; the configured `TimeoutMS`.
4. **Host reachability** — whether the terminal host/port is reachable from the robot machine, and whether the provider runtime (e.g., the EHLLAPI/emulator client) is installed on that machine.
5. **Package version** — `UiPath.Terminal.Activities` version.
