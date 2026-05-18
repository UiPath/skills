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

> **Hard precondition for steps 2–4:** before running any CLI command or drawing any conclusion, you MUST complete step 1 — either read the connection resource file or explicitly record that no project source is available. CLI evidence (`ping` returning 404, empty `connections list`) is **not sufficient** to distinguish "deleted connection" from "cross-workspace ownership"; only the resource file disambiguates them. Skipping step 1 makes any conclusion at step 2/3 ambiguous and forces the depth-verifier to reject the hypothesis.

1. **Read the connection resource file** — if source code is available, glob `**/connection/<connector-key>/*.json` from the project root to handle all project layouts (standalone, single-folder solution, multi-folder solution — see "Connection Resource File" in [overview.md](../overview.md)). If multiple files match, pick the one whose `resource.key` matches the connection ID in the error. From the file, extract every one of:
   - `spec.connectorName` — the exact display name to use in findings (do NOT guess from the activity package name)
   - `spec.connectorKey` — for CLI queries
   - `resource.name` — the **connection owner**. If this is an email, the connection lives in that user's personal workspace; if it differs from the runner's identity, the connection is cross-workspace.
   - `resource.folders[*].fullyQualifiedName` — the **folder binding**. Compare against the runner's job folder; if they differ, the connection is in a different folder than where the process runs.
   - `resource.key` — the connection ID (UUID). Cross-check against the connection ID in the runtime error and in the workflow source (XAML/code).
   - `spec.authenticationType` — `"AuthenticateAfterDeployment"` means the user must authenticate after creating the connection.

   Record these six values in evidence. If the glob returns zero results AND the project source path is confirmed accessible, only then mark the resource file as "absent" and proceed; the conclusion at the end MUST acknowledge ownership could not be determined and recommend the user provide the resource file.

2. `uip is connections list <connector-key> --folder-key <folder-key>` — check if a connection for that connector exists in the runner's folder. **Only meaningful after step 1**: combined with the resource file's `resource.folders` and `resource.name`, this confirms whether the offending connection lives in a different folder/user than the runner.

3. If found: `uip is connections ping <connection-id>` — verify it is active and enabled

4. **Cross-reference workflow binding** — if the workflow source is available, confirm the connection ID in the activity (`ConnectionId`/`ConnectionKey` attributes in XAML, or equivalent in coded workflows) matches `resource.key` from step 1. A mismatch means the runtime error connection ID is hard-bound elsewhere.

## Resolution

- **If connection not found in folder:** tell the user to create a new connection using the exact `connectorName` from step 1 (e.g., "Create a new **Microsoft OneDrive & SharePoint** connection"). If `authenticationType` is "AuthenticateAfterDeployment", tell the user they will need to authenticate the connection after creating it.
- **If connection belongs to a different user's workspace:** the runner needs their own connection. Create a new connection in the runner's workspace for the same connector, then update the workflow to reference the new connection ID and republish. For shared processes, consider deploying to a shared folder with a shared connection instead of personal workspaces.
- **If connection found but ping fails:** re-authenticate the connection via `uip is connections edit <connection-id>` or through the UI
- **If connection is active but error persists in deployed mode:** check that the robot account has permissions in the folder where the connection resides — it needs at least "Connections.View" permission
- **If this is a solution:** check `bindings_v2.json` to verify the folder binding for connections points to the correct folder. Add folder bindings so the connection resolves per-user when deployed.
