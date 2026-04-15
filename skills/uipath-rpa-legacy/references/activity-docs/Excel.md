# UiPath Excel Activities - Legacy Reference

## Overview
Excel automation with three access modes: Portable (file-based, no Excel required), Interop (COM, requires Excel), and Modern StudioX. Package: `UiPath.Excel.Activities`.

---

## Fundamental Split: Portable vs Interop vs Modern

| Aspect | Portable (WorkbookFile) | Interop (ExcelApplicationScope) | Modern (ExcelProcessScopeX) |
|--------|------------------------|---------------------------------|-----------------------------|
| Excel Required | NO | YES | YES |
| Library | ClosedXML / NPOI | COM Interop | COM + IExcelProcess |
| File Lock | None | Full (locked) | Full |
| Macros | NO | YES | YES |
| Formatting | Limited | Full | Full |
| Performance | Fast (no UI) | Slower (COM overhead) | Configurable |
| Scope Needed | None (standalone) | ExcelApplicationScope | ExcelProcessScopeX + ExcelApplicationCard |

**CRITICAL: Cannot mix patterns in same workflow**

**CRITICAL: Scope activities require `ActivityAction<T>` body** — you cannot place child activities directly inside `ExcelApplicationScope`, `ExcelProcessScopeX`, or `ExcelApplicationCard`. Each requires a `.Body` property containing `ActivityAction` with a `DelegateInArgument`. See [common-pitfalls.md](../common-pitfalls.md#scope-activities-require-activityaction-body-critical-for-xaml-generation) for the complete XAML template and all scope body patterns.

---

## Key Activities

### Portable (No Excel)
ReadRange, ReadCell, ReadCellFormula, ReadRow, ReadColumn, WriteRange, WriteCell, AppendRange, CreateTable, CreatePivotTable, GetTableRange, GetSheets, SetRangeColor, GetCellColor, CreateNewWorkbook

### CSV (Portable)
ReadCsvFile, WriteCsvFile, AppendCsvFile - DelimitatorOptions: Comma, Semicolon, Pipe, Caret, Tab

### Interop (ExcelApplicationScope children)
ExcelReadRange, ExcelWriteCell, ExcelWriteRange, ExcelAppendRange, ExcelSelectRange, ExcelAutoFillRange, ExcelCopyPasteRange, ExcelCreateTable, ExcelFilterTable, ExcelSortTable, ExcelDeleteRange, ExcelInsertColumn, ExcelDeleteColumn, ExcelRemoveDuplicatesRange, ExcelLookUpRange, ExcelCopySheet, ExecuteMacro, InvokeVBA

### Modern StudioX (ExcelApplicationCard children)
ReadRangeX, WriteCellX, WriteRangeX, AppendRangeX, SelectRangeX, ClearRangeX, CreateTableX, SortX, FilterX, DeleteRowsX, InsertRowsX, VLookupX, SaveExcelFileX, SaveAsPdfX, FormatRangeX, ExecuteMacroX, InvokeVBAX

---

## Critical Gotchas

### COM Object Cleanup
1. **Zombie Excel processes** - All COM objects must be explicitly released via `Marshal.ReleaseComObject()` or `DisposeWithReleaseComObject()` extension
2. **If body activity crashes, Excel process may remain open**
3. **InstanceCachePeriod (default 3000ms)** - Time Excel instance stays cached between activities

### Range Handling
4. **Single cell "A1" in ReadRangeX extends to entire sheet** - `extendSingleCellRanges: true` by default reads ALL data from A1 onward
5. **Multi-area ranges NOT supported** - `"A1:B10,D1:E10"` throws InvalidRange
6. **Full row**: `"1:5"`, Full column: `"A:C"`

### Sheet Names
7. **Sheet name is REQUIRED** and default is "Sheet1"
8. **Invalid chars**: `[ ] * ? : / \` - throws validation error
9. **Max 31 characters** per Excel spec
10. **Case sensitivity varies** - File-based: insensitive, Interop: can be sensitive

### Data Type Coercion (ExcelValue)
11. **Empty cell returns null** (not empty string)
12. **Dates stored as doubles** (serial numbers since 1900) - region-dependent
13. **DateTime conversion depends on system locale**
14. **OriginalValue vs OriginalDisplayValue** - raw (15) vs formatted ($15.00)

### Password Protection
15. **Two password types**: Password (read protection) vs EditPassword (write-reserved)
16. **Cannot set both Password and SecurePassword** simultaneously

### Workbook Scope
17. **AutoSave=true (default)** can corrupt file if not closed properly
18. **.xls files cannot use ClosedXML** - handled by NPOI in Portable mode or COM Interop. Legacy `WithWorkbook`/`OpenWorkbook` force Interop for .xls; modern Portable path uses NPOI instead.
19. **ReadOnly mode** - AutoSave disabled automatically

### CSV Quirks
20. **DelimitatorOptions** (note spelling "Delimitator" not "Delimiter")
21. **IgnoreQuotes option** - when true, parser doesn't treat quotes as field delimiters
22. **Default encoding is system encoding** - specify "UTF-8" explicitly for portability

### Macro/VBA
23. **MacroSetting must be EnableAll** or macros won't run
24. **InvokeVBA .bas file must be VB6 compatible** - injected into workbook VBProject at runtime
25. **Macro parameters are object[]** - order matters, complex types may not serialize

### File Conflicts
26. **FileConflictResolution**: Overwrite (close without saving), UseExisting, SaveAndReplace, Throw
27. **Default behavior depends on ExistingProcessAction** - can silently drop changes

### Deprecated Activities
- OpenWorkbook, CloseWorkbook, WithWorkbook (legacy)
- ExcelForEachRow v1 (use ExcelForEachRowX)
- CreatePivotTableX v1 (use v2)

### Additional Validated Gotchas
27. **Single cell "A1" extends ONLY when no colon** - "A1" expands to full used range, but "A1:A1" does NOT expand (treated as explicit range)
28. **ForEachRowX disables AutoSave during iteration** then re-enables; crash mid-iteration may leave AutoSave disabled
29. **.xlsb (binary workbook) not supported in Portable mode** - always requires Interop
30. **ClosedXML formula evaluation is limited** - unsupported formulas fall back to cached/stale values via GetRichText()
31. **Range address string max 255 characters** - limits multi-area ranges via COM
32. **Protected/locked sheets throw ExcelException** - check `ProtectContents && cellRange.Locked`
33. **Cell "A0" treated as "A:A" by ClosedXML** - known bug workaround in codebase
