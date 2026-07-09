---
confidence: high
---

# Connector Activity — GeneralException (DAP-GE)

## Context

What this looks like — robot exception `UiPath.IntegrationService.Activities.Runtime.Exceptions.GeneralException` with a `DAP-GE-` error code. The job faults at the moment the connector activity tries to resolve its connection (before the external API is called). The message carries the code:

- `Failed to retrieve connection. Consider using a different connection. Error code: DAP-GE-3000.` — this base sentence (including "Consider using a different connection") is **generic boilerplate that appears on EVERY DAP-GE-3000 regardless of sub-cause**. It is NOT evidence that the connection was deleted or is broken — do not diagnose from it. The `-`-delimited detail that follows the code is the classifier that names the real cause:
  - `- Connection [<id>] is invalid or you do not have access to it` — connection missing, deleted, or not accessible from the runner's identity/workspace.
  - `- User '<user-id>' does not have Connections.View permissions in [Connection: <id>]` — RBAC: the runner (robot account in deployed mode) lacks `Connections.View` in the folder where the connection lives.
  - `- Bad Gateway` (or other upstream text) — Integration Service / Identity returned a 5xx while resolving the connection.
- `Connection is disabled. Please enable the connection to continue. Error code: DAP-GE-3005.` — the connection exists and is bound correctly but is disabled.

Which activities produce this — the generic Integration Service connector activities, regardless of which connector they wrap:
- **ConnectorActivity** — any connector operation (per-connector classes are generated, e.g. `UiPath.Salesforce.IntegrationService.Activities.*`, but the runtime base is `ConnectorActivity`).
- **ConnectorHttpActivity** — the connector "HTTP request" / custom-call activity.
- **ConnectorTriggerActivity** — the trigger's debug/sample lookup resolves the same connection.
- **ConnectorPersistenceActivity** — long-running connector waits.

What can cause it:
- **DAP-GE-3000, invalid/no-access:** connection deleted/renamed after publish; connection lives in a different user's personal workspace than the runner; folder bindings (`bindings_v2.json`) point at the wrong folder.
- **DAP-GE-3000, Connections.View:** robot account lacks the permission in the connection's folder. Debug mode works (user identity) but deployed mode fails (robot identity).
- **DAP-GE-3000, Bad Gateway / 5xx:** transient Integration Service / Identity outage — retryable, not a config error.
- **DAP-GE-3005, disabled:** someone disabled the connection, or it auto-disabled after repeated auth failures.

## Investigation

The error code already names the cause class; the remaining work is confirming ownership/permission. Read the connection identity first.

1. **Read the connection resource file** — glob `**/connection/<connector-key>/*.json` from the project root (see "Connection Resource File" in [overview.md](../overview.md)). Extract `resource.key` (connection ID — must match the ID in the error), `resource.name` (owner), `resource.folders[*].fullyQualifiedName` (binding), `spec.connectorName`. This is the only way to distinguish "deleted" from "cross-workspace ownership" for DAP-GE-3000 invalid/no-access. If no source is available, say so and proceed on the error text.
2. For **DAP-GE-3005** the cause is unambiguous — skip to Resolution.
3. `uip is connections ping <connection-id>` — confirms current state (disabled / not accessible).
4. For the **Connections.View** detail: identify whether the failing identity is a robot account (deployed) vs the user (debug). Robot accounts often lack the permission the user has.

## Resolution

- **DAP-GE-3005 (disabled):** re-enable the connection in the Integration Service UI (or `uip is connections edit <connection-id>`). If it auto-disabled, re-authenticate — see [connection-auth-expired.md](./connection-auth-expired.md).
- **DAP-GE-3000, invalid / no access / cross-workspace:** this is the activity-side surfacing of [connection-invalid.md](./connection-invalid.md) — follow its Resolution (create a connection in the runner's workspace and repoint the activity, or deploy to a shared folder with a shared connection).
- **DAP-GE-3000, Connections.View:** grant the robot account at least `Connections.View` in the folder where the connection resides, **or** move/recreate the connection in a folder the robot can access (the runtime message names the connection's folder GUID and states both options verbatim).
- **DAP-GE-3000, Bad Gateway / 5xx:** transient platform error — retry the job. Do NOT recreate the connection, re-bind folders, or re-publish: the connection is fine, only the platform's resolution call momentarily failed. If it persists, check Integration Service / Identity status before treating it as a config problem.
