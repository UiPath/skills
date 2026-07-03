---
confidence: medium
signatures:
  - kind: exception
    value: "System.NullReferenceException"
    note: "attributed to UiPath.Terminal.Activities.TerminalSession, usually with no terminal-specific message — most often a masked connect failure (scope cleanup calls Shutdown() on a null connection)"
exclusions:
  - "TerminalConnectionException / connect-time message surfaced directly → terminal-session-connection-failed.md"
---

# Terminal — Terminal Session NullReferenceException

## Context

`TerminalSession` faults with `System.NullReferenceException`. In this scope the NRE is almost never a workflow-variable bug — it is usually a **masked connection failure**. When the connection open throws, the connection object is never assigned; the scope's cleanup path then calls `Shutdown()` on that null object, and the resulting `NullReferenceException` surfaces *instead of* (or alongside) the original connect error.

What this looks like:
- A bare `System.NullReferenceException` attributed to `UiPath.Terminal.Activities.TerminalSession`, frequently with no terminal-specific message.
- Often preceded — in the same job's earlier logs/traces — by a connect failure (`Error initiating connection`, `There was an error connecting to terminal`, `Terminal host process path not found`, etc.). That earlier message is the real cause.

What can cause it:
- **Cleanup after a failed open (most common).** `CreateConnection`/`Start` threw, leaving the internal connection null; the scope's close path invokes `Shutdown()` on null → NRE. The underlying connect failure is the true root cause.
- **Null or disposed `ExistingConnection`.** A reused connection variable evaluated to null (an upstream `TerminalSession` didn't emit `OutputConnection`, or the variable was never set / went out of scope) and is dereferenced.
- **Provider returned no session object.** A provider that signals failure by returning a null session rather than throwing, so the first dereference NRE's.

What to look for:
- Whether a connect-time error appears earlier in the same execution — if so, this NRE is the masked form of [terminal-session-connection-failed.md](./terminal-session-connection-failed.md).
- Whether the session uses `ExistingConnection`, and whether the upstream session that should have produced it actually succeeded and stayed alive.

> **Different cause — do not apply this playbook:**
> - A `NullReferenceException` from a **child** activity inside the session body (acting on screen data) is a workflow-logic / data problem in that child, not a session-open problem.
> - A `TerminalConnectionException` / `System.AggregateException` surfaced directly (without an NRE) → use [terminal-session-connection-failed.md](./terminal-session-connection-failed.md).

## Investigation

1. **Look for an underlying connect failure first.** Scan the same job's earlier Error-level logs and activity traces for a `TerminalConnectionException` or provider connect message. If present, treat this NRE as the masked connect failure and switch to [terminal-session-connection-failed.md](./terminal-session-connection-failed.md).
2. **Determine the connection mode.** New connection (`ConnectionString`) vs. reused (`ExistingConnection`). For a reused connection, trace back to the upstream `TerminalSession` and confirm it succeeded and emitted a live `OutputConnection`.
3. **Capture the connection config** (provider type, terminal type, host, port) — a missing provider runtime or unreachable host is the usual hidden cause behind a cleanup NRE.

## Resolution

- **If an underlying connect failure is present:** fix that connect failure per [terminal-session-connection-failed.md](./terminal-session-connection-failed.md) (reachability, provider runtime, port, timeout). Resolving the open removes the cleanup NRE.
- **If `ExistingConnection` is null/disposed:** ensure the upstream `TerminalSession` emits its connection via `OutputConnection` and keeps it alive (`CloseConnection` unchecked) for as long as it is reused, and that the connection variable is in scope and assigned before this session runs.
- **If no underlying error and the open genuinely returns no session:** capture full provider logs and escalate with the provider type and host — the provider is failing without a descriptive error.

Do not "fix" this by enabling `ContinueOnError` to swallow the NRE — that hides the real connect failure and leaves the session unusable downstream.
