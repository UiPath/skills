# Excel Activities

Activities from the `UiPath.Excel.Activities` package for automating Microsoft Excel on Windows. Two execution surfaces coexist: modern Excel-scope activities that operate inside an `Excel Process Scope` and drive a real Excel.exe instance via COM interop, and legacy workbook activities that read/write `.xlsx` files directly through OpenXML without Excel installed. `Invoke VBA` (`UiPath.Excel.Activities.Business.InvokeVBAX`) is COM-only — it requires Excel.exe and a workbook handle.

## How Invoke VBA Executes

`Invoke VBA` reads a macro from an **external code file** (`.txt`, `.vba`, `.bas`) at the configured `CodeFilePath`, injects it into the workbook's `VBProject` at runtime, calls the function named in `EntryMethodName`, then removes the injected module. Behaviour chain:

1. Resolve the active workbook handle from the surrounding `Excel Process Scope`
2. Read the macro source text from `CodeFilePath`
3. Add a new VBA module to the workbook via `Workbook.VBProject.VBComponents.Add` (this step requires Excel's "Trust access to the VBA project object model" setting to be enabled)
4. Run `Application.Run("<EntryMethodName>", <EntryMethodParameters>)`
5. Remove the injected module

Failures can originate at any layer — Excel security policy (step 3), code file content (step 2), entry method resolution (step 4), parameter marshaling (step 4), or COM interop with Excel itself (steps 1, 3, 4). Knowing which layer produced the error narrows the investigation.

## Key Activities

- **Invoke VBA** (`InvokeVBAX`, display name "Invoke VBA") — execute a VBA macro stored in an external code file against the workbook currently open in the parent `Excel Process Scope`. Properties: `CodeFilePath` (path to `.txt`/`.vba`/`.bas` containing the macro source), `EntryMethodName` (name of the `Sub` or `Function` to invoke), `EntryMethodParameters` (`IEnumerable<Object>` of arguments), `Output` (return value when `EntryMethodName` points to a `Function`).
- **Lookup Range** — find the cell address of a value within a worksheet range. Two surfaces: classic `UiPath.Excel.Activities.LookUpRange` (inside an `Excel Application Scope`, **Excel Interop / COM only**) and modern `UiPath.Excel.Activities.LookUpRangeX` (inside a `Use Excel File` / `Excel Process Scope`). Properties: `Range` (A1 range to search; leave **blank** — not `""` — to search the whole used range), `Value` (the value to find), `SheetName` (target sheet), `Output` (the matched cell address). Searches only *visible* cells, so active AutoFilters change the result.

## Common Failure Patterns

- **Trust access to VBA project denied** — `Invoke VBA` faults the first time it tries to inject a module because Excel's "Trust access to the VBA project object model" setting is disabled. Surfaces as `Programmatic access to Visual Basic Project is not trusted` or a wrapped variant. The error is a security-policy block, not a code defect.
- **Macro source file unreadable or malformed** — `Invoke VBA` faults reading or compiling the macro source. Surfaces as `Cannot run the macro`, `Compile error`, `Syntax error`, or `Sub or Function not defined`. Causes: code not wrapped in a `Sub`/`Function` block, non-UTF-8 encoding with hidden BOM/control characters (common when the file was generated inside Studio), missing or wrong `CodeFilePath`, code authored in an `.xlsm` rather than an external text file.
- **Entry method name mismatch** — `Invoke VBA` faults with `Cannot run the macro '<name>'. The macro may not be available in this workbook` or `Sub or Function not defined` because `EntryMethodName` does not match a `Sub`/`Function` declared in the code file. Causes: typo, case mismatch (VBA identifiers are case-insensitive in source but UiPath passes the string through to `Application.Run`, which has been observed to reject case-mismatched names in some Excel versions), parentheses appended to the name (`MyMacro()` instead of `MyMacro`), or the macro is nested inside another `Sub`.
- **Parameter type or shape mismatch** — `Invoke VBA` faults marshaling `EntryMethodParameters` into the COM call. Surfaces as `Type mismatch`, `Wrong number of arguments or invalid property assignment`, or a Studio freeze during property edit. Causes: `EntryMethodParameters` not an `IEnumerable<Object>` (e.g., a raw `String` or `Object` typed directly into the property panel), wrong arity (count mismatches the macro signature), or values typed inline in the property window instead of built via an `Assign` activity.
- **COM interop with Excel failed** — `Invoke VBA` (or the surrounding Excel activity) faults with an HRESULT from the COM layer. The most common is `0x80010100 RPC_E_SYS_CALL_FAILED` ("The system call failed"). Causes: Excel busy with a blocking modal dialog (license prompt, recover-unsaved-files banner, macro-warning bar), Excel.exe hung, multiple Office versions installed, or a 32-bit/64-bit Office mismatch with the robot process.

### Lookup Range

- **Excel not installed / Interop init failure** — classic `Lookup Range` launches Excel.exe via the Interop API and faults at startup on a host with no Excel. Surfaces as `Excel is not installed`, `REGDB_E_CLASSNOTREG` (`80040154`), or `Could not load ... Microsoft.Office.Interop.Excel`. Migration target on Excel-less hosts: Workbook `Read Range` (OpenXML) + `Lookup Data Table`.
- **Silent miss from active filters** — `Lookup Range` searches only visible cells, so active AutoFilters/column filters that hide the target row make it return null/empty with no error. A downstream null fault is the first visible symptom.
- **Workbook locked / file in use** — opening the workbook faults with `The process cannot access the file because it is being used by another process` / `locked for editing`. Causes: file open interactively, an orphaned `EXCEL.EXE` holding the handle, a concurrent job, or a sync/AV client. Distinct from the COM `0x80010100` dispatcher failure above.
- **Object reference not set (sheet/range missing or no scope)** — `NullReferenceException` when the `SheetName` does not exist (typo/rename/case), a named range/table is undefined, or the activity runs outside an `Excel Application Scope` / `Use Excel File` so there is no workbook context.
- **Invalid range syntax or value misconfiguration** — `Range` set to an empty-string `""` instead of left blank (whole-sheet search is *blank*, not `""`), a malformed A1 reference, unescaped wildcards (`*`/`?`/`~`) in the search `Value`, or a type mismatch (text-vs-number, stray whitespace) that makes a present value fail to match.

## Package

NuGet: `UiPath.Excel.Activities`

Version-specific bugs are documented in the relevant playbooks.
