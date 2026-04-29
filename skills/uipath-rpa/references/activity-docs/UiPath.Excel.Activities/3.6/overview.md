# UiPath Excel Activities

`UiPath.Excel.Activities`

Activities for reading, writing, and manipulating Excel workbooks, CSV files, charts, pivot tables, and cell formatting. Includes both cross-platform (file-based) and Windows-only (Excel Interop) activities.

## Documentation

- [XAML Activities Reference](activities/) — Per-activity documentation for XAML workflows

## Activities

### Cross-Platform — CSV

| Activity | Description |
|----------|-------------|
| [Read CSV](activities/ReadCsvFile.md) | Reads all entries from a CSV file into a DataTable |
| [Write CSV](activities/AppendWriteCsvFile.md) | Writes or appends a DataTable to a CSV file |

### Cross-Platform — Workbook

| Activity | Description |
|----------|-------------|
| [Read Range Workbook](activities/ReadRange.md) | Reads a range from a spreadsheet as a DataTable |
| [Write Range Workbook](activities/WriteRange.md) | Writes a DataTable to a spreadsheet starting from a cell |
| [Read Cell Workbook](activities/ReadCell.md) | Reads the value of a cell as a string |
| [Read Cell Formula Workbook](activities/ReadCellFormula.md) | Reads the formula of a cell as a string |
| [Write Cell Workbook](activities/WriteCell.md) | Writes a value into a cell |
| [Append Range Workbook](activities/AppendRange.md) | Appends a DataTable after existing data in a sheet |
| [Get Table Range Workbook](activities/GetTableRange.md) | Gets the range of a named table |
| [Read Row Workbook](activities/ReadRow.md) | Reads row values starting from a cell |
| [Read Column Workbook](activities/ReadColumn.md) | Reads column values starting from a cell |
| [Create Pivot Table Workbook](activities/CreatePivotTable.md) | Creates a pivot table from a data source |
| [Get Cell Color Workbook](activities/GetCellColor.md) | Gets the background color of a cell |
| [Set Range Color Workbook](activities/SetRangeColor.md) | Sets the background color of a range |
| [Create New Workbook](activities/CreateNewWorkbook.md) | Creates a new Excel workbook |
| [Get Sheets Workbook](activities/GetSheets.md) | Gets the list of sheet names |
| [Insert Chart Workbook](activities/InsertChart.md) | Inserts a chart into a workbook |
| [Update Chart Workbook](activities/UpdateChart.md) | Updates an existing chart with modifications |

### Windows — Scopes

| Activity | Description |
|----------|-------------|
| [Use Excel File](activities/ExcelApplicationCard.md) | Opens an Excel file and provides a scope for Excel activities |
| [Excel Process Scope](activities/ExcelProcessScopeX.md) | Manages the Excel application process lifecycle |

### Windows — Range

| Activity | Description |
|----------|-------------|
| [Read Range](activities/ReadRangeX.md) | Reads data from a range into a DataTable |
| [Write Range](activities/WriteRangeX.md) | Writes a DataTable to a range |
| [Append Range](activities/AppendRangeX.md) | Appends data after existing content |
| [Clear Range](activities/ClearRangeX.md) | Clears the contents of a range |
| [Copy Paste Range](activities/CopyPasteRangeX.md) | Copies a range and pastes it to a destination |
| [Fill Range](activities/FillRangeX.md) | Fills a range using auto-fill rules |
| [Auto Fit](activities/AutoFitX.md) | Auto-fits column widths or row heights |
| [Create Table](activities/CreateTableX.md) | Creates a named table from a range |
| [Delete Column](activities/DeleteColumnX.md) | Deletes a column from a sheet |
| [Delete Rows](activities/DeleteRowsX.md) | Deletes rows from a sheet |
| [Insert Rows](activities/InsertRowsX.md) | Inserts rows into a sheet |
| [Insert Column](activities/InsertColumnX.md) | Inserts a column into a sheet |
| [For Each Excel Row](activities/ExcelForEachRowX.md) | Iterates over each row in a range |
| [Export to CSV](activities/ExportExcelToCsvX.md) | Exports an Excel range to a CSV file |
| [Find/Replace Value](activities/FindReplaceValueX.md) | Finds and optionally replaces values in a range |
| [Find First/Last Data Row](activities/FindFirstLastDataRowX.md) | Finds the first and last row with data |
| [Lookup Range](activities/LookupX.md) | Looks up a value in a range and returns the cell address |
| [MATCH Function](activities/MatchFunctionX.md) | Finds the position of a value in a range |
| [VLOOKUP](activities/VLookupX.md) | Performs a vertical lookup in a range |
| [Filter](activities/FilterX.md) | Applies filters to a range |
| [Sort](activities/SortX.md) | Sorts a range by one or more columns |
| [Text to Columns](activities/TextToColumnsX.md) | Splits text in a column into multiple columns |
| [Remove Duplicates](activities/RemoveDuplicatesX.md) | Removes duplicate rows from a range |
| [Format Range](activities/FormatRangeX.md) | Applies formatting (font, alignment, data type) to a range |
| [Get Selected Range](activities/GetSelectedRangeX.md) | Gets the currently selected range in Excel |
| [Select Range](activities/SelectRangeX.md) | Selects a range in the active Excel workbook |

### Windows — Cell

| Activity | Description |
|----------|-------------|
| [Read Cell Value](activities/ReadCellValueX.md) | Reads the value of a cell |
| [Read Cell Formula](activities/ReadCellFormulaX.md) | Reads the formula of a cell |
| [Write Cell](activities/WriteCellX.md) | Writes a value to a cell |
| [Auto Fill](activities/AutoFillX.md) | Auto-fills cells based on a source range pattern |
| [Get Cell Color](activities/GetCellColorX.md) | Gets the background color of a cell |

### Windows — Workbook Management

| Activity | Description |
|----------|-------------|
| [Save Excel File](activities/SaveExcelFileX.md) | Saves the current Excel file |
| [Save Excel File As](activities/SaveExcelFileAsX.md) | Saves the Excel file with a new name or format |
| [Save As PDF](activities/SaveAsPdfX.md) | Exports the workbook or sheet to PDF |
| [Insert Sheet](activities/InsertSheetX.md) | Inserts a new sheet |
| [Delete Sheet](activities/DeleteSheetX.md) | Deletes a sheet |
| [Duplicate Sheet](activities/DuplicateSheetX.md) | Duplicates a sheet |
| [Rename Sheet](activities/RenameSheetX.md) | Renames a sheet |
| [For Each Sheet](activities/ForEachSheetX.md) | Iterates over each sheet in a workbook |
| [Protect Sheet](activities/ProtectSheetX.md) | Protects a sheet with a password |
| [Unprotect Sheet](activities/UnprotectSheetX.md) | Removes protection from a sheet |
| [Run Spreadsheet Macro](activities/ExecuteMacroX.md) | Executes an Excel macro |
| [Invoke VBA](activities/InvokeVBAX.md) | Invokes a VBA script from a code file |
| [Refresh Data Connections](activities/RefreshDataConnectionsX.md) | Refreshes all data connections in the workbook |
| [Add Sensitivity Label](activities/AddSensitivityLabelX.md) | Adds or updates a sensitivity label |
| [Get Sensitivity Label](activities/GetSensitivityLabelX.md) | Gets the current sensitivity label |

### Windows — Pivot Table

| Activity | Description |
|----------|-------------|
| [Create Pivot Table](activities/CreatePivotTableXv2.md) | Creates a pivot table from a data source |
| [Change Pivot Table Data Source](activities/ChangePivotTableDataSourceX.md) | Changes the data source of a pivot table |
| [Refresh Pivot Table](activities/RefreshPivotTableX.md) | Refreshes a pivot table |
| [Filter Pivot Table](activities/FilterPivotTableX.md) | Applies filters to a pivot table |

### Windows — Chart

| Activity | Description |
|----------|-------------|
| [Insert Excel Chart](activities/InsertExcelChartX.md) | Inserts a chart into a sheet |
| [Update Chart](activities/UpdateChartX.md) | Updates an existing chart with modifications |
| [Copy Chart to Clipboard](activities/CopyChartToClipboardX.md) | Copies a chart to the clipboard |
