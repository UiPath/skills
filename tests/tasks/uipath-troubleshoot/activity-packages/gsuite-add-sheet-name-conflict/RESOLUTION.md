# Resolution — SheetTabBuilder (Shared)

## Fault
The last job in folder **Shared** (`SheetTabBuilder`, job `2fbf6ba4-b347-462f-a83e-33c6c34bbea6`, Unattended on `MOCK-HOST`) ended **Faulted** ~4s after start. It ran a single GSuite **Add Sheet** (`UiPath.GSuite.Activities.AddSheetConnections`) activity.

## Cause
The target spreadsheet **already contains a sheet (tab) whose name matches the configured `SheetName`**, and the activity's `ConflictResolution` was left at its default `Fail`, so it refused to create a duplicate and threw:

```
UiPath.GSuite.Exceptions.GSuiteException: A sheet with the same name already exists.
   at UiPath.GSuite.Sheets.Extensions.ISheetsServiceExtensions.AddSheetWithConflictResolution(...)
   at UiPath.GSuite.Activities.AddSheetConnections.SafeExecuteAsync(...)
```

This is a deterministic conflict-resolution failure (`ConflictResolution = Fail` + a pre-existing same-named sheet), raised synchronously by the activity. The connection authenticated and the spreadsheet resolved fine; it is not a connection/auth, 404/resource-not-found, invalid-range, or transient problem. (The Google Drive and Sheets connections serving folder Shared are Enabled and valid — a connection list confirms this, so the connection is not the problem.)

## Resolution
Resolve the name conflict by any of:
- Set `SheetName` to a value that is unique within the target spreadsheet, or
- Change `ConflictResolution` to `Replace` (overwrite the existing tab) or `Rename` (auto-suffix the new tab), or
- Remove/rename the pre-existing same-named tab in the spreadsheet, then re-run.

Must NOT attribute to: an HTTP 404 / resource-not-found, an invalid/inaccessible connection or auth failure, a null/empty or unparseable range, rate limiting / 429, a transient 5xx, or a timeout — the activity threw a same-name conflict because `ConflictResolution = Fail` met an existing sheet of that name.
