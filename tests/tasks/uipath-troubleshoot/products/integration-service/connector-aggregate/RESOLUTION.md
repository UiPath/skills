# Final Resolution

Root Cause: A transient upstream **502 Bad Gateway** while the `Salesforce: Create Record` (ConnectorActivity) was resolving its Integration Service connection. The async failure is wrapped in `System.AggregateException`, whose **inner** exception is the real cause: `UiPath.IntegrationService.Activities.Runtime.Exceptions.GeneralException: Failed to retrieve connection. Consider using a different connection. - Bad Gateway Error code: DAP-GE-3000.`

What went wrong: Connector activities run asynchronously, so a fault is surfaced as `System.AggregateException` ("One or more errors occurred."). The aggregate itself is not the cause — `InnerExceptions[0]` is the `GeneralException` with code **DAP-GE-3000** and detail **Bad Gateway**, meaning Integration Service / Identity returned a transient 5xx while resolving the connection. The connection is not misconfigured; the platform momentarily failed to return it.

Why: `AggregateException` must always be unwrapped — the inner exception carries the DAP code and the actionable detail. Here the unwrapped cause is transient (Bad Gateway), so the correct response is to retry, not to change configuration.

Evidence:

### Orchestrator
- Process **LeadSync** (release version 30156), folder **Shared** (`1965a46b-db4e-469e-aaaa-7e0b379cb34d`), job `d3b8a4f2-9e5a-4c7d-b2e3-8f1c6d4a0b59` ended **Faulted**, host **MOCK-HOST**, `ErrorCode: Robot`.
- Job `Info` + error-level log: `System.AggregateException: One or more errors occurred. (...)` with the inner (`--->`) `GeneralException: Failed to retrieve connection. Consider using a different connection. - Bad Gateway Error code: DAP-GE-3000.` at `ConnectionService.GetConnectionAsync` → `ConnectorActivity.ExecuteAsync`.

Immediate fix:
1. **Retry the job.** The unwrapped cause is a transient Bad Gateway (502) from Integration Service / Identity during connection resolution — re-run the job.
2. If it recurs consistently, check Integration Service / Identity status before treating it as a configuration problem; only then investigate the connection itself.

Preventive fix:
1. Add a retry (e.g. Retry Scope / Orchestrator job retry) around connector activities so transient 5xx connection-resolution errors self-recover instead of faulting the job.

Must NOT attribute the root cause to `System.AggregateException` itself (it is only the async wrapper — the inner exception is the cause), nor stop at "one or more errors occurred" without unwrapping. Must NOT attribute it to a disabled connection (`DAP-GE-3005`), an invalid/no-access connection, an auth/`invalid_grant` failure, a workflow-logic bug, or bad input. The inner detail is specifically a transient Bad Gateway.
