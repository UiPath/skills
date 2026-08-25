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

> **Hard precondition for steps 2–4:** before drawing a conclusion, complete step 1 — either read the connection resource file or explicitly record that no project source is available. A `ping` 404 by itself is ambiguous. When source is absent, disambiguate with the exact-ID lookup plus folder-scoped and tenant-visible connection inventories; only call the inventory tenant-wide when the active identity has that scope. `ResourceOverwrites[*].EntityDisplayName` is a deployment display label, **not an ownership field** — never infer cross-workspace ownership from its mismatch with the runner identity.

1. **Read the connection resource file** — if source code is available, glob `**/connection/<connector-key>/*.json` from the investigation working directory; if the project folder is inside a solution, ALSO glob from the project folder's **parent** — in a solution, `resources/` sits at the solution root beside the project folder (see "Connection Resource File" in [overview.md](../overview.md) for all layouts). Only after both globs return zero may the resource file be marked absent. If multiple files match, pick the one whose `resource.key` matches the connection ID in the error. From the file, extract every one of:
   - `spec.connectorName` — the exact display name to use in findings (do NOT guess from the activity package name)
   - `spec.connectorKey` — for CLI queries
   - `resource.name` — the **connection owner**. If this is an email, the connection lives in that user's personal workspace; if it differs from the runner's identity, the connection is cross-workspace.
   - `resource.folders[*].fullyQualifiedName` — the **folder binding**. Compare against the runner's job folder; if they differ, the connection is in a different folder than where the process runs.
   - `resource.key` — the connection ID (UUID). Cross-check against the connection ID in the runtime error and in the workflow source (XAML/code).
   - `spec.authenticationType` — `"AuthenticateAfterDeployment"` means the user must authenticate after creating the connection.

   Record these six values in evidence. If the glob returns zero results AND the project source path is confirmed accessible, only then mark the resource file as "absent" and proceed to the API evidence below. Do not substitute a job's `ResourceOverwrites[*].EntityDisplayName` for `resource.name`; the former is only the display label captured at deployment.

2. Query the exact ID first: `uip is connections list --connection-id <connection-id>` and `uip is connections ping <connection-id>`. Then run `uip is connections list <connector-key> --folder-key <bound-folder-key>` when the connector key is known. If source is absent, also inspect the bound folder and, only when the active identity has tenant-wide visibility, `uip is connections list` for the exact ID and connector. These checks are meaningful after step 1 records whether source was found.

3. If found: `uip is connections ping <connection-id>` — verify it is active and enabled

4. **Cross-reference workflow binding** — if the workflow source is available, confirm the connection ID in the activity (`ConnectionId`/`ConnectionKey` attributes in XAML, or equivalent in coded workflows) matches `resource.key` from step 1. A mismatch means the runtime error connection ID is hard-bound elsewhere.

5. **Disambiguate the 404 — "deleted" vs "cross-workspace."** A `ping` 404 means the connection is *not resolvable from the runner's context*, NOT necessarily *deleted*. Use the strongest corroborating evidence available:

   | Evidence with exact-ID 404 | Cause |
   |----------------------------|-------|
   | Exact ID is absent from the bound folder **and** from a connection inventory known to be tenant-wide; the connector is also absent there | Connection deleted or renamed after publish |
   | Exact ID is positively listed in another user/workspace/folder, or current resource/binding evidence positively locates it there | Cross-workspace / wrong-folder connection |
   | Inventory scope is only the runner's visible context, or neither branch has positive corroboration | Ambiguous — report deleted vs inaccessible as alternatives and request source/admin-scope evidence |

   Do NOT report "connection deleted" on a 404 alone, and do NOT report cross-workspace ownership from a display-name mismatch alone. Positive current location evidence beats a stale deployment label. When the exact ID is absent from both its bound folder and a genuinely tenant-wide inventory, classify it as deleted; when the ID is positively found elsewhere, classify it as cross-workspace.

## Resolution

- **If the connection is deleted:** create a new connection for the same connector, update the activity/binding to the new connection ID, republish, and rerun. Use the exact `connectorName` from source or API evidence; if connector identity is unavailable, say so rather than guessing. If `authenticationType` is "AuthenticateAfterDeployment", authenticate it after creating.
- **If connection belongs to a different user's workspace:** the runner needs their own connection. Create a new connection in the runner's workspace for the same connector, then update the workflow to reference the new connection ID and republish. For shared processes, consider deploying to a shared folder with a shared connection instead of personal workspaces.
- **If connection found but ping fails:** re-authenticate the connection via `uip is connections edit <connection-id>` or through the UI
- **If connection is active but error persists in deployed mode:** check that the robot account has permissions in the folder where the connection resides — it needs at least "Connections.View" permission
- **If this is a solution:** check `bindings_v2.json` to verify the folder binding for connections points to the correct folder. Add folder bindings so the connection resolves per-user when deployed.
