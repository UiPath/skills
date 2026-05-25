# Excel Activities

Activities from the `UiPath.Excel.Activities` package for automating Microsoft Excel workbooks on the host filesystem. The package supports two runtime providers and two container shapes; failure surfaces differ across them.

> **Scope** — this package is the desktop Excel surface (`UiPath.Excel.Activities`). Cloud Excel via Microsoft Graph lives in `UiPath.MicrosoftOffice365.Activities` and is documented under [`o365-activities/`](../o365-activities/overview.md).

## How Execution Works

A Read Range / Write Range / Append Range / sheet-op activity executes inside one of two scopes:

1. **Excel Application Scope** (legacy) — opens the workbook through Microsoft Excel via COM interop. Requires Excel installed on the host. Holds the workbook open for the duration of the scope. Activities inside the scope inherit the open workbook reference.
2. **Use Excel File** (modern, same NuGet package) — opens the workbook with the OpenXML provider by default; falls back to Excel COM when the file requires Excel features the OpenXML provider does not support (or when `Read Formatting` / similar properties force COM). Does not require Excel installed when only OpenXML features are used.

Failures originate at one of four layers: file resolution (path / share / permissions), file acquisition (lock / corruption), provider parsing (sheet / range / cell address), or post-processing inside the activity (cell-type conversion, formula evaluation).

## Key Activity Types

### Range read

- **Read Range** (`ReadRange`, modern `ExcelReadRange`) — read a rectangular range from a worksheet into a `DataTable`. Accepts a sheet name plus an A1-notation range (empty range = used range).
- **Read Cell** / **Read Cell Formula** — read a single cell value or its formula text.
- **Read Column** / **Read Row** — read a single column or row into an array.

### Range write

- **Write Range** / **Write Cell** / **Append Range** — write a `DataTable`, value, or appended rows back to a worksheet. Subject to the same file-acquisition and sheet-resolution failures as the read family.

### Sheet / workbook

- **Get Workbook Sheets** — enumerate sheet names in a workbook.
- **Insert Sheet** / **Delete Sheet** / **Rename Sheet** / **Copy Sheet** — sheet-level operations.

### Filtering / pivot

- **Filter Range** / **Pivot Range** / **Sort Range** — operations on a configured range; share the sheet- and range-resolution failure surface with the read family.

## Common Failure Patterns

### Read Range — file-locked

`System.IO.IOException: The process cannot access the file '<path>' because it is being used by another process.` Workbook is held open by another process (user-opened Excel UI, orphan `EXCEL.EXE` from a prior job, lock from a different host on a network share). Affects every activity that opens the workbook (Read Range, Write Range, Excel Application Scope, Use Excel File).

### Read Range — sheet not found

`BusinessRuleException: The sheet with the name '<name>' does not exist` (wording varies slightly by package version). Configured `SheetName` does not match any sheet in the workbook — typo, case-sensitivity on the OpenXML provider, sheet renamed or deleted upstream, leading/trailing whitespace. Affects every range-addressed activity.

### Read Range — file not found

`System.IO.FileNotFoundException: Could not find file '<path>'` or `System.IO.DirectoryNotFoundException`. Workbook path does not resolve — file moved or deleted, UNC share unreachable, relative path resolved against the wrong working directory, drive letter not mapped under the Robot's session.

### Read Range — null reference / target-invocation

`System.NullReferenceException` or `System.Reflection.TargetInvocationException` surfacing from inside the activity. Workbook contains content the active provider cannot parse — sensitivity labels (Microsoft Purview / Azure Information Protection), unsupported macros or embedded objects under the OpenXML provider, broken named ranges, or formula references to deleted sheets. Often masked by a generic wrapper exception with no specific cell pointer.

## Package

NuGet: `UiPath.Excel.Activities`
