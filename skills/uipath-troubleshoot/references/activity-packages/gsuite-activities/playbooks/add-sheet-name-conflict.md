---
confidence: high
---

# GSuite Add Sheet — A sheet with the same name already exists

## Context

What this looks like:
- Activity `Add Sheet` (`UiPath.GSuite.Activities.AddSheetConnections`) throws `GSuiteException`
- Error message: `A sheet with the same name already exists.`
- Job faults synchronously the moment the activity runs

What can cause it:
- The target spreadsheet already contains a sheet (tab) whose title equals the configured `SheetName` (case-insensitive comparison), and `ConflictResolution` is set to `Fail`. This is the only cause — Google Sheets does not permit two sheets with the same name within one spreadsheet, and the `Fail` branch refuses to proceed when a duplicate is detected.

Notes:
- `AddSheetConnections` is the only GSuite activity that produces this exception. Other Sheets activities (`AddSheetConnections` aside) do not exercise this code path.
- The default value of `ConflictResolution` on `AddSheetConnections` is `Fail`, so this is the out-of-the-box behavior when the property is left unset.

## Resolution

A spreadsheet cannot contain two sheets with the same name. The error is unambiguous; no further investigation is needed. Stop the investigation and ask the user to do one of the following:

1. **Change the `SheetName`** on the activity so it is unique within the target spreadsheet (remember: matching is case-insensitive — `"Data"` and `"data"` collide).
2. **Ensure the target spreadsheet contains no sheet with that name** (rename or delete the existing sheet first).
3. **Change `ConflictResolution`** on the activity to a value that handles the duplicate:
   - `Replace` — delete the existing sheet with that name and add a new sheet at the same position
   - `Rename` — automatically rename the new sheet to a unique name (appends `1`, `2`, … until no collision remains)
