# Final Resolution

Root Cause: A `For Each` activity iterates the output of an Integration Service connector "query records" operation that returned **null** (no result set), so dereferencing it throws `System.NullReferenceException` and the job faults.

What went wrong: The faulted activity is `UiPath.Core.Activities.ForEach\`1` parameterized over the connector output type `UiPath.IntegrationService.Activities.SWEntities.C5D2F5448FB_executeQuery_List...` — i.e. a `For Each` over the result of a connector query (an `executeQuery` / "List records" operation). The collection it was given is `null` (the operation returned no body / null rather than an empty list), and `ForEachBase.ContinueExecuting` dereferences it, raising `NullReferenceException`.

Why: `NullReferenceException` here is opaque — there is no error code or message detail. The stack frame is the signal: the generic `ForEach\`1` is specialized on an `IntegrationService.Activities.SWEntities.*_executeQuery_List` type, which only happens when the loop iterates a connector operation's output. The workflow does not guard the connector output for null/empty before enumerating it.

Evidence:

### Orchestrator
- Process **ContactImport** (release version 14098), folder **Shared** (`1965a46b-db4e-469e-aaaa-7e0b379cb34d`), job `c2a7f3e1-8d49-4b6c-a1f2-7e0d5c3b9a48` ended **Faulted**, host **MOCK-HOST**, `ErrorCode: Robot`.
- Job `Info`: `System.NullReferenceException: Object reference not set to an instance of an object.` at `ForEach<Object> "For Each contact"` in `ContactImport.xaml`, via `ForEachBase\`1.ContinueExecuting`.
- Error-level log names the faulted activity type: `ForEach\`1[[...IntegrationService.Activities.SWEntities.C5D2F5448FB_executeQuery_List...]]` — a `For Each` over a connector query output.

### Integration Service (Runtime)
- The connector query operation feeding the `For Each` returned `null` (no rows / null body) instead of an empty collection, so the loop's collection reference is null.

Immediate fix:
1. **Guard the connector output before the `For Each`.** Check the query result for null / empty (e.g. `If result IsNot Nothing AndAlso result.Count > 0`) before iterating, so a query that returns no records skips the loop instead of faulting.
2. If the connector activity's output is not assigned to the variable the `For Each` reads, map the connector operation's result to that variable.

Preventive fix:
1. Treat "no records returned" as a normal outcome for query/list connector operations — always null/empty-guard their output before enumeration.
2. If a non-empty result is required, validate it explicitly and raise a clear business error instead of letting a raw `NullReferenceException` fault the job.

Must NOT attribute to: a disabled / invalid / no-access connection (`DAP-GE-*`), an auth / token (`invalid_grant`) failure, a `DAP-RT` operation error, or an IPC `RemoteException` — there is no DAP code and no connection error here. The connector call itself did not error; the fault is the workflow dereferencing a null/empty connector result. Do NOT invent a specific upstream value not present in the evidence.
