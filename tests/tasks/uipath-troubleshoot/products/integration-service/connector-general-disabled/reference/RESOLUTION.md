# Final Resolution

Root Cause: The Integration Service **connection used by the `Salesforce: HTTP Request` (ConnectorHttpActivity) is disabled**. The activity faults during connection resolution — before any external API call — with `UiPath.IntegrationService.Activities.Runtime.Exceptions.GeneralException: Connection is disabled. Please enable the connection to continue. Error code: DAP-GE-3005.`

What went wrong: When `ConnectorHttpActivity` runs, it first resolves its connection via `ConnectionService.GetConnectionAsync`. The connection (`c4d8f0a2-6b1e-4d93-a7c5-8f201b3e9d40`, "Salesforce - Production") is in a **Disabled** state, so resolution throws `GeneralException` with error code **DAP-GE-3005** and the job faults immediately. This is a connection *state* problem, not a credential, permission, or input problem.

Why: A connection that exists and is bound correctly can still be disabled — manually by an admin, or automatically after repeated authentication failures. `DAP-GE-3005` is specifically "connection disabled," distinct from `DAP-GE-3000` ("failed to retrieve connection" — invalid / no access / missing permission).

Evidence:

### Orchestrator
- Process **OrderSync** (release version 10042), folder **Shared** (`1965a46b-db4e-469e-aaaa-7e0b379cb34d`), job `3f8a1c7e-9b2d-4e6a-8c11-5d7e9f0a1b2c` ended **Faulted**, host **MOCK-HOST**, `ErrorCode: Robot`.
- Job `Info` + error-level log carry the verbatim signature `GeneralException: Connection is disabled. Please enable the connection to continue. Error code: DAP-GE-3005.` with the `ConnectorHttpActivity.ExecuteAsync` → `ConnectorActivityBase.ResolveConnectionAsync` → `ConnectionService.GetConnectionAsync` stack.

### Integration Service
- Connection `c4d8f0a2-6b1e-4d93-a7c5-8f201b3e9d40` ("Salesforce - Production", connector `uipath-salesforce`) shows `IsActive: false`, `State: Disabled`. `uip is connections ping` on it fails ("connection is disabled").

Immediate fix:
1. **Re-enable the connection.** In the Integration Service UI (or `uip is connections edit c4d8f0a2-6b1e-4d93-a7c5-8f201b3e9d40`), enable "Salesforce - Production", then re-run the job.
   - If the connection auto-disabled after auth failures, re-authenticate it (re-authorize the app in Salesforce, then reconnect) before enabling.

Preventive fix:
1. Monitor connection health for connections used by unattended processes so a disabled/expired connection is caught before the next scheduled run.
2. For shared/unattended automations, prefer a connection owned in the runner's shared folder over a personal one, reducing the chance an owner-side change disables it silently.

Must NOT attribute to: a missing/invalid connection or missing `Connections.View` permission (that would be `DAP-GE-3000`, not `DAP-GE-3005`); expired credentials alone (the state is *disabled*, which must be re-enabled regardless of token state); a workflow logic bug, bad input, or the external Salesforce API (the fault is before any API call).
