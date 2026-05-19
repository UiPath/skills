---
confidence: high
---

# GSuite Drive — File or folder not found (HTTP 404)

## Context

What this looks like — any of the following messages, all originating from a Google API `HTTP 404 NotFound` response:

- `File not found: <id>. [404]`
- `The service drive has thrown an exception. HttpStatusCode is NotFound. File not found`
- `The service sheets has thrown an exception. HttpStatusCode is NotFound. Requested entity was not found.`
- `The resource was not found.`

The job faults synchronously the moment the activity tries to resolve the resource.

What activities can produce this error:
Most `UiPath.GSuite.Activities` activities that take a Drive file, folder, spreadsheet, or document identifier (ID, URL, path, or browse selection) — for example: `GetFileFolderConnections`, `GetFileFolderInfoConnections`, `DownloadFileConnections`, `MoveFileConnections`, `CopyFileConnections`, `DeleteFileOrFolderConnections`, `RenameFileFolderConnections`, `ShareFileFolderConnections`, `UploadFilesConnections` (when targeting an existing parent folder), and any Sheets/Docs activity that opens a spreadsheet or document by ID.

What can cause it:
- The configured ID, URL, or path resolves to a Drive resource that no longer exists, has been moved to Trash, has been permanently deleted, or was never accessible to the authenticated account. This is the only cause the error can describe — Google has authoritatively returned `404 NotFound` for the request.

> **Different cause, similar message — do not apply this playbook:**
> - **`ApplyFileLabelsConnections`** can throw `The resource was not found. Please make sure that the selected label is enabled for "Drive and Docs".` That is a label-configuration issue, not a missing file.
> - **`The document with the name <name> was not found in the specified folder.`** is a name-based lookup miss (no document with that title in the parent), not a 404 against an ID. Treat as a separate scenario.
> - **`File does not exist.`** (`FileNotFoundException`) refers to a missing **local filesystem** path (e.g., an upload source path or service-account key file), not a Drive resource.

## Resolution

The error is unambiguous; no further investigation is needed. Stop the investigation and ask the user to verify the target resource:

1. **Confirm the file or folder still exists** in Google Drive (it may have been deleted, trashed, or moved out of the visible scope).
2. **Confirm the configured identifier is correct** — the ID, URL, or path on the activity must point to the intended resource. Common mistakes: a stale ID copied from an older version of the file, a URL pointing to a different account's resource, a path that no longer matches the actual folder structure.
3. **Confirm the connection's authenticated account has access** to the resource. A file owned by another user that was never shared with this account will also surface as `404 NotFound`.

If the user confirms the resource exists, is reachable in the Drive UI under the same account, and the identifier is correct, the cause is outside the activity — escalate (connection scope, domain policy, sharing) rather than continue under this playbook.
