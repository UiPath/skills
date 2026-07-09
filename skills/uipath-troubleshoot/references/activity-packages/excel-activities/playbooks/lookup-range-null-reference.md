---
confidence: medium
---

# Lookup Range — Object Reference Not Set (Sheet or Range Missing / No Scope)

## Context

What this looks like:
- Activity `Lookup Range` (`UiPath.Excel.Activities.ExcelLookUpRange` / `LookUpRangeX`) faults with `Object reference not set to an instance of an object` (`System.NullReferenceException`)
- The fault is synchronous, the moment the activity tries to resolve its target sheet or range
- No file-in-use message (that routes to [lookup-range-file-locked.md](./lookup-range-file-locked.md)) and no `Excel is not installed` message (that routes to [lookup-range-excel-not-installed.md](./lookup-range-excel-not-installed.md))

What can cause it (any of):
- **Target sheet does not exist** — the `SheetName` configured on the activity (or implied by the range) names a sheet that is absent from the workbook: a typo, a rename, a case/whitespace difference, or the wrong workbook is open. The activity dereferences a null worksheet handle.
- **Target range does not resolve** — the named range or table the activity points at is not defined in the workbook, so the range object is null.
- **No surrounding scope / workbook not opened** — the classic `Lookup Range` was dropped outside an `Excel Application Scope`, or the modern `LookUpRangeX` outside a `Use Excel File` / `Excel Process Scope`, so there is no workbook context object and the activity dereferences null. (Also occurs when the scope failed to open earlier but execution continued.)

Notes:
- `NullReferenceException` is a generic .NET fault; the *Excel-specific* root cause is almost always one of the three above for this activity. The generic runtime-exception playbook in `runtime-exceptions/playbooks/null-reference-exception.md` covers null faults in user workflow code — this playbook is for the null fault originating *inside* the `Lookup Range` activity's sheet/range/scope resolution.
- A sheet-name mismatch here is the direct analogue of the GSuite "sheet does not exist" and the asset-name-mismatch patterns: exact-match lookup, no fuzzy fallback.

## Investigation

1. Read the `Lookup Range` node from the workflow `.xaml`: capture the configured `SheetName`, the range/table reference, and whether the activity sits inside an `Excel Application Scope` / `Use Excel File` container.
2. Confirm the surrounding scope exists and opened successfully (check the job log for a successful "workbook opened" line before the fault; if the scope itself faulted, fix that first).
3. Open the target workbook (or ask the user to) and list the actual sheet/tab names. Compare against the activity's `SheetName` character-for-character — watch for trailing spaces, case differences, and similar-looking names.
4. If the activity references a named range or table, confirm that name is actually defined in the workbook (`Formulas > Name Manager`).

## Resolution

- **If the sheet name does not match** — fix the `SheetName` on the activity to match the workbook's tab name exactly (case and spacing included), or rename/add the sheet in the workbook so the configured name resolves. Save, rebuild, republish.
- **If the named range/table is undefined** — define it in the workbook (`Name Manager` / format-as-table), or change the activity to address an explicit A1 range instead of the missing name.
- **If the activity is not inside a scope** — wrap it: classic `Lookup Range` inside an `Excel Application Scope`, modern `LookUpRangeX` inside a `Use Excel File` / `Excel Process Scope` bound to the workbook. Without the scope there is no workbook context and the activity always null-faults.
- **If the scope opened the wrong workbook** — correct the `WorkbookPath` so the sheet the activity expects is actually present in the opened file.

After the fix, confirm the lookup resolves a real cell address rather than returning null — a silent null result with active filters present is a *different* scenario (see [lookup-range-active-filters.md](./lookup-range-active-filters.md)).
