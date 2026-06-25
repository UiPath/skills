# Final Resolution

Root Cause: The Integration Service connection used by the `Workday: New Invoice (sample)` (ConnectorTriggerActivity) **cannot refresh its OAuth token** — the identity provider returned `invalid_grant`. The connector executor surfaces this across the IPC boundary as `UiPath.Ipc.RemoteException: Could not obtain access token. (invalid_grant)`, and the job faults.

What went wrong: Connector activities run out-of-process; a fault in the executor is wrapped in `RemoteException`. The `RemoteException` class itself is generic — the **operative signal is the unwrapped inner message**: `Could not obtain access token. (invalid_grant)`. `invalid_grant` means the OAuth refresh token is no longer valid (expired, revoked, or the authorizing user's access was withdrawn), so a new access token can't be minted and the connector call never reaches the external service.

Why: This is an authentication-state problem on the connection, not a connectivity, input, or workflow problem. `invalid_grant` specifically points at the refresh-token grant being rejected by the IdP.

Evidence:

### Orchestrator
- Process **InvoiceTrigger** (release version 7715), folder **Shared** (`1965a46b-db4e-469e-aaaa-7e0b379cb34d`), job `9e1f3a5c-7b2d-4f6e-8a0c-1d3b5f7e9a2c` ended **Faulted**, host **MOCK-HOST**, `ErrorCode: Robot`.
- Job `Info` + error-level log carry `UiPath.Ipc.RemoteException: Could not obtain access token. (invalid_grant)` with the `ConnectorTriggerActivity.DebugExecuteAsync` → `ExecuteAsync` stack (no `DAP-` code — this is the IPC-boundary wrapper).

### Integration Service
- Connection `a7c3e1f9-4b6d-42a8-9c05-3e8f1d0b7a62` ("Workday - Finance", connector `uipath-workday`) pings as `IsActive: false`, `State: AuthenticationFailed`, message `Could not obtain access token. (invalid_grant)`.

Immediate fix:
1. **Re-authenticate the connection.** Reconnect "Workday - Finance" in the Integration Service UI (or `uip is connections edit a7c3e1f9-4b6d-42a8-9c05-3e8f1d0b7a62`). If the authorizing user revoked app access (or left the org), re-authorize the app in Workday first, or have a current user re-own/re-authenticate the connection, then re-run the job.

Preventive fix:
1. Monitor connection auth health so an `invalid_grant` is caught before the next scheduled trigger run.
2. For unattended automations, own the connection with a service/shared identity that won't lose access when an individual user leaves, to avoid `invalid_grant` from revoked personal grants.

Must NOT attribute to: a generic network / transport / IPC crash, a UiPath platform outage, a missing or disabled connection (the connection exists; it is an *auth* failure, not `DAP-GE-3005`), a `DAP-RT` operation error, or a workflow-logic bug. The cause is the unwrapped `invalid_grant` token-refresh failure. Do NOT stop at "RemoteException" without unwrapping to the inner message.
