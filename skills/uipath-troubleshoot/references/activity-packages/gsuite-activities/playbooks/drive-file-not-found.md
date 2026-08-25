---
confidence: high
---

# GSuite — Resource not found / item does not resolve (HTTP 404)

## Context

What this looks like — any of the following messages, all meaning the target the activity tried to address does not resolve:

- `File not found: <id>. [404]`
- `The service drive has thrown an exception. HttpStatusCode is NotFound. File not found`
- `The service sheets has thrown an exception. HttpStatusCode is NotFound. Requested entity was not found.`
- `The service gmail has thrown an exception. HttpStatusCode is NotFound. ...` (Gmail message by ID)
- `The resource was not found.` — the translated form of any Google `HTTP 404 NotFound` (Drive file/folder, spreadsheet, document, **or Gmail message by ID**).
- `Cannot find item configured with connection ` `` `<connectionId>` `` `.` — the activity's configured item (spreadsheet/file selected via the connection browser) could not be resolved by ID.
- ``Cannot find item configured with connection `<connectionId>` at path `<path>`.`` — same, when resolution fell back to a path (`FullPath` / `FullPathHint`) and that path doesn't exist in Drive either.

The job faults synchronously the moment the activity tries to resolve the resource.

What activities can produce this error:
Any `UiPath.GSuite.Activities` activity that addresses a resource by identifier:
- **Drive / Sheets / Docs by ID, URL, or path** — `GetFileFolderConnections`, `GetFileFolderInfoConnections`, legacy `GetFileInfo`, `DownloadFileConnections`, `MoveFileConnections`, `CopyFileConnections`, `DeleteFileOrFolderConnections`, `RenameFileFolderConnections`, `ShareFileFolderConnections`, `UploadFilesConnections` (existing parent), and any Sheets/Docs activity that opens a spreadsheet or document by ID. The `Cannot find item configured with connection ...` form comes from activities whose target was picked through the connection's item browser (typically Sheets/Drive `*Connections`). Legacy `GetFileInfo` surfaces the 404 **raw** (`File not found: <id>. [404]`) and faults the job, rather than swallowing it the way the modern `*Connections` variants can — a faulted job, not a null result, is the expected legacy symptom.
- **Gmail message by ID** — `GetEmailByIdConnections` ("Get Email By Id") when the configured `EmailId` doesn't exist; trigger fetches (`Gmail.Triggers.NewEmailReceived` / `EmailSent`) when the sampled message was deleted between selection and retrieval.

What can cause it:
- The configured ID, URL, or path resolves to a resource that no longer exists, has been moved to Trash, has been permanently deleted, or was never accessible to the authenticated account. Google has authoritatively returned `404 NotFound`.
- For the `Cannot find item configured with connection ...` forms: the browser-selected item ID is stale (the file/spreadsheet was deleted or moved) and no valid path fallback exists.
- For Gmail by ID: the message ID is stale (copied from an older run, or the message was deleted/trashed), or it belongs to a different mailbox than the one the connection authenticates.

> **Different cause, similar message — do not apply this playbook:**
> - **`Permission to the resource was denied.`** / **`Invalid authentication credentials.`** (403 / 401) mean access was *denied*, not that the resource is missing — use [connection-and-auth-failures.md](./connection-and-auth-failures.md). (Note: a resource that exists but was never shared with the account can surface as either 404 or 403, depending on the API — check the status class.)
> - **`ApplyFileLabelsConnections`** can throw `The resource was not found. Please make sure that the selected label is enabled for "Drive and Docs".` That is a label-configuration issue, not a missing file.
> - **`The document with the name <name> was not found in the specified folder.`** is a name-based lookup miss (no document with that title in the parent), not a 404 against an ID. Treat as a separate scenario.
> - **`File does not exist: <path>`** (`FileNotFoundException`) refers to a missing **local filesystem** path (e.g., a `SendEmail` attachment, an upload source path, or a service-account key file), not a Drive resource — use [invalid-or-null-input.md](./invalid-or-null-input.md).

## Resolution

The error is unambiguous; no further investigation is needed. Stop the investigation and ask the user to verify the target resource:

1. **Confirm the resource still exists** under the connection's account — the Drive file/folder, spreadsheet, or document in Google Drive, or the Gmail message in the mailbox (it may have been deleted, trashed, or moved out of the visible scope).
2. **Confirm the configured identifier is correct** — the ID, URL, path, or Gmail `EmailId` on the activity must point to the intended resource. Common mistakes: a stale ID copied from an older run, a URL or message ID pointing to a different account's resource, a path that no longer matches the actual folder structure. For the `Cannot find item configured with connection ...` forms, re-select the item through the connection browser so a fresh ID is captured.
3. **Confirm the connection's authenticated account has access** to the resource. A resource owned by another user that was never shared with this account can also surface as `404 NotFound`.

If the user confirms the resource exists, is reachable in the Google UI under the same account, and the identifier is correct, the cause is outside the activity — escalate (connection scope, domain policy, sharing — see [connection-and-auth-failures.md](./connection-and-auth-failures.md)) rather than continue under this playbook.
