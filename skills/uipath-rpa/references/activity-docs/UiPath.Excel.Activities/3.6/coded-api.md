# Excel Activities — Coded Workflow API

`UiPath.Excel.Activities`

Perform Excel operations — read, write, format, chart, filter, sort, and manage workbooks — from coded C# workflows.

**Service accessor:** `excel` (type `IExcelService`)
**Required package:** `"UiPath.Excel.Activities": "*"` in project.json dependencies

## Auto-Imported Namespaces

These namespaces are automatically available in coded workflows when this package is installed:

```
System
System.Collections.Generic
System.Data
UiPath.Excel
UiPath.Excel.Activities
UiPath.Excel.Activities.API
UiPath.Excel.Activities.API.Models
```

> **Note:** Some types used in CSV, formatting, protection, and window-resize operations live outside these namespaces. Add `using UiPath.CSV;` for `DelimitatorOptions`, `using System.Drawing;` for `Color`, `using System.Security;` for `SecureString`, `using UiPath.Excel.Model;` for `ResizeWindowOptions`, and `using UiPath.Excel.Activities.Business;` for formatting types such as `ICellFormat`, `GeneralFormat`, and `ExcelFormatParameters` as needed.

## Service Overview

The `excel` service exposes two API surfaces:

1. **Portable API** (`IWorkHandle`) — Cross-platform workbook operations over Excel files (XLSX and legacy XLS). Use `excel.UseWorkBook(...)` to get an `IWorkHandle`, then call extension methods for read/write/cell operations. Works on all platforms.
2. **Windows/Interop API** (`IWorkbookQuickHandle`) — Full-featured Excel interop operations. Use `excel.UseExcelFile(...)` to get an `IWorkbookQuickHandle` with sheet/table/chart indexers, optionally targeting a specific Excel process created via `excel.ExcelProcessScope(...)` and passed through `UseOptions.ExcelProcess`. Windows only.

---

## Portable Workbook Operations

These methods work cross-platform over Excel workbook formats (XLSX via Open XML, with support for legacy XLS).

### `IWorkHandle UseWorkBook(WorkbookOptions options)`

Opens or creates a workbook using the specified options. When `CreateNew` is true and the file does not exist, a new workbook is created. When `CreateNew` is true and the file already exists, the `ConflictBehavior` setting controls whether to replace, fail, or skip. When `ConflictBehavior` is null (default) or `CreateNew` is false, the existing file is opened.

**Parameters:**
- `options` (`WorkbookOptions`) — Options for the workbook

**Returns:** `IWorkHandle` — Disposable handle to the workbook. Use with `using` statement.

### `IWorkHandle UseWorkBook(string path, bool createNew = true)`

Opens a workbook at the specified path.

**Parameters:**
- `path` (`string`) — Path of the workbook
- `createNew` (`bool`) — If the workbook does not exist, determines if a new workbook is created. Default: `true`

**Returns:** `IWorkHandle` — Disposable handle to the workbook. Use with `using` statement.

---

## Windows/Interop Workbook Operations

These methods require Excel interop (Windows only) and provide full Excel feature support.

### `IWorkbookQuickHandle UseExcelFile(UseOptions options)`

Opens an Excel file using interop with detailed configuration options.

**Parameters:**
- `options` (`UseOptions`) — Options used when opening or creating the file

**Returns:** `IWorkbookQuickHandle` — Disposable handle for the Excel file with sheet/table/chart indexers.

### `IWorkbookQuickHandle UseExcelFile(string path)`

Opens an Excel file using interop with default options: creates the file if it does not exist and saves changes when the handle is disposed.

**Parameters:**
- `path` (`string`) — The path of the Excel file

**Returns:** `IWorkbookQuickHandle` — Disposable handle for the Excel file.

### `IWorkbookQuickHandle UseExcelFile(string path, bool saveChanges, bool createIfNotExist)`

Opens an Excel file using interop with save and create options.

**Parameters:**
- `path` (`string`) — The path of the Excel file
- `saveChanges` (`bool`) — True to save changes after workbook operations
- `createIfNotExist` (`bool`) — True to create the file if it does not exist

**Returns:** `IWorkbookQuickHandle` — Disposable handle for the Excel file.

### `IExcelProcess ExcelProcessScope(ScopeOptions options)`

Controls interaction with the Excel application process. The returned `IExcelProcess` should be disposed when no longer needed.

**Parameters:**
- `options` (`ScopeOptions`) — Options for interaction with Excel

**Returns:** `IExcelProcess` — Disposable process controller for how Excel files are handled.

### `IExcelProcess ExcelProcessScope()`

Creates an `IExcelProcess` using default options (retrieved from project settings).

**Returns:** `IExcelProcess` — Disposable process controller.

---

## Handle Types

### `IWorkHandle`

Handle to the workbook for portable (Open XML) coded operations.

> This type implements `IDisposable`. Always use inside a `using` statement or call `Dispose()` explicitly.

#### Extension Methods (Portable)

| Method | Return Type | Description |
|--------|------------|-------------|
| `ReadRange(string sheetName, string range, bool addHeaders, bool preserveFormat)` | `DataTable` | Reads a range as DataTable. If range is empty, reads whole sheet. If range is a single cell, reads from that cell onward. |
| `WriteRange(string sheetName, string startingCell, DataTable table, bool addHeaders)` | `void` | Writes DataTable data starting at the specified cell. Creates sheet if it doesn't exist. Changes saved immediately. |
| `AppendRange(string sheetName, DataTable table)` | `void` | Appends DataTable data after existing data in the sheet. Creates sheet if it doesn't exist. |
| `ReadCell(string sheetName, string cell, bool preserveFormat)` | `object` | Reads a single cell value. |
| `ReadCellFormula(string sheetName, string cell)` | `string` | Reads the formula from a cell. |
| `ReadColumn(string sheetName, string startingCell, bool preserveFormat)` | `IEnumerable<object>` | Reads values from a column starting at the specified cell. |
| `ReadRow(string sheetName, string startingCell, bool preserveFormat)` | `IEnumerable<object>` | Reads values from a row starting at the specified cell. |
| `WriteCell(string sheetName, string cell, string text)` | `void` | Writes a value into a cell. Creates sheet if it doesn't exist. |
| `GetTableRange(string sheetName, string tableName, bool isPivot)` | `string` | Extracts the range of an Excel table or pivot table from the specified sheet, depending on `isPivot`. |
| `GetCellColor(string sheetName, string cell)` | `Color` | Retrieves the fill color of a cell. |
| `SetRangeColor(string sheetName, string range, Color color)` | `void` | Sets the fill color for a range. |
| `GetSheets(bool onlyVisibleSheets = false)` | `IEnumerable<string>` | Returns the list of sheet names from the workbook. |
| `CreatePivotTable(string targetSheet, IPivotTableInfo pivotTableInfo)` | `void` | Creates a pivot table in the specified sheet. |
| `InsertChart(CreateChartConfig config)` | `string` | Inserts a chart into the workbook. Returns the chart name. |
| `UpdateChart(UpdateChartConfiguration config)` | `void` | Applies modifications to an existing chart. |

### `IWorkbookQuickHandle`

Handle for Windows/Interop Excel operations with rich indexer access.

> This type implements `IDisposable`. Always use inside a `using` statement or call `Dispose()` explicitly.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `SelectedRange` | `RangeValue` | The currently selected range in the Excel application. |
| `SelectedCell` | `ExcelValue` | The currently selected cell in the Excel application. |
| `SelectedSheet` | `WorksheetQuickHandle` | The worksheet currently selected in the Excel application. |
| `Sheet` | `IWorksheetIndexer` | Array of workbook sheets; use `Sheet["SheetName"]` to select a sheet (`ISheetRef`). |
| `Table` | `ITableIndexer` | Reference to a particular table; use `Table["TableName"]` to select a table (`ITableRef`). |
| `FilePath` | `string` | The workbook file path. |
| `AllPivotTables` | `IPivotTableRef` | Reference to refresh all pivot tables in the workbook. |

#### Extension Methods (Windows/Interop)

| Method | Return Type | Description |
|--------|------------|-------------|
| `ForEachSheet(Action<ISheetRef> act)` | `void` | Iterates over each visible sheet in the workbook. |
| `ForEachSheet(Func<ISheetRef, bool> func)` | `void` | Iterates over sheets; return `false` to break. |
| `InsertSheet(string sheetName)` | `ISheetRef` | Inserts a new sheet in the workbook. |
| `ExecuteMacro(string macroName, IList<object> macroArguments)` | `object` | Executes a macro within a macro-enabled workbook. |
| `InvokeVBA(string codeFilePath, string entryMethodname, IList<object> arguments)` | `object` | Invokes a VBA function from an external code file. |
| `RefreshDataConnections()` | `void` | Refreshes all data sources in the workbook. |
| `SaveExcelFile()` | `void` | Saves any pending changes. |
| `SaveExcelFileAs(string filePath, bool replaceExisting, ExcelSaveAsType saveAsType)` | `void` | Saves the workbook as a different file/format. |
| `SaveExcelFileAs(string filePath, ExcelSaveAsType saveAsType)` | `void` | Saves as a different file (replaces existing by default). |
| `SaveAsPdf(string filePath, bool replaceExisting, int? startPage, int? endPage, PdfSaveQuality saveQuality)` | `void` | Saves the workbook as PDF with page range and quality options. |
| `SaveAsPdf(string filePath, bool replaceExisting)` | `void` | Saves the workbook as PDF (all pages, standard quality). |
| `SaveAsPdf(string filePath)` | `void` | Saves as PDF (replaces existing, standard quality). |
| `AddSensitivityLabel(IExcelLabelObject label)` | `void` | Adds or updates a sensitivity label on the workbook. |
| `GetSensitivityLabel()` | `IExcelLabelObject` | Retrieves the sensitivity label from the workbook. |

### Range Reference Types

The Windows API uses typed references for ranges, cells, sheets, tables, and charts. These are obtained from `IWorkbookQuickHandle` indexers.

| Type | Description | Obtained From |
|------|-------------|---------------|
| `ISheetRef` | Reference to a worksheet. Extends `IReadWriteRangeRef`. Has `Name` property. | `handle.Sheet["SheetName"]` |
| `ITableRef` | Reference to an Excel table. Has `TableName` and `Columns` properties. | `handle.Table["TableName"]` (returns `RangeValue`, which implements `ITableRef`) |
| `IPivotTableRef` | Reference to a pivot table. Has `TableName` property. | Via `ISheetRef` or `AllPivotTables` |
| `IChartRef` | Reference to a chart. Has `ChartName`, `ParentSheet`, `ChartInfo` properties. | Via chart operations |
| `IReadRangeRef` | Readable range (may be dynamic). Has `Worksheet`, `Address`, `FirstCell`, `FullRangeName`, `RowCount` properties and `GetNumberOfColumns()`, `GetTableOrRangeColumns(bool)`, `ToRawDataTable()`, `ReadAsDataTable(bool, bool, bool, bool, ReadFormattingOptions?)` methods. | Via sheet/table refs |
| `IReadWriteRangeRef` | Readable and writable range. | Extends `IReadRangeRef` |
| `IWellDefinedReadRangeRef` | Range with fixed address and size. | Via specific range operations |
| `IWellDefinedReadWriteRangeRef` | Writable range with fixed address and size. Extends `IWellDefinedReadRangeRef` and `IReadWriteRangeRef`. | Via `FillRange` target; base of `ICurrentRowQuickHandle` |
| `IReadCellRef` | Readable cell reference. Has `Address`, `Worksheet`. | Via cell operations |
| `IReadWriteCellRef` | Readable and writable cell reference. | Extends `IReadCellRef` |
| `ICurrentRowQuickHandle` | Current row in a ForEachRow loop. Access cells by name `row["Column"]` or by index `row.ByIndex[0]`. | Via `ForEachRow` callback |

### Range Extension Methods (Windows/Interop)

These extension methods operate on the range reference types obtained from `IWorkbookQuickHandle`.

#### Read Operations

| Method | Extends | Return Type | Description |
|--------|---------|------------|-------------|
| `ReadRange(bool hasHeaders, ReadFormattingOptions? readFormattingOptions, bool visibleRowsOnly)` | `IReadRangeRef` | `DataTable` | Reads range as DataTable with formatting and visibility options. |
| `ReadRange(bool hasHeaders, bool visibleRowsOnly)` | `IReadRangeRef` | `DataTable` | Reads range as DataTable using the workbook formatting settings and specified visibility options. |
| `ReadCellValue(bool getFormattedText)` | `IReadCellRef` | `object` | Reads a cell value. When `getFormattedText` is true, returns the display value (e.g., `"$15.00"`); when false, returns the raw value (e.g., `15`). |
| `ReadCellValue()` | `IReadCellRef` | `object` | Reads the formatted cell value. |
| `FindFirstLastDataRow(string columnName, bool hasHeaders, bool visibleRowsOnly, int firstRowOffset, int lastRowOffset, int blankRowsToSkip, LastRowConfiguration configureLastRowAs)` | `IReadRangeRef` | `(int first, int last)` | Finds first and last rows with data. Returns -1 if no data found. |
| `FindFirstLastDataRow(string columnName, bool hasHeaders, bool visibleRowsOnly, LastRowConfiguration configureLastRowAs)` | `IReadRangeRef` | `(int first, int last)` | Finds first/last data rows with default offsets. |
| `FindFirstLastDataRow(string columnName)` | `IReadRangeRef` | `(int first, int last)` | Finds first/last data rows with all defaults. |
| `FindReplaceValue(object valueToFind, FindReplaceOptions operation, object replaceWith, LookInOptions lookIn, bool matchCase, bool matchEntireCellContents)` | `IReadRangeRef` | `string` | Finds or replaces a value. Returns cell address where found. |
| `LookupRange(object label, IReadRangeRef resultRange)` | `IReadRangeRef` | `object` | LOOKUP function: finds data in a range. |
| `LookupRange(object label)` | `IReadRangeRef` | `object` | LOOKUP with default result range. |
| `VLookup(object label, int? columnIndex, bool exactMatch)` | `IReadRangeRef` | `object` | VLOOKUP function. |
| `VLookup(object label)` | `IReadRangeRef` | `object` | VLOOKUP with exact match and default column. |
| `MatchFunction(object valueToMatch, MatchType matchFunctionType)` | `IWellDefinedReadRangeRef` | `int` | MATCH function: returns relative position of matched value. |
| `MatchFunction(object valueToMatch)` | `IWellDefinedReadRangeRef` | `int` | MATCH with default type (LargestValueLessOrEqual). |
| `GetCellColorInternal()` | `IReadCellRef` | `Color` | Extracts the background color of a cell. **Note:** The `Internal` suffix is part of the public API method name. |

#### Write Operations

| Method | Extends | Return Type | Description |
|--------|---------|------------|-------------|
| `WriteRange(DataTable source, bool append, bool excludeHeaders, bool ignoreEmptySource)` | `IReadWriteRangeRef` | `void` | Writes DataTable into Excel. |
| `WriteRange(DataTable source, bool append, bool excludeHeaders)` | `IReadWriteRangeRef` | `void` | Writes DataTable (throws on empty source). |
| `WriteCell(object value, int rowOffset)` | `IReadWriteCellRef` | `void` | Writes a value/formula into a cell with row offset. |
| `WriteCell(object value)` | `IReadWriteCellRef` | `void` | Writes a value/formula into a cell. |
| `AppendRange(IReadRangeRef source, string columnName, bool transpose, CopyPasteRangeOptions pasteOptions, bool destinationHasHeaders, bool excludeSourceHeaders)` | `IReadWriteRangeRef` | `void` | Appends data from source range to destination. |
| `AppendRange(IReadRangeRef source, bool transpose, CopyPasteRangeOptions pasteOptions, bool excludeSourceHeaders)` | `IReadWriteRangeRef` | `void` | Appends data with paste options. |
| `AppendRange(IReadRangeRef source)` | `IReadWriteRangeRef` | `void` | Appends data with all defaults. |
| `CopyPasteRange(IReadRangeRef sourceRange, bool excludeSourceHeaders, bool excludeDestinationHeaders, bool transpose, CopyPasteRangeOptions options)` | `IReadWriteRangeRef` | `void` | Copies and pastes a range to another location. |
| `FillRange(object value)` | `IWellDefinedReadWriteRangeRef` | `void` | Fills all cells in range with a formula or value. |
| `ClearRange(bool hasHeaders)` | `IReadWriteRangeRef` | `void` | Clears data from a range/sheet/table. |
| `ClearRange()` | `IReadWriteRangeRef` | `void` | Clears data (no headers). |

#### Row & Column Operations

| Method | Extends | Return Type | Description |
|--------|---------|------------|-------------|
| `InsertRows(int nbOfRows, InsertRowPosition insertPosition, int specificIndex, bool hasHeaders)` | `IReadWriteRangeRef` | `void` | Inserts rows at the specified location. |
| `InsertRows(int nbOfRows)` | `IReadWriteRangeRef` | `void` | Inserts rows at the end (default). |
| `DeleteColumn(string columnName, bool hasHeaders)` | `IReadWriteRangeRef` | `void` | Deletes a column from a range. |
| `DeleteColumn(DeleteRowsOption deleteOption, string rowPositions, bool hasHeaders)` | `IReadWriteRangeRef` | `void` | Deletes rows by option (specific, visible, hidden, duplicates). **Note:** Method is named `DeleteColumn` for legacy reasons but deletes rows — see the `DeleteRowsOption` parameter. |
| `InsertColumn(string columnName, ColumnRelativePosition position, bool hasHeaders, string newColumnHeader, ICellFormat columnFormat)` | `IReadWriteRangeRef` | `void` | Inserts a column at the specified location. |
| `InsertColumn(string columnName)` | `IReadWriteRangeRef` | `void` | Inserts a column before the target (defaults). |
| `RemoveDuplicates(bool hasHeaders, ColumnsCompare columnsMode, IEnumerable<string> columns)` | `IReadWriteRangeRef` | `void` | Removes duplicate rows. |
| `ForEachRow(EmptyRowBehavior emptyRowBehavior, bool forceFirstRowAsHeaders, bool saveAfterEachRow, Func<ICurrentRowQuickHandle, bool> func)` | `IReadRangeRef` | `void` | Iterates over each row; return `false` to break. |
| `ForEachRow(EmptyRowBehavior emptyRowBehavior, bool forceFirstRowAsHeaders, bool saveAfterEachRow, Action<ICurrentRowQuickHandle> act)` | `IReadRangeRef` | `void` | Iterates over each row. |
| `ForEachRow(Func<ICurrentRowQuickHandle, bool> func)` | `IReadRangeRef` | `void` | Iterates rows with defaults (stop on empty). |
| `ForEachRow(Action<ICurrentRowQuickHandle> act)` | `IReadRangeRef` | `void` | Iterates rows with defaults. |

#### Formatting & Appearance

| Method | Extends | Return Type | Description |
|--------|---------|------------|-------------|
| `Autofit(bool columns, bool rows)` | `IReadRangeRef` | `void` | Autofits columns and/or rows. |
| `Autofit()` | `IReadRangeRef` | `void` | Autofits both columns and rows. |
| `Autofill()` | `IWellDefinedReadRangeRef` | `void` | Autofills a range using its data source pattern. |
| `FormatRange(ICellFormat format, AlignmentOptions alignment, FontOptions font)` | `IReadRangeRef` | `void` | Sets format, alignment, and font for cells in a range. |
| `SelectRange()` | `IReadRangeRef` | `void` | Selects a range in the Excel application. |

#### Sheet Operations

| Method | Extends | Return Type | Description |
|--------|---------|------------|-------------|
| `DeleteSheet()` | `ISheetRef` | `void` | Deletes the sheet from the workbook. |
| `DuplicateSheet(string name)` | `ISheetRef` | `void` | Creates a copy of the sheet. |
| `RenameSheet(string name)` | `ISheetRef` | `void` | Renames the sheet. |
| `ProtectSheet(string password, ProtectSheetAdditionalPermissions additionalPermissions)` | `ISheetRef` | `void` | Protects the sheet with a password. |
| `ProtectSheet(string password)` | `ISheetRef` | `void` | Protects the sheet (no additional permissions). |
| `ProtectSheet(SecureString securedPassword, ProtectSheetAdditionalPermissions additionalPermissions)` | `ISheetRef` | `void` | Protects the sheet with a secure password. |
| `ProtectSheet(SecureString securedPassword)` | `ISheetRef` | `void` | Protects the sheet with a secure password (no additional permissions). |
| `UnprotectSheet(string password)` | `ISheetRef` | `void` | Unprotects the sheet. |
| `UnprotectSheet(SecureString securedPassword)` | `ISheetRef` | `void` | Unprotects the sheet with a secure password. |

#### Table & Pivot Operations

| Method | Extends | Return Type | Description |
|--------|---------|------------|-------------|
| `CreateTable(bool hasHeaders, bool replaceExisting, string tableName)` | `IReadWriteRangeRef` | `string` | Formats range as a named table. Returns the table name. |
| `CreateTable(bool replaceExisting, string tableName)` | `IReadWriteRangeRef` | `string` | Creates a table (assumes headers). |
| `CreatePivotTable(string destinationTableName, IReadWriteRangeRef destination, PivotTableDescriptor descriptor)` | `IReadRangeRef` | `void` | Creates a pivot table from range/table data. |
| `ChangePivotTableDataSource(IPivotTableRef pivotTable)` | `IWellDefinedReadRangeRef` | `void` | Changes the data source of a pivot table. |
| `RefreshPivotTable(PivotTableLayoutRowType? layoutRowType)` | `IPivotTableRef` | `void` | Refreshes pivot table data and optionally changes layout. |
| `FilterPivotTable(string columnName, IEnumerable<string> values, bool clearFilter)` | `IPivotTableRef` | `void` | Filters a pivot table by column values. |
| `Filter(FilterOptions options)` | `IReadWriteRangeRef` | `void` | Filters a range/table/sheet by column values. |
| `Sort(SortXDescriptor descriptor, bool hasHeaders)` | `IReadWriteRangeRef` | `void` | Sorts data by one or more columns. |
| `TextToColumns(IReadWriteRangeRef destRange, TextToColumnsOptions options)` | `IWellDefinedReadRangeRef` | `void` | Splits text into columns using delimiters or fixed width. |
| `TextToColumns(IReadWriteRangeRef destRange)` | `IWellDefinedReadRangeRef` | `void` | Splits text into columns using default options. |

#### Chart Operations

| Method | Extends | Return Type | Description |
|--------|---------|------------|-------------|
| `InsertExcelChart(ISheetRef sheet, ExcelChartCategory chartCategory, ExcelChartType chartType, int left, int top, int width, int height)` | `IReadRangeRef` | `IChartRef` | Creates a chart from range data. |
| `GetChart(ExcelChartAction action, string fileName, bool replaceFile)` | `IChartRef` | `void` | Saves chart to file or copies to clipboard. |
| `GetChart()` | `IChartRef` | `void` | Copies chart to clipboard. |

#### Export Operations

| Method | Extends | Return Type | Description |
|--------|---------|------------|-------------|
| `ExportExcelToSCV(string fileName)` | `IReadRangeRef` | `void` | Exports a range, table, sheet, or pivot table to a CSV file. **Note:** The `SCV` suffix is intentional — it matches the public API method name. |

### `IExcelProcess`

Controls interaction with the Excel application process.

> This type implements `IDisposable`. Always use inside a `using` statement or call `Dispose()` explicitly.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `ProcessId` | `int?` | The process ID of the Excel process. Is `null` until the Excel process is created or attached. |
| `Visible` | `bool` | Whether the Excel window is visible. |

#### Methods

| Method | Return Type | Description |
|--------|------------|-------------|
| `IsAlive()` | `bool` | Checks whether the Excel process is still running. |
| `Quit()` | `bool` | Terminates the Excel process. Returns true if successfully quit. |

### `ICurrentRowQuickHandle`

Represents the current row during a `ForEachRow` loop. Extends `IWellDefinedReadWriteRangeRef`.

#### Indexers

| Indexer | Type | Description |
|---------|------|-------------|
| `this[string column]` | `ExcelValue` (get/set) | Access cell value by column name. |
| `ByIndex[int index]` | `ExcelValue` (get/set) | Access cell value by column index. |
| `ByField[string name]` | `ExcelValue` (get/set) | Access cell value by field name. |

### `ExcelValue`

Represents a cell value from an Excel document (Windows/Interop API). Returned by `ICurrentRowQuickHandle` indexers and the `SelectedCell` property.

> All constructors are `internal`, so you do not use `new ExcelValue(...)` directly. In practice, you work with `ExcelValue` instances by reading from handle indexers (e.g., `row["Column"]`) and assigning primitive values to cells (e.g., `row["Column"] = 5;`) which are implicitly converted to `ExcelValue`. You can also use the typed value properties below to read or set the underlying cell value — see **Implicit Conversions** for the full list of supported types.

#### Read-Only Properties

| Property | Type | Description |
|----------|------|-------------|
| `Color` | `System.Drawing.Color` | The background color of the cell. |
| `Formula` | `string` | The formula of the cell (if any). |
| `RawValue` | `object` | The unformatted value of the cell. |
| `RawValueType` | `Type` | The CLR type of the raw value. |
| `Worksheet` | `string` | The name of the worksheet the cell belongs to. |
| `Address` | `string` | The cell address (e.g., `"A1"`). |

#### Typed Value Properties (get/set)

Use these to read or write cell values with type safety. The setter persists the value back to Excel.

| Property | Type | Description |
|----------|------|-------------|
| `StringValue` | `string` | Read/write a string value. |
| `Int32Value` | `int` | Read/write an integer value. |
| `BooleanValue` | `bool` | Read/write a boolean value. |
| `DoubleValue` | `double` | Read/write a double value. |
| `DecimalValue` | `decimal` | Read/write a decimal value. |
| `DateTimeValue` | `DateTime` | Read/write a DateTime value. |
| `TimeSpanValue` | `TimeSpan` | Read/write a TimeSpan value. |

#### Implicit Conversions

`ExcelValue` supports implicit conversion **from** `bool`, `int`, `long`, `double`, `decimal`, `string`, `DateTime`, and `TimeSpan` (allowing direct cell assignment) and **to** the same types (allowing direct reading):

```csharp
row["Quantity"] = 5;             // implicit conversion from int to ExcelValue
row["Name"] = "Alice";           // implicit conversion from string to ExcelValue
string name = row["Name"];       // implicit conversion from ExcelValue to string
int quantity = row["Quantity"];   // implicit conversion from ExcelValue to int
```

### `RangeValue`

Represents a range in Excel (Windows/Interop API). Returned by `IWorkbookQuickHandle.SelectedRange` and table indexers. Implements `ITableRef` and `IPivotTableRef`. Supports implicit conversion to and from `DataTable`, so `DataTable data = handle.Table["TableName"];` works directly.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `Worksheet` | `string` | The name of the worksheet the range belongs to. |
| `Address` | `string` | The address of the range (e.g., `"A1:D10"`). |
| `FullRangeName` | `string` | The full name of the range (e.g., `"Sheet1!A1:D10"`). |
| `FirstCell` | `string` | The address of the first cell in the range. |
| `RowCount` | `int` | The number of rows in the range. |
| `Columns` | `IEnumerable<string>` | The list of columns (when the range represents a table). |
| `TableName` | `string` | The table name (when the range represents a table). |
| `RangeType` | `ExcelRangeType` | The type of range: `Range`, `Table`, `PivotTable`, `Sheet`, or `DataTable`. |
| `DataTableOutValue` | `DataTable` | Helper DataTable for Out/InOut arguments. The getter always returns a new empty DataTable and does not read the current range contents (this is by design). |

---

## Static CSV Methods

These are static methods on the `ExcelOperations` class (no handle required).

| Method | Return Type | Description |
|--------|------------|-------------|
| `ExcelOperations.ReadCsvFile(string filePath, DelimitatorOptions delimiter, bool includeColumnNames, string encodingStr, bool ignoreQuotes)` | `DataTable` | Reads a CSV file into a DataTable. |
| `ExcelOperations.WriteCsvFile(string filePath, DataTable data, DelimitatorOptions delimiter, bool addHeaders, string encodingStr, bool shouldQuote)` | `void` | Writes a DataTable to a CSV file (replaces existing data). |
| `ExcelOperations.AppendCsvFile(string filePath, DataTable data, DelimitatorOptions delimiter, string encodingStr)` | `void` | Appends a DataTable to an existing CSV file. |

---

## Options & Configuration Classes

### `WorkbookOptions`

Options for opening or creating a workbook (portable API).

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `Path` | `string` | `null` | Path of the workbook. |
| `Password` | `string` | `null` | Password of the workbook, if necessary. |
| `CreateNew` | `bool` | `true` | Create the workbook if it does not exist. |
| `ConflictBehavior` | `ConflictBehavior?` | `null` | Behavior when a file already exists and `CreateNew` is true. When null, the existing file is opened. |

### `UseOptions`

Options for opening or creating Excel files (Windows/Interop API).

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `ExcelProcess` | `IExcelProcess` | `null` | Controls interaction with Excel. If null, options are retrieved from project settings. |
| `Path` | `string` | `null` | Path of the Excel file. |
| `Password` | `string` | `null` | Password for the Excel file. |
| `EditPassword` | `string` | `null` | Edit password for the Excel file. |
| `CreateIfNotExist` | `bool` | `true` | Create the file if it does not exist. |
| `KeepExcelOpen` | `bool` | `false` | Keep the file open after the operation. |
| `ReadFormatting` | `ReadFormattingOptions?` | `null` | How to format read values (Default, RawValue, DisplayValue). Null reads from project settings. |
| `ReadOnly` | `bool` | `false` | Open the workbook as read-only. |
| `ResizeWindow` | `ResizeWindowOptions` | `None` | Resize the Excel window (None, Minimize, Maximize). |
| `SaveChanges` | `bool` | `true` | Save changes after workbook operations. |
| `SensitivityOperation` | `ExcelLabelOperation` | `None` | Sensitivity label operation when opening/creating. |
| `SensitivityLabel` | `IExcelLabelObject` | `null` | Sensitivity label to apply (only when SensitivityOperation is Add). |

### `ScopeOptions`

Options for controlling the Excel process (Windows/Interop API). If a property is null, it is retrieved from project settings.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `DisplayAllerts` | `bool?` | `null` | Allow Excel to display alerts and messages. **Note:** The property name is intentionally spelled `DisplayAllerts` (not "Alerts") to match the source API. |
| `ExistingProcessAction` | `ExistingExcelProcessAction?` | `null` | Action if other Excel processes are running. |
| `FileConflictResolution` | `ExcelFileConflictResolution?` | `null` | Action if Excel document conflicts are detected between processes. |
| `LaunchMethod` | `ExcelStartMethod?` | `null` | How the Excel process is launched. |
| `LaunchTimeout` | `int?` | `null` | Time to wait for Excel to start (full process launch). |
| `MacroSetting` | `MacroSetting?` | `null` | Enable or disable macros. |
| `ProcessMode` | `ExcelProcessMode?` | `null` | New process, reuse if available, or unique for attended users. |
| `ShowExcelWindow` | `bool?` | `null` | Show the Excel window during automation. |

### `FilterOptions`

Options for filtering ranges (Windows/Interop API).

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `ColumnName` | `string` | `null` | Column containing the values to filter. |
| `ClearFilter` | `bool` | `false` | Clear any existing filter applied to the target range. |
| `Filter` | `IFilter` | `null` | Filter implementation: `BasicFilter` (list of values) or `AdvancedFilter` (conditions). |

### `BasicFilter`

Simple filter matching a list of values. Implements `IFilter`.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `Values` | `List<string>` | empty list | List of matching values. |

### `AdvancedFilter`

Filter with operator conditions. Implements `IFilter`.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `Operator` | `LogicalOperator` | `And` | Operator between the two conditions. |
| `Condition1` | `ExcelFilterOperator` | — | Operator for the first condition. |
| `Value1` | `string` | `null` | Value for the first condition. |
| `Condition2` | `ExcelFilterOperator` | — | Operator for the second condition. |
| `Value2` | `string` | `null` | Value for the second condition. |

### `TextToColumnsOptions`

Options for splitting text into columns.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `ParsingType` | `TextToColumnsParsingType` | `Delimited` | Delimited (by characters) or FixedWidth (by character count). |
| `NumberOfCharactersPerColumn` | `int` | `0` | Width of each data unit (fixed width mode). |
| `ColumnsDelimiters` | `TextToColumnsDelimiters` | Tab, Semicolon, Comma, Space | Delimiters to use (flags enum). |
| `SplitByLineBreak` | `bool` | `false` | Split by line breaks. |
| `OtherSeparator` | `char?` | `null` | Custom separator character (when `Other` flag is set). |
| `ConsecutiveOperatorsAsOne` | `bool` | `true` | Treat consecutive delimiters as one. |
| `TextQualifier` | `TextToColumnsTextQualifier` | `None` | Character that encloses text values. |

### `CreateChartConfig`

Configuration for creating a chart (portable API).

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `UseTableSource` | `bool` | `false` | Use a table as the data source (instead of a range). |
| `SourceSheet` | `string` | `null` | Sheet containing the source data. |
| `SourceRange` | `string` | `null` | Range address for the chart data (when `UseTableSource` is false). |
| `SourceTable` | `string` | `null` | Table name for the chart data (when `UseTableSource` is true). |
| `PlacementSheet` | `string` | `null` | Sheet where the chart will be placed. |
| `ChartCategory` | `ExcelChartCategory` | `Column` | Chart category (Area, Bar, Column, Line, Pie, Scatter). |
| `ChartType` | `ExcelChartType` | `xlColumnClustered` | Specific chart subtype. |
| `Height` | `int` | `211` | Chart height in points. |
| `Width` | `int` | `355` | Chart width in points. |
| `Left` | `int` | `60` | Left position in points. |
| `Top` | `int` | `20` | Top position in points. |

### `UpdateChartConfiguration`

Configuration for updating an existing chart (portable API).

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `ChartName` | `string` | `null` | Name of the chart to update. |
| `PlacementSheet` | `string` | `null` | Sheet containing the chart. |
| `Type` | `ChartModificationType` | — | Type of modification to apply. |
| `Modifications` | `IEnumerable<IChartModification>` | `null` | Collection of modifications to apply. |

#### Chart Modification Types (`IChartModification`)

Each modification type corresponds to a `ChartModificationType` value:

**`ChangeDataRangeChartModification`**

| Property | Type | Description |
|----------|------|-------------|
| `UseTableSource` | `bool` | Use a table as the data source. |
| `TableName` | `string` | Table name (when `UseTableSource` is true). |
| `SheetName` | `string` | Sheet containing the data range. |
| `Range` | `string` | Range address for the new data. |

**`ModifyChartTitleChartModification`**

| Property | Type | Description |
|----------|------|-------------|
| `Title` | `string` | New chart title text. |
| `ShowTitle` | `bool` | Whether to display the title. |

**`UpdateAxisTitleChartModification`**

| Property | Type | Description |
|----------|------|-------------|
| `Axis` | `AxisOrientationType` | Which axis to update (`Horizontal` or `Vertical`). |
| `ShowTitle` | `bool` | Whether to display the axis title. |
| `Title` | `string` | New axis title text. |

**`UpdateAxisBoundsChartModification`**

| Property | Type | Description |
|----------|------|-------------|
| `Axis` | `AxisOrientationType` | Which axis to update (`Horizontal` or `Vertical`). |
| `MinBound` | `double?` | Minimum axis value (null for auto). |
| `MaxBound` | `double?` | Maximum axis value (null for auto). |

**`ShowHideLegendChartModification`**

| Property | Type | Description |
|----------|------|-------------|
| `ShowLegend` | `bool` | Whether to display the chart legend. |

**`ShowHideDataLabelsChartModification`**

| Property | Type | Description |
|----------|------|-------------|
| `ShowDataLabels` | `bool` | Whether to display data labels. |

### `PivotTableDescriptor`

Describes the structure of a pivot table (Windows/Interop API).

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `Rows` | `List<RowPivotTableFieldDescription>` | empty list | Fields to use as row labels. |
| `Columns` | `List<ColumnPivotTableFieldDescription>` | empty list | Fields to use as column labels. |
| `Filters` | `List<FilterPivotTableFieldDescription>` | empty list | Fields to use as report filters. |
| `Values` | `List<ValuePivotTableFieldDescription>` | empty list | Fields to aggregate as values. |
| `ValuesMode` | `PivotTableValuesMode` | `Columns` | Display values in columns or rows. |
| `LayoutRowType` | `PivotTableLayoutRowType` | `Compact` | Row layout type (Compact, Tabular, Outline). |

**Pivot field description types** — All inherit from `PivotTableFieldDescriptionBase` with a `Name` property (the source column name). `ValuePivotTableFieldDescription` adds:

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `Function` | `PivotTableFunction` | — | Aggregation function (Sum, Count, Average, Max, Min, Product, etc.). |

### `IPivotTableInfo`

Marker interface for pivot table creation info (portable API). Used by `IWorkHandle.CreatePivotTable`. No properties — implementations define the pivot table structure.

### `SortXDescriptor`

Describes columns to sort by (Windows/Interop API).

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `SortColumns` | `List<SortXColumnModel>` | empty list | Ordered list of columns to sort by. |

### `SortXColumnModel`

Holds sort information for a single column.

**Constructor:** `SortXColumnModel(string columnName, OrderType sortOrder)`

| Property | Type | Description |
|----------|------|-------------|
| `ColumnName` | `string` | Name of the column to sort by. |
| `SortOrder` | `OrderType` | Sort direction: `Ascending` or `Descending`. |
| `ColumnIndex` | `int` | Column index (set automatically during sort). |

### `ICellFormat`

Represents a cell number format for formatting operations.

| Member | Type | Description |
|--------|------|-------------|
| `FormatType` | `CellFormat` | The format category: `General`, `Number`, `Date`, `Time`, `Percentage`, `Currency`, `Text`, `Custom`. |
| `UseLocal` | `bool` | Whether to use locale-specific formatting. |
| `ToExcelString(ExcelFormatParameters)` | `string` | Converts the format to an Excel format string. |

### `AlignmentOptions`

Alignment settings for `FormatRange`.

| Property | Type | Description |
|----------|------|-------------|
| `HorizontalAlignment` | `ExcelRangeHorizontalAlignment` | Horizontal alignment. |
| `VerticalAlignment` | `ExcelRangeVerticalAlignment` | Vertical alignment. |
| `WrapText` | `bool` | Whether to wrap text in the cell. |

### `FontOptions`

Font settings for `FormatRange`.

| Property | Type | Description |
|----------|------|-------------|
| `FontFamilyName` | `string` | Font family name (e.g., `"Calibri"`). |
| `Style` | `ExcelRangeFontStyle` | Font style (bold, italic, etc.). |
| `Size` | `double` | Font size in points. |
| `Color` | `Color` | Font foreground color. |
| `FillColor` | `Color` | Cell fill/background color. |
| `UnderlineStyle` | `ExcelRangeUnderlineStyle` | Underline style. |

### `IExcelLabelObject`

Sensitivity label to apply to or retrieve from a workbook.

| Property | Type | Description |
|----------|------|-------------|
| `LabelId` | `string` | Sensitivity label ID. |
| `Justification` | `string` | Justification for changing the label. |

---

## Enum Reference

**`ConflictBehavior`**: `Replace`, `Fail`, `Skip`

**`ReadFormattingOptions`**: `Default`, `RawValue`, `DisplayValue`

**`ResizeWindowOptions`**: `None`, `Minimize`, `Maximize`

**`ExcelLabelOperation`**: `None`, `Add`, `Clear`

**`EmptyRowBehavior`**: `StopAfterThreeConsecutiveEmptyRows`, `Stop`, `Skip`, `Process`

**`PdfSaveQuality`**: `StandardQuality`, `MinimumQuality`

**`ExcelSaveAsType`**: `OpenXmlWorkbook`, `BinaryWorkbook`, `MacroEnabledWorkbook`, `OldWorkbook`

**`ExcelChartAction`**: `CopyToClipboard`, `SaveAsPicture`

**`ExcelChartCategory`**: `Area`, `Bar`, `Column`, `Line`, `Pie`, `Scatter`

**`CopyPasteRangeOptions`**: `All`, `Values`, `Formulas`, `Formats`

**`FindReplaceOptions`**: `Find`, `Replace`, `ReplaceAll`

**`LookInOptions`**: `Values`, `Formulas`

**`DeleteRowsOption`**: `Specific`, `Visible`, `Hidden`, `Duplicates`

**`InsertRowPosition`**: `Start`, `End`, `Specific`

**`ColumnRelativePosition`**: `Before`, `After`

**`ColumnsCompare`**: `IndividualColumns`, `AllColumns`

**`MatchType`**: `LargestValueLessOrEqual`, `ExactlyEqual`, `SmallestValueGreaterOrEqual`

**`LastRowConfiguration`**: `LastPopulatedRow`, `FirstEmptyRow`

**`PivotTableLayoutRowType`**: `Compact`, `Tabular`, `Outline`

**`ProtectSheetAdditionalPermissions`** (flags): `None`, `AllowDeletingColumns`, `AllowDeletingRows`, `DrawingObjects`, `Scenarios`, `AllowFiltering`, `AllowFormattingCells`, `AllowFormattingColumns`, `AllowFormattingRows`, `AllowInsertingColumns`, `AllowInsertingHyperlinks`, `AllowInsertingRows`, `AllowSorting`, `AllowUsingPivotTables`

**`DelimitatorOptions`**: `Comma`, `Semicolon`, `Pipe`, `Caret`, `Tab`

**`ExcelProcessMode`**: `AlwaysCreateNew`, `AttendedUser`, `ReuseIfExists`, `OnlyIfExists`

**`ExcelFileConflictResolution`**: `None`, `CloseWithoutSaving`, `PromptUser`, `ThrowException`

**`ExistingExcelProcessAction`**: `None`, `ForceKill`

**`ExcelStartMethod`**: `Automation`, `Application`

**`MacroSetting`**: `EnableAll`, `DisableAll`, `ReadFromExcelSettings`

**`LogicalOperator`**: `And`, `Or`

**`ExcelFilterOperator`**: `NONE`, `LT` (<), `GT` (>), `LTE` (<=), `GTE` (>=), `EQ` (=), `NOTEQ` (!=), `EMPTY`, `NOTEMPTY`, `STARTSWITH`, `ENDSWITH`, `CONTAINS`, `NOTSTARTSWITH`, `NOTENDSWITH`, `NOTCONTAINS`

**`ExcelChartType`**: `xlArea`, `xlAreaStacked`, `xlAreaStacked100`, `xlBarClustered`, `xlBarStacked`, `xlBarStacked100`, `xlColumnClustered`, `xlColumnStacked`, `xlColumnStacked100`, `xlLine`, `xlLineMarkers`, `xlLineMarkersStacked`, `xlLineMarkersStacked100`, `xlLineStacked`, `xlLineStacked100`, `xlDoughnut`, `xlPie`, `xlXYScatterSmoothNoMarkers`, `xlXYScatterSmooth`, `xlXYScatterLinesNoMarkers`, `xlXYScatterLines`, `xlXYScatter`, `Other`

**`TextToColumnsParsingType`**: `Delimited`, `FixedWidth`

**`TextToColumnsDelimiters`** (flags): `None`, `Tab`, `Semicolon`, `Comma`, `Space`, `Other`

**`TextToColumnsTextQualifier`**: `None`, `DoubleQuote`, `SingleQuote`

**`PivotTableFunction`**: `Sum`, `Count`, `Average`, `Max`, `Min`, `Product`, `CountNumbers`, `StdDev`, `StdDevp`, `Var`, `Varp`

**`PivotTableValuesMode`**: `Columns`, `Rows`

**`ChartModificationType`**: `ChangeDataRange`, `ModifyChartTitle`, `UpdateAxisTitle`, `UpdateAxisBounds`, `ShowHideLegend`, `ShowHideDataLabels`

**`ExcelRangeType`**: `Range`, `Table`, `PivotTable`, `Sheet`, `DataTable`

**`OrderType`**: `Ascending`, `Descending`

**`CellFormat`**: `General`, `Number`, `Date`, `Time`, `Percentage`, `Currency`, `Text`, `Custom`

**`ExcelRangeHorizontalAlignment`**: `xlHAlignGeneral`, `xlHAlignLeft`, `xlHAlignCenter`, `xlHAlignRight`, `xlHAlignFill`, `xlHAlignJustify`, `xlHAlignCenterAcrossSelection`, `xlHAlignDistributed`

**`ExcelRangeVerticalAlignment`**: `xlVAlignTop`, `xlVAlignCenter`, `xlVAlignBottom`, `xlVAlignJustify`, `xlVAlignDistributed`

**`ExcelRangeFontStyle`**: `Regular`, `Italic`, `Bold`, `BoldItalic`

**`ExcelRangeUnderlineStyle`**: `None`, `Single`, `Double`, `SingleAccounting`, `DoubleAccounting`

**`AxisOrientationType`**: `Horizontal`, `Vertical`

---

## Common Patterns

### Read and process Excel data (Portable)

```csharp
[Workflow]
public void Execute()
{
    using var workbook = excel.UseWorkBook("C:\\Data\\report.xlsx", createNew: false);
    var data = workbook.ReadRange("Sheet1", "A1:D100", addHeaders: true, preserveFormat: false);

    foreach (DataRow row in data.Rows)
    {
        var name = row["Name"].ToString();
        var amount = Convert.ToDecimal(row["Amount"]);
        Log($"Processing {name}: {amount:C}");
    }
}
```

### Read, transform, and write back (Windows/Interop)

```csharp
[Workflow]
public void Execute()
{
    using var file = excel.UseExcelFile("C:\\Data\\sales.xlsx", saveChanges: true, createIfNotExist: false);
    var sheet = file.Sheet["Sales"];

    var data = sheet.ReadRange(hasHeaders: true, visibleRowsOnly: false);

    // Add a computed column
    data.Columns.Add("Total", typeof(decimal));
    foreach (DataRow row in data.Rows)
    {
        row["Total"] = Convert.ToDecimal(row["Quantity"]) * Convert.ToDecimal(row["Price"]);
    }

    // Write results to a new sheet
    var resultsSheet = file.InsertSheet("Results");
    resultsSheet.WriteRange(data, append: false, excludeHeaders: false);
}
```

### Iterate rows and update cells (Windows/Interop)

```csharp
[Workflow]
public void Execute()
{
    using var file = excel.UseExcelFile("C:\\Data\\inventory.xlsx");
    var sheet = file.Sheet["Inventory"];

    sheet.ForEachRow(EmptyRowBehavior.Stop, forceFirstRowAsHeaders: true, saveAfterEachRow: false, row =>
    {
        var quantity = row["Quantity"].Int32Value;
        if (quantity < 10)
        {
            row["Status"].StringValue = "Low Stock";
        }
    });
}
```

### Create a workbook with options (Portable)

```csharp
[Workflow]
public void Execute()
{
    var options = new WorkbookOptions
    {
        Path = "C:\\Output\\new_report.xlsx",
        CreateNew = true,
        ConflictBehavior = ConflictBehavior.Replace
    };

    using var workbook = excel.UseWorkBook(options);
    var report = new DataTable();
    report.Columns.Add("Date", typeof(string));
    report.Columns.Add("Revenue", typeof(decimal));
    report.Rows.Add("2026-01-01", 15000.50m);
    report.Rows.Add("2026-01-02", 22300.75m);

    workbook.WriteRange("Summary", "A1", report, addHeaders: true);
}
```

### Excel Process Scope with filtering and export (Windows/Interop)

```csharp
[Workflow]
public void Execute()
{
    using var process = excel.ExcelProcessScope(new ScopeOptions
    {
        ShowExcelWindow = false,
        MacroSetting = MacroSetting.DisableAll
    });

    var useOptions = new UseOptions
    {
        Path = "C:\\Data\\large_dataset.xlsx",
        ExcelProcess = process,
        SaveChanges = false,
        ReadOnly = true
    };

    using var file = excel.UseExcelFile(useOptions);
    var sheet = file.Sheet["Data"];

    // Filter to specific values
    sheet.Filter(new FilterOptions
    {
        ColumnName = "Region",
        Filter = new BasicFilter { Values = new List<string> { "North", "East" } }
    });

    // Read only visible (filtered) rows
    var filtered = sheet.ReadRange(hasHeaders: true, visibleRowsOnly: true);

    // Export to CSV
    ExcelOperations.WriteCsvFile("C:\\Output\\filtered.csv", filtered, UiPath.CSV.DelimitatorOptions.Comma,
        addHeaders: true, encodingStr: "utf-8", shouldQuote: true);
}
```
