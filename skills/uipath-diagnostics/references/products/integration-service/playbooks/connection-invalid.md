---
confidence: high
---

# Connection Invalid or No Access

## Context

What this looks like:
- Error message: "connection [name] is invalid or you do not have access"
- Maestro error code 102002 (IntSvcOperationFailed) or 102008 (GetConnectionInvalidInputError)
- Process fails immediately when trying to use an Integration Service connection

What can cause it:
- Connection does not exist in the folder where the process runs
- Connection exists in a different user's personal workspace — the process was published with a connection that belongs to another user and is not accessible from the runner's workspace
- Connection exists but is disabled or in an error state
- Robot account (deployed mode) lacks folder permissions to access the connection — debug mode works because it runs under the user's identity
- Connection was deleted or renamed after the process was published
- Folder bindings (`bindings_v2.json`) point to a different folder than where the connection resides

What to look for:
- The connection name and connector key in the error message or project files
- Whether the issue occurs in debug mode, deployed mode, or both
- Whether the process was published from a different user's workspace

## Investigation

1. **Read the connection resource file** — if source code is available, find and read the connection JSON (see "Connection Resource File" in [overview.md](../overview.md) for path pattern and field reference). Use `spec.connectorName` as the exact display name in all findings — do NOT guess from the activity package name.
2. `uip is connections list <connector-key> --folder-key <folder-key>` — check if a connection for that connector exists in the runner's folder
3. If found: `uip is connections ping <connection-id>` — verify it is active and enabled

## Resolution

- **If connection not found in folder:** tell the user to create a new connection using the exact `connectorName` from step 1 (e.g., "Create a new **Microsoft OneDrive & SharePoint** connection"). If `authenticationType` is "AuthenticateAfterDeployment", tell the user they will need to authenticate the connection after creating it.
- **If connection belongs to a different user's workspace:** the runner needs their own connection. Create a new connection in the runner's workspace for the same connector, then update the workflow to reference the new connection ID and republish. For shared processes, consider deploying to a shared folder with a shared connection instead of personal workspaces.
- **If connection found but ping fails:** re-authenticate the connection via `uip is connections edit <connection-id>` or through the UI
- **If connection is active but error persists in deployed mode:** check that the robot account has permissions in the folder where the connection resides — it needs at least "Connections.View" permission
- **If this is a solution:** check `bindings_v2.json` to verify the folder binding for connections points to the correct folder. Add folder bindings so the connection resolves per-user when deployed.
