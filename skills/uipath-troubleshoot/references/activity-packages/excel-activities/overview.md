# Excel Activities

Activities from the `UiPath.Excel.Activities` package for automating Microsoft Excel workbooks on Windows. The package supports two runtime providers and two container shapes; failure surfaces differ across them. Modern Excel-scope activities run inside an `Excel Process Scope` / `Use Excel File` and either drive a real Excel.exe instance via COM interop or read/write through OpenXML; legacy workbook activities and `Excel Application Scope` use COM (Excel installed) or OpenXML file access. `Invoke VBA` (`UiPath.Excel.Activities.Business.InvokeVBAX`) is COM-only — it requires Excel.exe and a workbook handle.

> **Scope** — this package is the desktop Excel surface (`UiPath.Excel.Activities`). Cloud Excel via Microsoft Graph lives in `UiPath.MicrosoftOffice365.Activities` and is documented under [`o365-activities/`](../o365-activities/overview.md).

## How Execution Works

A Read Range / Write Range / Append Range / Delete Range / sheet-op activity executes inside one of two scopes:

1. **Excel Application Scope** (legacy) — opens the workbook through Microsoft Excel via COM interop. Requires Excel installed on the host. Holds the workbook open for the duration of the scope. Activities inside the scope inherit the open workbook reference.
2. **Use Excel File** (modern, same NuGet package) — opens the workbook with the OpenXML provider by default; falls back to Excel COM when the file requires Excel features the OpenXML provider does not support (or when `Read Formatting` / similar properties force COM). Does not require Excel installed when only OpenXML features are used.

Failures originate at one of four layers: file resolution (path / share / permissions), file acquisition (lock / corruption), provider parsing (sheet / range / cell address), or post-processing inside the activity (cell-type conversion, formula evaluation).

## How Invoke VBA Executes

`Invoke VBA` reads a macro from an **external code file** (`.txt`, `.vba`, `.bas`) at the configured `CodeFilePath`, injects it into the workbook's `VBProject` at runtime, calls the function named in `EntryMethodName`, then removes the injected module. Behaviour chain:

1. Resolve the active workbook handle from the surrounding `Excel Process Scope`
2. Read the macro source text from `CodeFilePath`
3. Add a new VBA module to the workbook via `Workbook.VBProject.VBComponents.Add` (this step requires Excel's "Trust access to the VBA project object model" setting to be enabled)
4. Run `Application.Run("<EntryMethodName>", <EntryMethodParameters>)`
5. Remove the injected module

Failures can originate at any layer — Excel security policy (step 3), code file content (step 2), entry method resolution (step 4), parameter marshaling (step 4), or COM interop with Excel itself (steps 1, 3, 4). Knowing which layer produced the error narrows the investigation.

## Key Activities

### Range read / write / delete

- **Read Range** (`ReadRange`, modern `ExcelReadRange`) — read a rectangular range from a worksheet into a `DataTable`. Accepts a sheet name plus an A1-notation range (empty range = used range).
- **Read Cell** / **Read Cell Formula** — read a single cell value or its formula text.
- **Read Column** / **Read Row** — read a single column or row into an array.
- **Write Range** / **Write Cell** / **Append Range** — write a `DataTable`, value, or appended rows back to a worksheet. Subject to the same file-acquisition and sheet-resolution failures as the read family.
- **Delete Range** (`DeleteRange`, modern `DeleteRangeX`) — remove a range and shift surrounding cells. Sensitive to `ShiftCells` / `ShiftOption` interaction with merged cells and Excel Tables.

### Sheet / workbook / filtering

- **Get Workbook Sheets** — enumerate sheet names in a workbook.
- **Insert Sheet** / **Delete Sheet** / **Rename Sheet** / **Copy Sheet** — sheet-level operations.
- **Filter Range** / **Pivot Range** / **Sort Range** — operations on a configured range; share the sheet- and range-resolution failure surface with the read family.

### Macros and lookup

- **Invoke VBA** (`InvokeVBAX`, display name "Invoke VBA") — execute a VBA macro stored in an external code file against the workbook currently open in the parent `Excel Process Scope`. Properties: `CodeFilePath` (path to `.txt`/`.vba`/`.bas` containing the macro source), `EntryMethodName` (name of the `Sub` or `Function` to invoke), `EntryMethodParameters` (`IEnumerable<Object>` of arguments), `Output` (return value when `EntryMethodName` points to a `Function`).
- **Execute Macro** (`ExecuteMacro`, modern "Run Spreadsheet Macro") — run a macro already present in the workbook by name. COM-only.
- **Lookup Range** — find the cell address of a value within a worksheet range. Two surfaces: classic `UiPath.Excel.Activities.ExcelLookUpRange` (inside an `Excel Application Scope`, **Excel Interop / COM only**) and modern `UiPath.Excel.Activities.LookUpRangeX` (inside a `Use Excel File` / `Excel Process Scope`). Properties: `Range` (A1 range to search; leave **blank** — not `""` — to search the whole used range), `Value`, `SheetName`, `Output` (the matched cell address). Searches only *visible* cells, so active AutoFilters change the result.

## Common Failure Patterns

### Read / Write / Delete Range

- **File-locked** — `System.IO.IOException: The process cannot access the file '<path>' because it is being used by another process.` Workbook held open by another process (user-opened Excel UI, orphan `EXCEL.EXE` from a prior job, lock from a different host on a network share). Affects every activity that opens the workbook (Read Range, Write Range, Delete Range, Excel Application Scope, Use Excel File).
- **Sheet not found** — `BusinessRuleException: The sheet with the name '<name>' does not exist` (wording varies slightly by package version). Configured `SheetName` does not match any sheet in the workbook — typo, case-sensitivity on the OpenXML provider, sheet renamed or deleted upstream, leading/trailing whitespace. Affects every range-addressed activity.
- **File not found** — `System.IO.FileNotFoundException: Could not find file '<path>'` or `System.IO.DirectoryNotFoundException`. Workbook path does not resolve — file moved or deleted, UNC share unreachable, relative path resolved against the wrong working directory, drive letter not mapped under the Robot's session.
- **Null reference / target-invocation** — `System.NullReferenceException` or `System.Reflection.TargetInvocationException` surfacing from inside the activity. Workbook contains content the active provider cannot parse — sensitivity labels (Microsoft Purview / Azure Information Protection), unsupported macros or embedded objects under the OpenXML provider, broken named ranges, formula references to deleted sheets, or (on Write Range) an uninitialized `DataTable`. Often masked by a generic wrapper exception with no specific cell pointer.

### Invoke VBA

- **Trust access to VBA project denied** — `Invoke VBA` faults the first time it tries to inject a module because Excel's "Trust access to the VBA project object model" setting is disabled. Surfaces as `Programmatic access to Visual Basic Project is not trusted` or a wrapped variant. A security-policy block, not a code defect.
- **Macro source file unreadable or malformed** — faults reading or compiling the macro source. Surfaces as `Cannot run the macro`, `Compile error`, `Syntax error`, or `Sub or Function not defined`. Causes: code not wrapped in a `Sub`/`Function` block, non-UTF-8 encoding with hidden BOM/control characters (common when the file was generated inside Studio), missing or wrong `CodeFilePath`, code authored in an `.xlsm` rather than an external text file.
- **Entry method name mismatch** — `Cannot run the macro '<name>'. The macro may not be available in this workbook` or `Sub or Function not defined` because `EntryMethodName` does not match a `Sub`/`Function` declared in the code file. Causes: typo, case mismatch, parentheses appended to the name (`MyMacro()` instead of `MyMacro`), or the macro nested inside another `Sub`.
- **Parameter type or shape mismatch** — faults marshaling `EntryMethodParameters` into the COM call. Surfaces as `Type mismatch`, `Wrong number of arguments or invalid property assignment`, or a Studio freeze during property edit. Causes: not an `IEnumerable<Object>` (e.g., a raw `String` typed into the property panel), wrong arity, or values typed inline instead of built via an `Assign`.
- **COM interop with Excel failed** — faults with an HRESULT from the COM layer, most commonly `0x80010100 RPC_E_SYS_CALL_FAILED` ("The system call failed"). Causes: Excel busy with a blocking modal dialog (license prompt, recover-unsaved-files banner, macro-warning bar), Excel.exe hung, multiple Office versions installed, or a 32-bit/64-bit Office mismatch with the robot process.

### Execute Macro

- **Macro fault / hang** — `COMException` with `0x80020009 DISP_E_EXCEPTION`, `0x800AC472`, or `0x80010108 RPC_E_DISCONNECTED`; or a job hang with no exception when the macro surfaces a modal dialog. Causes: macro name absent from the workbook, a VBA error inside the macro, the macro tearing down Excel (`Workbooks.Close` / `Application.Quit`), Trust Center policy disabling macros on the Robot host, an STA apartment violation, or a missing add-in / ActiveX dependency.

### Lookup Range

- **Excel not installed / Interop init failure** — classic `Lookup Range` launches Excel.exe via the Interop API and faults at startup on a host with no Excel. Surfaces as `Excel is not installed`, `REGDB_E_CLASSNOTREG` (`80040154`), or `Could not load ... Microsoft.Office.Interop.Excel`. Migration target on Excel-less hosts: Workbook `Read Range` (OpenXML) + `Lookup Data Table`.
- **Silent miss from active filters** — searches only visible cells, so active AutoFilters/column filters that hide the target row make it return null/empty with no error. A downstream null fault is the first visible symptom.
- **Workbook locked / file in use** — opening the workbook faults with `being used by another process` / `locked for editing`. Causes: file open interactively, an orphaned `EXCEL.EXE` holding the handle, a concurrent job, or a sync/AV client. Distinct from the COM `0x80010100` dispatcher failure above.
- **Object reference not set (sheet/range missing or no scope)** — `NullReferenceException` when the `SheetName` does not exist (typo/rename/case), a named range/table is undefined, or the activity runs outside an `Excel Application Scope` / `Use Excel File` so there is no workbook context.
- **Invalid range syntax or value misconfiguration** — `Range` set to an empty-string `""` instead of left blank (whole-sheet search is *blank*, not `""`), a malformed A1 reference, unescaped wildcards (`*`/`?`/`~`) in the search `Value`, or a type mismatch (text-vs-number, stray whitespace) that makes a present value fail to match.
- **Silent miss against a formula cell** — the search target is the *computed* result of an Excel formula and the Interop read can fail or read an unrefreshed value. Returns null/wrong even though the displayed cell text matches. Common with volatile formulas, cross-sheet / external references, and add-in-dependent calculations. Fix: freeze the cell to a static value (`Copy > Paste Special > Values`) or move off Interop to the Workbook `Read Range` + `Lookup Data Table` path, which reads cached values rather than re-evaluating.

## Package

NuGet: `UiPath.Excel.Activities`

Version-specific bugs are documented in the relevant playbooks.
