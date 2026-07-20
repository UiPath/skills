# Resolution — DriveFileCreator (Shared)

## Fault
The last job in folder **Shared** (`DriveFileCreator`, job `6c8b1949-2603-437d-86a6-6b82b989fd6a`, Unattended on `MOCK-HOST`) ended **Faulted** ~4s after start. It ran a single GSuite **Create Folder** (`UiPath.GSuite.Activities.CreateFolderConnections`) activity.

## Cause
The destination (My Drive root) **already contains more than one item named `dupe-folder`**, and the activity's `ConflictResolution` required resolving to a single existing item (`UseExisting`). Because the name is ambiguous — multiple matches — the activity could not resolve it and threw:

```
UiPath.GSuite.Exceptions.GSuiteException: Multiple items with the name dupe-folder found in the specified folder.
   at UiPath.GSuite.Drive.Services.DriveServiceProxy.CreateFolderAsync(...)
   at UiPath.GSuite.Activities.CreateFolderConnections.SafeExecuteAsync(...)
```

This is a **name-ambiguity conflict** raised synchronously by the activity. The connection authenticated and the parent folder resolved fine; it is not a 404/resource-not-found, auth/connection, invalid-range, or transient failure. (Google Drive permits multiple items with the same name in one folder, so name-based resolution becomes ambiguous once duplicates exist.) The Google Drive and Sheets connections serving folder Shared are Enabled and valid — a connection list confirms this, so the connection is not the problem.

## Resolution
Make the name resolvable to a single item, by any of:

- **Remove or rename** the duplicate `dupe-folder` item(s) so only one (or none) remains, then re-run; or
- **Target the item by its Drive ID** instead of by name (unambiguous); or
- Use a `ConflictResolution` that does not require selecting a single existing match (e.g. `AddSeparate` to always create new, or `Rename`).

Must NOT attribute to: an HTTP 404 / resource-not-found, an invalid/inaccessible connection or auth failure, a null/empty or unparseable range, a Sheets "sheet name already exists" conflict (that is a different activity), rate limiting / 429, a transient 5xx, or a per-request timeout — the activity threw because the configured name matched multiple items and `ConflictResolution` could not disambiguate.
