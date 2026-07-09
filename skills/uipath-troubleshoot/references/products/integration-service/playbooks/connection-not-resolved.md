---
confidence: high
---

# Connection Not Resolved (DAP-GE-3000 / DAP-GE-3005 / DAP-RT-1002)

> **Fault bucket: 👤 A — Customer-resolvable.** A connection/binding/permission problem on the customer's side (deleted, disabled, unbound, or wrong-folder connection). Lead with: "This is a connection configuration issue on your side — here's what to reselect/re-enable/rebind." See [dap-error-codes-reference.md](../dap-error-codes-reference.md#fault-ownership--the-two-bucket-decision).

## Context

What this looks like — three related codes, all meaning IS could not resolve a usable connection before calling the provider:

| Code | Name | Specific cause |
|---|---|---|
| `DAP-GE-3000` | FailedToGetConnection | Connection could not be retrieved — deleted, inaccessible, or wrong connection selected |
| `DAP-GE-3005` | ConnectionDisabled | Connection exists but is disabled; user must re-enable it |
| `DAP-RT-1002` | ConnectionIdNull | No connection ID on the activity — unconfigured or broken binding |

What can cause it (cause IDs map to Resolution steps below):
- **CA001** — Connection was deleted or renamed after the process was published (`3000`)
- **CA002** — Connection is in a different user's personal workspace or a folder the runner cannot reach (`3000`)
- **CA003** — Runner's robot account lacks permission on the folder holding the connection (`3000`)
- **CA004** — Connection was manually disabled, or auto-disabled after repeated auth failures (`3005`)
- **CA005** — Activity has no connection bound — published without selecting a connection, or the binding was lost in migration (`1002`)

What to look for:
- `ConnectionId` in the customEvent — present for `3000`/`3005`, **null/absent for `1002`** (that absence is itself the diagnosis)
- Whether the failure is debug-only (runs under user identity) or deployed (runs under robot account — may lack folder permission)

> The Maestro-surfaced view of the same root causes is [connection-invalid.md](./connection-invalid.md) ("connection is invalid or you do not have access"). Prefer this playbook when a DAP code is present.

## Investigation

1. **Read the connection resource file** — if source code is available, glob `**/connection/<connector-key>/*.json` from the project root (see "Connection Resource File" in [overview.md](../overview.md)). Extract `resource.key` (connection ID), `resource.name` (owner), `resource.folders[*].fullyQualifiedName` (binding), and `spec.connectorName`.
2. Branch on the code:
   - **`DAP-RT-1002` (ConnectionIdNull):** confirm the activity in the workflow source has no `ConnectionId`/`ConnectionKey` bound. The fix is re-binding, not connection health — skip the ping checks.
   - **`DAP-GE-3000` (FailedToGetConnection):** `uip is connections list <connector-key> --folder-key <folder-key>` — check whether the connection exists in the runner's folder. Compare the resource file's `resource.folders` and `resource.name` against the runner's job folder/identity to distinguish "deleted" from "cross-workspace / wrong folder."
   - **`DAP-GE-3005` (ConnectionDisabled):** `uip is connections ping <connection-id>` — confirm it resolves but reports disabled.
3. **Caller identity** — determine whether the failure is in debug (user) or deployed (robot account) mode. A robot account may lack `Connections.View` in the connection's folder even when the connection exists.

## Resolution

- **`CA005` — `DAP-RT-1002`:** open the activity, select the correct connection, and republish. If lost during package migration, re-bind every affected activity.
- **`CA001` — `DAP-GE-3000`, connection missing in folder:** create a connection using the exact `connectorName` from the resource file; if `authenticationType` is `AuthenticateAfterDeployment`, authenticate it after creating.
- **`CA002` — `DAP-GE-3000`, cross-workspace / wrong folder:** create a connection in the runner's workspace (or a shared folder for shared processes), update the workflow to reference its ID, and republish.
- **`CA003` — `DAP-GE-3000`, robot lacks permission:** grant the robot account at least `Connections.View` in the folder where the connection resides.
- **`CA004` — `DAP-GE-3005`:** re-enable the connection in the Integration Service UI. If it was auto-disabled after auth failures, re-authenticate first (see [connection-auth-expired.md](./connection-auth-expired.md)) or it will disable again.
