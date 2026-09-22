# Final Resolution

Root Cause: The robot running the job **does not have `Connections.View` permission in the folder where the Integration Service connection lives**, so the `Google Drive: Get File or Folder` (ConnectorActivity) cannot resolve its connection and faults during connection resolution with `UiPath.IntegrationService.Activities.Runtime.Exceptions.GeneralException: ... Error code: DAP-GE-3000.`

> This scenario's error text was captured from a **real Orchestrator faulted job** — a Google Drive `ConnectorActivity` published to the **Shared** folder and run by a robot, while the connection it references lives in a **different folder** (`dea5d8d6-…`, a personal workspace) the robot cannot read. The signature, the `Connections.View` guidance, and the stack frames are verbatim (identities scrubbed).

What went wrong: When the `ConnectorActivity` runs, `ConnectionService.GetConnectionAsync` → `ConnectorActivityBase.BuildExecutionParametersAsync` tries to resolve the connection. The connection exists, but it is bound to folder `dea5d8d6-…`, and the executing robot identity lacks `Connections.View` there. Resolution fails before any Google API call, raising `GeneralException` with code **DAP-GE-3000**. The message states the fix verbatim: *"Ask your administrator to grant Connections.View on that folder, or move the connection to a folder where the robot has the required permission."*

Why: This is the cross-folder / RBAC variant of `DAP-GE-3000` (distinct from `DAP-GE-3005`, which is a *disabled* connection). The connection is neither disabled nor invalid — the robot's identity simply cannot see it in the folder where it is bound. Debug runs under the user's identity would succeed; the deployed robot account fails.

Evidence:

### Orchestrator
- Process **DriveSync**, folder **Shared** (`1965a46b-db4e-469e-aaaa-7e0b379cb34d`), job `f5e5eaa8-ce88-482f-9506-01394caa3967` ended **Faulted**, host **MOCK-HOST**, run by robot identity `robot_account`, `ErrorCode: Robot`.
- Job `Info` + error-level log carry the verbatim signature: `GeneralException: Failed to retrieve connection. ... The robot does not have the Connections.View permission in the folder where this connection lives. ... (Folder: dea5d8d6-…) Error code: DAP-GE-3000.` with `ConnectionService.GetConnectionAsync` → `ConnectorActivityBase.BuildExecutionParametersAsync` → `ConnectorActivity.ExecuteAsync`.
- The connection lives in folder `dea5d8d6-…` (a different folder than the **Shared** folder the job ran in).

Immediate fix:
1. **Grant the robot `Connections.View` on the connection's folder** (`dea5d8d6-…`), OR
2. **Move/recreate the connection in a folder the robot can access** (e.g. create a Google Drive connection in the **Shared** folder where the process runs), then re-run the job.

Preventive fix:
1. For shared/unattended automations, keep connections in the same folder the process is deployed to (or a parent folder the robot inherits), instead of a user's personal workspace.
2. Verify connection-folder permissions for the robot account before publishing a process that uses Integration Service connectors.

Must NOT attribute to: a *disabled* connection (`DAP-GE-3005`); an invalid / deleted / nonexistent connection; expired credentials or an OAuth / `invalid_grant` auth failure; a `DAP-RT` operation error or a downstream provider (404/etc.); an IPC `RemoteException`; or a workflow-logic bug. The connection resolves for someone — the robot just lacks `Connections.View` in its folder.
