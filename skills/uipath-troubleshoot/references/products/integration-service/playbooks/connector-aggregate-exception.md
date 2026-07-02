---
confidence: low
signatures:
  - kind: exception
    value: "System.AggregateException"
    note: "async wrapper on a connector activity stack — the real error is InnerExceptions[0]; route on the inner exception"
exclusions:
  - "inner GeneralException (DAP-GE) → connector-general-exception.md"
  - "inner RuntimeException (DAP-RT) → connector-runtime-exception.md"
  - "inner Ipc/CoreIpc RemoteException → connector-remote-exception.md"
  - "inner NullReferenceException → connector-null-reference.md"
---

# Connector Activity — AggregateException

## Context

What this looks like — robot exception `System.AggregateException` on a connector activity (the stack shows a connector class such as `UiPath.<Connector>.IntegrationService.Activities.<Operation>` or `...Scope`, often via `AsyncCodeActivity.CompleteAsyncCodeActivityWorkItem`). Connector activities run asynchronously; when the async operation faults (or several parallel branches fault), the failures are collected into an `AggregateException`. The wrapper itself carries no useful cause — **the real error is in `InnerExceptions[0]`** (and, if that is itself a wrapper, recurse).

Which activities produce this:
- **ConnectorActivity** — and connector `Scope` activities wrapping async connector calls.

What can cause it:
- Any underlying connector failure surfaced through the async boundary — most commonly a `GeneralException`/`RuntimeException` (DAP code), a `RemoteException` (token/transport/HTTP), or a downstream service error.
- Multiple parallel connector calls where one or more faulted.

## Investigation

1. **Unwrap.** Read the inner exception(s) from the job log / `traces spans get` — the aggregate is never the answer. Take `InnerExceptions[0]`; if it is itself a wrapper (`RemoteException`, another `AggregateException`), recurse to the innermost concrete error.
2. **Re-classify by the inner exception** and switch to the matching playbook:
   - inner `...GeneralException` (DAP-GE) → [connector-general-exception.md](./connector-general-exception.md)
   - inner `...RuntimeException` (DAP-RT) → [connector-runtime-exception.md](./connector-runtime-exception.md)
   - inner `Ipc`/`CoreIpc` `RemoteException` → [connector-remote-exception.md](./connector-remote-exception.md)
   - inner `NullReferenceException` → [connector-null-reference.md](./connector-null-reference.md)
3. If multiple inner exceptions, report each — but the first concrete one is usually the root.

## Resolution

There is no fix for `AggregateException` itself. Resolve the **unwrapped inner exception** using the playbook it maps to (step 2). The aggregate disappears once the underlying connector failure is fixed.
