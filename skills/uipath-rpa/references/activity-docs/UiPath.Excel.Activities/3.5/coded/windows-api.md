# Excel — Windows (Interop) API

Full-featured API using `excel.UseExcelFile(...)` returning `IWorkbookQuickHandle`. Uses COM interop. For general info see [excel.md](excel.md).

---

## Opening Excel Files

### `excel.UseExcelFile(string path)`
Opens an Excel file with default options (save changes = true, create if not exists = true).
Returns `IWorkbookQuickHandle` (disposable — use with `using`).

```csharp
using var workbook = excel.UseExcelFile("data.xlsx");
```

### `excel.UseExcelFile(string path, bool saveChanges, bool createIfNotExist)`

```csharp
using var workbook = excel.UseExcelFile("data.xlsx", saveChanges: true, createIfNotExist: false);
```

### `excel.UseExcelFile(UseOptions options)`
Full control over how the file is opened.

```csharp
using var workbook = excel.UseExcelFile(new UseOptions
{
    Path = "data.xlsx",
    Password = "secret",
    EditPassword = "editSecret",
    CreateIfNotExist = true,
    KeepExcelOpen = false,
    ReadFormatting = ReadFormattingOptions.Default,
    ReadOnly = false,
    ResizeWindow = ResizeWindowOptions.None,
    SaveChanges = true,
    SensitivityOperation = ExcelLabelOperation.None,
    SensitivityLabel = null
});
```

#### `UseOptions` Properties

| Property | Type | Default | Description |
|---|---|---|---|
| `Path` | `string` | — | Path of the Excel file |
| `Password` | `string` | `null` | Password for the file |
| `EditPassword` | `string` | `null` | Edit password for the file |
| `CreateIfNotExist` | `bool` | `true` | Create the file if it does not exist |
| `KeepExcelOpen` | `bool` | `false` | Keep the file open after the operation |
| `ReadFormatting` | `ReadFormattingOptions?` | `null` (from settings) | How to read cell values |
| `ReadOnly` | `bool` | `false` | Open the workbook read-only |
| `ResizeWindow` | `ResizeWindowOptions` | `None` | Resize the Excel window |
| `SaveChanges` | `bool` | `true` | Save changes when done |
| `ExcelProcess` | `IExcelProcess` | `null` | Excel process to use (from `ExcelProcessScope`) |
| `SensitivityOperation` | `ExcelLabelOperation` | `None` | Sensitivity label operation |
| `SensitivityLabel` | `IExcelLabelObject` | `null` | Sensitivity label to apply |

---

## Excel Process Scope

Controls the interaction with the Excel application.

### `excel.ExcelProcessScope()`
Creates an `IExcelProcess` using default options from project settings.

### `excel.ExcelProcessScope(ScopeOptions options)`

```csharp
using var excelProcess = excel.ExcelProcessScope(new ScopeOptions
{
    DisplayAllerts = false,
    ShowExcelWindow = false,
    MacroSetting = MacroSetting.EnableAll
});

using var workbook = excel.UseExcelFile(new UseOptions
{
    Path = "macro_file.xlsm",
    ExcelProcess = excelProcess
});
```

#### `ScopeOptions` Properties

| Property | Type | Description |
|---|---|---|
| `DisplayAllerts` | `bool?` | Allow Excel alerts and messages |
| `ExistingProcessAction` | `ExistingExcelProcessAction?` | Action if other Excel processes are running |
| `FileConflictResolution` | `ExcelFileConflictResolution?` | Action for file conflicts between Excel processes |
| `LaunchMethod` | `ExcelStartMethod?` | How the Excel process is launched |
| `LaunchTimeout` | `int?` | Time to wait for Excel to start |
| `MacroSetting` | `MacroSetting?` | Enable or disable macros |
| `ProcessMode` | `ExcelProcessMode?` | New process, reuse, or ensure unique |
| `ShowExcelWindow` | `bool?` | Show the Excel window during automation |

---

## IWorkbookQuickHandle — Navigating the Workbook

`IWorkbookQuickHandle` is the main handle returned by `UseExcelFile`. It provides indexers to access sheets, tables, and pivot tables.

### Accessing Sheets

```csharp
// Access a sheet by name — returns WorksheetQuickHandle (implements ISheetRef)
var sheet = workbook.Sheet["Sheet1"];
```

### Accessing Ranges

```csharp
// Access a range within a sheet — returns RangeValue (implements IReadWriteRangeRef)
var range = workbook.Sheet["Sheet1"].Range["A1:C10"];

// Whole sheet as a range (ISheetRef implements IReadWriteRangeRef)
IReadWriteRangeRef wholeSheet = workbook.Sheet["Sheet1"];
```

### Accessing Cells

```csharp
// Access a cell — returns ExcelValue (implements IReadWriteCellRef)
var cell = workbook.Sheet["Sheet1"].Cell["A1"];

// Access with row offset
var cellWithOffset = workbook.Sheet["Sheet1"].Cell["A1", 2]; // A3
```

### Accessing Tables

```csharp
// Access a named table — returns RangeValue
var table = workbook.Table["MyTable"];
```

### Accessing Pivot Tables

```csharp
// Access a pivot table by name within a sheet
var pivot = workbook.Sheet["Sheet1"].PivotTable["PivotTable1"];

// Access all pivot tables in the workbook
var allPivots = workbook.AllPivotTables;
```

### Accessing Charts

```csharp
// Access a chart by name within a sheet
var chart = workbook.Sheet["Sheet1"].Chart["Chart1"];
```

### Other Properties

| Property | Type | Description |
|---|---|---|
| `FilePath` | `string` | The workbook file path |
| `SelectedRange` | `RangeValue` | Currently selected range |
| `SelectedCell` | `ExcelValue` | Currently selected cell |
| `SelectedSheet` | `WorksheetQuickHandle` | Currently selected sheet |

---

## Reading Data

### ReadRange — Read a range as DataTable

```csharp
// Read with default formatting
DataTable dt = workbook.Sheet["Sheet1"].ReadRange(hasHeaders: true, visibleRowsOnly: false);

// Read with specific formatting options
DataTable dt = workbook.Sheet["Sheet1"].ReadRange(
    hasHeaders: true,
    readFormattingOptions: ReadFormattingOptions.DisplayValue,
    visibleRowsOnly: false
);

// Read a specific range
DataTable dt = workbook.Sheet["Sheet1"].Range["A1:D10"].ReadRange(hasHeaders: true, visibleRowsOnly: true);

// Read from a named table
DataTable dt = workbook.Table["MyTable"].ReadRange(hasHeaders: true, visibleRowsOnly: false);
```

**Parameters:**
| Parameter | Type | Description |
|---|---|---|
| `hasHeaders` | `bool` | First row is a header row |
| `readFormattingOptions` | `ReadFormattingOptions?` | Formatting to apply. `null` uses parent settings. Non-default values result in slower performance |
| `visibleRowsOnly` | `bool` | Read only visible rows (ignores filtered/hidden) |

### ReadCellValue — Read a single cell value

```csharp
// Read formatted value
object value = workbook.Sheet["Sheet1"].Cell["B2"].ReadCellValue();

// Read raw value (no formatting)
object rawValue = workbook.Sheet["Sheet1"].Cell["B2"].ReadCellValue(getFormattedText: false);
```

### GetCellColor

```csharp
Color color = workbook.Sheet["Sheet1"].Cell["A1"].GetCellColorInternal();
```

---

## Writing Data

### WriteRange — Write a DataTable to a range

```csharp
// Write to a sheet (overwrites existing data)
workbook.Sheet["Sheet1"].WriteRange(dataTable, append: false, excludeHeaders: false);

// Append data
workbook.Sheet["Sheet1"].WriteRange(dataTable, append: true, excludeHeaders: false);

// Write to a specific range
workbook.Sheet["Sheet1"].Range["C1"].WriteRange(dataTable, append: false, excludeHeaders: true);

// Write with empty source handling
workbook.Sheet["Sheet1"].WriteRange(dataTable, append: false, excludeHeaders: false, ignoreEmptySource: true);
```

**Parameters:**
| Parameter | Type | Description |
|---|---|---|
| `source` | `DataTable` | The data to write |
| `append` | `bool` | Append starting at first blank row |
| `excludeHeaders` | `bool` | Skip writing column headers |
| `ignoreEmptySource` | `bool` | If `true`, empty DataTable is ignored. If `false`, throws error |

### WriteCell — Write to a single cell

```csharp
// Write a value
workbook.Sheet["Sheet1"].Cell["A1"].WriteCell("Hello World");

// Write a formula
workbook.Sheet["Sheet1"].Cell["B1"].WriteCell("=SUM(A1:A10)");

// Write with row offset
workbook.Sheet["Sheet1"].Cell["A1"].WriteCell("Value", rowOffset: 3); // writes to A4
```

### AppendRange — Append data

```csharp
// Simple append (range-to-range)
workbook.Sheet["Sheet1"].AppendRange(sourceRange);

// Append with options
workbook.Sheet["Sheet1"].AppendRange(
    source: workbook.Sheet["Sheet2"],
    columnName: "A",
    transpose: false,
    pasteOptions: CopyPasteRangeOptions.Values,
    destinationHasHeaders: true,
    excludeSourceHeaders: true
);
```

### FillRange — Fill all cells in a range

```csharp
workbook.Sheet["Sheet1"].Range["A1:A10"].FillRange("Default Value");
workbook.Sheet["Sheet1"].Range["B1:B10"].FillRange("=A1*2");
```

### CopyPasteRange

```csharp
workbook.Sheet["Sheet1"].Range["A1:C10"].CopyPasteRange(
    sourceRange: workbook.Sheet["Sheet2"].Range["A1:C10"],
    excludeSourceHeaders: false,
    excludeDestinationHeaders: false,
    transpose: false,
    options: CopyPasteRangeOptions.All
);
```

---

## Iterating

### ForEachRow — Iterate over rows

```csharp
// Simple iteration
workbook.Sheet["Sheet1"].ForEachRow(row =>
{
    // Access cell by column letter
    var name = row["A"];

    // Access by field/header name
    var email = row.ByField["Email"];

    // Access by column index (1-based)
    var id = row.ByIndex[1];

    // Write to current row
    row.ByField["Status"] = "Processed";
});

// With options
workbook.Sheet["Sheet1"].ForEachRow(
    emptyRowBehavior: EmptyRowBehavior.Stop,
    forceFirstRowAsHeaders: true,
    saveAfterEachRow: false,
    act: row =>
    {
        Log($"Processing: {row.ByField["Name"]}");
    }
);

// With break support (return false to stop)
workbook.Sheet["Sheet1"].ForEachRow(row =>
{
    if (row.ByField["Name"].ToString() == "STOP")
        return false; // break
    Log(row.ByField["Name"].ToString());
    return true; // continue
});
```

**Parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `emptyRowBehavior` | `EmptyRowBehavior` | `Stop` | Action on empty rows |
| `forceFirstRowAsHeaders` | `bool` | `false` | First row is header |
| `saveAfterEachRow` | `bool` | `false` | Save workbook after each row |

**`EmptyRowBehavior` enum:**
- `Stop` — stop at first empty row
- `StopAfterThreeConsecutiveEmptyRows` — stop after 3 consecutive empty rows
- `Skip` — skip empty rows, continue processing
- `Process` — process empty rows too

### ForEachSheet — Iterate over sheets

```csharp
// Simple iteration
workbook.ForEachSheet(sheet =>
{
    Log($"Sheet: {sheet.Name}");
    DataTable dt = sheet.ReadRange(true, false);
    Log($"  Rows: {dt.Rows.Count}");
});

// With break support
workbook.ForEachSheet(sheet =>
{
    if (sheet.Name == "Summary")
        return false; // stop
    return true;
});
```

---

## Sheet Operations

### InsertSheet

```csharp
ISheetRef newSheet = workbook.InsertSheet("NewSheet");
```

### DeleteSheet

```csharp
workbook.Sheet["OldSheet"].DeleteSheet();
```

### DuplicateSheet

```csharp
workbook.Sheet["Template"].DuplicateSheet("TemplateCopy");
```

### RenameSheet

```csharp
workbook.Sheet["Sheet1"].RenameSheet("MainData");
```

### ProtectSheet / UnprotectSheet

```csharp
// Protect with password
workbook.Sheet["Sheet1"].ProtectSheet("password123");

// Protect with additional permissions
workbook.Sheet["Sheet1"].ProtectSheet("password123",
    ProtectSheetAdditionalPermissions.AllowSorting | ProtectSheetAdditionalPermissions.AllowFiltering);

// Unprotect
workbook.Sheet["Sheet1"].UnprotectSheet("password123");
```

**`ProtectSheetAdditionalPermissions` flags:**
`None`, `AllowDeletingColumns`, `AllowDeletingRows`, `DrawingObjects`, `Scenarios`, `AllowFiltering`, `AllowFormattingCells`, `AllowFormattingColumns`, `AllowFormattingRows`, `AllowInsertingColumns`, `AllowInsertingHyperlinks`, `AllowInsertingRows`, `AllowSorting`, `AllowUsingPivotTables`

---

## Row and Column Operations

### InsertRows

```csharp
// Insert 3 rows at the end
workbook.Sheet["Sheet1"].InsertRows(3);

// Insert 2 rows at a specific position
workbook.Sheet["Sheet1"].InsertRows(
    nbOfRows: 2,
    insertPosition: InsertRowPosition.Specific,
    specificIndex: 5,
    hasHeaders: true
);
```

**`InsertRowPosition` enum:** `Start`, `End`, `Specific`

### DeleteRows

```csharp
workbook.Sheet["Sheet1"].DeleteColumn(
    deleteOption: DeleteRowsOption.Specific,
    rowPositions: "1,3,5",
    hasHeaders: true
);
```

**`DeleteRowsOption` enum:** `Specific`, `Visible`, `Hidden`, `Duplicates`

### InsertColumn

```csharp
// Insert before column A
workbook.Sheet["Sheet1"].InsertColumn("A");

// Insert after column B with header and format
workbook.Sheet["Sheet1"].InsertColumn(
    columnName: "B",
    position: ColumnRelativePosition.After,
    hasHeaders: true,
    newColumnHeader: "New Column",
    columnFormat: new GeneralFormat()
);
```

### DeleteColumn

```csharp
workbook.Sheet["Sheet1"].DeleteColumn(columnName: "C", hasHeaders: true);
```

### ClearRange

```csharp
workbook.Sheet["Sheet1"].ClearRange();
workbook.Sheet["Sheet1"].Range["A1:D10"].ClearRange(hasHeaders: true);
```

### RemoveDuplicates

```csharp
// Remove duplicates comparing all columns
workbook.Sheet["Sheet1"].RemoveDuplicates(
    hasHeaders: true,
    columnsMode: ColumnsCompare.AllColumns,
    columns: null
);

// Remove duplicates comparing specific columns
workbook.Sheet["Sheet1"].RemoveDuplicates(
    hasHeaders: true,
    columnsMode: ColumnsCompare.IndividualColumns,
    columns: new[] { "Name", "Email" }
);
```

---

## Filtering

### Filter — Filter a range

```csharp
// Basic filter (match specific values)
workbook.Sheet["Sheet1"].Filter(new FilterOptions
{
    ColumnName = "Status",
    Filter = new BasicFilter { Values = new List<string> { "Active", "Pending" } }
});

// Advanced filter
workbook.Sheet["Sheet1"].Filter(new FilterOptions
{
    ColumnName = "Amount",
    Filter = new AdvancedFilter
    {
        Operator = LogicalOperator.And,
        Condition1 = ExcelFilterOperator.GTE,
        Value1 = "100",
        Condition2 = ExcelFilterOperator.LT,
        Value2 = "1000"
    }
});

// Clear filters
workbook.Sheet["Sheet1"].Filter(new FilterOptions { ClearFilter = true });
```

#### `FilterOptions` Properties

| Property | Type | Default | Description |
|---|---|---|---|
| `ColumnName` | `string` | — | Column containing the values to filter |
| `ClearFilter` | `bool` | `false` | Clear existing filters |
| `Filter` | `IFilter` | `null` | A `BasicFilter` or `AdvancedFilter` instance |

#### `BasicFilter`

| Property | Type | Description |
|---|---|---|
| `Values` | `List<string>` | List of matching values |

#### `AdvancedFilter`

| Property | Type | Default | Description |
|---|---|---|---|
| `Operator` | `LogicalOperator` | `And` | `And` or `Or` between conditions |
| `Condition1` | `ExcelFilterOperator` | — | First condition operator |
| `Value1` | `string` | — | First condition value |
| `Condition2` | `ExcelFilterOperator` | — | Second condition operator |
| `Value2` | `string` | — | Second condition value |

**`ExcelFilterOperator` enum:** `NONE`, `LT` (<), `GT` (>), `LTE` (<=), `GTE` (>=), `EQ` (=), `NOTEQ` (!=), `EMPTY`, `NOTEMPTY`, `STARTSWITH`, `ENDSWITH`, `CONTAINS`, `NOTSTARTSWITH`, `NOTENDSWITH`, `NOTCONTAINS`

### FilterPivotTable

```csharp
workbook.Sheet["Sheet1"].PivotTable["PivotTable1"].FilterPivotTable(
    columnName: "Region",
    values: new[] { "North", "South" },
    clearFilter: false
);
```

---

## Sorting

```csharp
var descriptor = new SortXDescriptor();
descriptor.SortColumns.Add(new SortXColumnModel("Name", OrderType.Ascending));
descriptor.SortColumns.Add(new SortXColumnModel("Date", OrderType.Descending));

workbook.Sheet["Sheet1"].Sort(descriptor, hasHeaders: true);
```

---

## Find and Replace

### FindReplaceValue

```csharp
// Find a value
string address = workbook.Sheet["Sheet1"].FindReplaceValue(
    valueToFind: "John",
    operation: FindReplaceOptions.Find,
    replaceWith: null,
    lookIn: LookInOptions.Values,
    matchCase: false,
    matchEntireCellContents: false
);

// Replace all
workbook.Sheet["Sheet1"].FindReplaceValue(
    valueToFind: "old",
    operation: FindReplaceOptions.ReplaceAll,
    replaceWith: "new",
    lookIn: LookInOptions.Values,
    matchCase: true,
    matchEntireCellContents: false
);
```

**`FindReplaceOptions` enum:** `Find`, `Replace`, `ReplaceAll`
**`LookInOptions` enum:** `Values`, `Formulas`

### FindFirstLastDataRow

```csharp
// Simple — find first/last data rows in column A
(int first, int last) = workbook.Sheet["Sheet1"].FindFirstLastDataRow("A");

// With options
(int first, int last) = workbook.Sheet["Sheet1"].FindFirstLastDataRow(
    columnName: "A",
    hasHeaders: true,
    visibleRowsOnly: false,
    firstRowOffset: 0,
    lastRowOffset: 0,
    blankRowsToSkip: 1,
    configureLastRowAs: LastRowConfiguration.LastPopulatedRow
);
```

**`LastRowConfiguration` enum:** `LastPopulatedRow`, `FirstEmptyRow`

---

## Lookup Operations

### VLookup

```csharp
// With defaults (exact match = true)
object result = workbook.Sheet["Sheet1"].Range["A1:D10"].VLookup(label: "SearchValue");

// With options
object result = workbook.Sheet["Sheet1"].Range["A1:D10"].VLookup(
    label: "SearchValue",
    columnIndex: 3,
    exactMatch: true
);
```

### LookupRange

```csharp
object result = workbook.Sheet["Sheet1"].Range["A:A"].LookupRange(
    label: "SearchValue",
    resultRange: workbook.Sheet["Sheet1"].Range["C:C"]
);
```

### MatchFunction

```csharp
int position = workbook.Sheet["Sheet1"].Range["A1:A20"].MatchFunction(
    valueToMatch: "Target",
    matchFunctionType: MatchType.ExactlyEqual
);
```

**`MatchType` enum:** `LargestValueLessOrEqual` (1), `ExactlyEqual` (0), `SmallestValueGreaterOrEqual` (-1)

---

## Formatting

### FormatRange

```csharp
workbook.Sheet["Sheet1"].Range["A1:D10"].FormatRange(
    format: new CurrencyFormat { Currency = "$", DecimalPlaces = 2 },
    alignment: new AlignmentOptions
    {
        HorizontalAlignment = ExcelRangeHorizontalAlignment.xlHAlignCenter,
        VerticalAlignment = ExcelRangeVerticalAlignment.xlVAlignCenter,
        WrapText = true
    },
    font: new FontOptions
    {
        FontFamilyName = "Arial",
        Style = ExcelRangeFontStyle.Bold,
        Size = 12,
        Color = Color.Black,
        FillColor = Color.LightGray,
        UnderlineStyle = ExcelRangeUnderlineStyle.None
    }
);
```

#### Cell Format Types (`ICellFormat` implementations)

| Class | Description | Key Properties |
|---|---|---|
| `GeneralFormat` | General formatting | — |
| `TextFormat` | Text format (`@`) | — |
| `NumberFormat` | Numeric format | `DecimalPlaces`, `UseThousandSeparator` |
| `CurrencyFormat` | Currency format | `Currency` (symbol), `SetAtTheEnd`, `DecimalPlaces`, `UseThousandSeparator` |
| `PercentageFormat` | Percentage format | `DecimalPlaces`, `UseThousandSeparator` |
| `DateFormat` | Date format | `Type` (Short/Long) |
| `TimeFormat` | Time format | `IsAMPM`, `Type` (HoursMinutes/HoursMinutesSeconds) |
| `CustomFormat` | Custom Excel format string | `FormatAsString` |

#### `AlignmentOptions`

| Property | Type | Description |
|---|---|---|
| `HorizontalAlignment` | `ExcelRangeHorizontalAlignment` | `xlHAlignGeneral`, `xlHAlignLeft`, `xlHAlignCenter`, `xlHAlignRight`, `xlHAlignFill`, `xlHAlignJustify`, `xlHAlignCenterAcrossSelection`, `xlHAlignDistributed` |
| `VerticalAlignment` | `ExcelRangeVerticalAlignment` | `xlVAlignTop`, `xlVAlignCenter`, `xlVAlignBottom`, `xlVAlignJustify`, `xlVAlignDistributed` |
| `WrapText` | `bool` | Wrap text in cells |

#### `FontOptions`

| Property | Type | Description |
|---|---|---|
| `FontFamilyName` | `string` | Font name (e.g., "Arial") |
| `Style` | `ExcelRangeFontStyle` | `Regular`, `Italic`, `Bold`, `BoldItalic` |
| `Size` | `double` | Font size |
| `Color` | `Color` | Text color |
| `FillColor` | `Color` | Cell background color |
| `UnderlineStyle` | `ExcelRangeUnderlineStyle` | `None`, `Single`, `Double`, `SingleAccounting`, `DoubleAccounting` |

### Autofit

```csharp
// Autofit both columns and rows
workbook.Sheet["Sheet1"].Range["A1:D10"].Autofit();

// Autofit columns only
workbook.Sheet["Sheet1"].Range["A1:D10"].Autofit(columns: true, rows: false);
```

### Autofill

```csharp
// Autofill a range based on source data pattern
workbook.Sheet["Sheet1"].Range["A1:A2"].Autofill();
```

---

## Table Operations

### CreateTable

```csharp
// Create a table from a range
string tableName = workbook.Sheet["Sheet1"].Range["A1:D10"].CreateTable(
    hasHeaders: true,
    replaceExisting: false,
    tableName: "SalesData"
);
```

---

## Pivot Table Operations

### CreatePivotTable

```csharp
var descriptor = new PivotTableDescriptor
{
    LayoutRowType = PivotTableLayoutRowType.Tabular,
    ValuesMode = PivotTableValuesMode.Columns
};
descriptor.Rows.Add(new RowPivotTableFieldDescription { Name = "Category" });
descriptor.Columns.Add(new ColumnPivotTableFieldDescription { Name = "Region" });
descriptor.Values.Add(new ValuePivotTableFieldDescription
{
    Name = "Amount",
    Function = PivotTableFunction.Sum
});
descriptor.Filters.Add(new FilterPivotTableFieldDescription { Name = "Year" });

workbook.Sheet["Sheet1"].Range["A1:D100"].CreatePivotTable(
    destinationTableName: "SalesPivot",
    destination: workbook.Sheet["PivotSheet"],
    descriptor: descriptor
);
```

**`PivotTableLayoutRowType` enum:** `Compact`, `Tabular`, `Outline`
**`PivotTableFunction` enum:** `Sum`, `Count`, `Average`, `Max`, `Min`, `Product`, `CountNumbers`, `StdDev`, `StdDevp`, `Var`, `Varp`

### ChangePivotTableDataSource

```csharp
workbook.Sheet["Sheet1"].Range["A1:D200"].ChangePivotTableDataSource(
    workbook.Sheet["PivotSheet"].PivotTable["SalesPivot"]
);
```

### RefreshPivotTable

```csharp
workbook.Sheet["PivotSheet"].PivotTable["SalesPivot"].RefreshPivotTable(
    layoutRowType: PivotTableLayoutRowType.Tabular
);
```

### FilterPivotTable

```csharp
workbook.Sheet["PivotSheet"].PivotTable["SalesPivot"].FilterPivotTable(
    columnName: "Region",
    values: new[] { "North" },
    clearFilter: false
);
```

---

## Chart Operations

### InsertExcelChart

```csharp
IChartRef chart = workbook.Sheet["Sheet1"].Range["A1:C10"].InsertExcelChart(
    sheet: workbook.Sheet["Sheet1"],
    chartCategory: ExcelChartCategory.Column,
    chartType: ExcelChartType.xlColumnClustered,
    left: 300, top: 10, width: 400, height: 300
);
```

**`ExcelChartCategory` enum:** `Area`, `Bar`, `Column`, `Line`, `Pie`, `Scatter`

**`ExcelChartType` enum:**
- Area: `xlArea`, `xlAreaStacked`, `xlAreaStacked100`
- Bar: `xlBarClustered`, `xlBarStacked`, `xlBarStacked100`
- Column: `xlColumnClustered`, `xlColumnStacked`, `xlColumnStacked100`
- Line: `xlLine`, `xlLineMarkers`, `xlLineMarkersStacked`, `xlLineMarkersStacked100`, `xlLineStacked`, `xlLineStacked100`
- Pie: `xlPie`, `xlDoughnut`
- Scatter: `xlXYScatter`, `xlXYScatterLines`, `xlXYScatterLinesNoMarkers`, `xlXYScatterSmooth`, `xlXYScatterSmoothNoMarkers`

### GetChart

```csharp
// Copy chart to clipboard
workbook.Sheet["Sheet1"].Chart["Chart1"].GetChart();

// Save chart as image
workbook.Sheet["Sheet1"].Chart["Chart1"].GetChart(
    action: ExcelChartAction.SaveAsPicture,
    fileName: "chart.png",
    replaceFile: true
);
```

**`ExcelChartAction` enum:** `CopyToClipboard`, `SaveAsPicture`

---

## Text to Columns

```csharp
workbook.Sheet["Sheet1"].Range["A1:A10"].TextToColumns(
    destRange: workbook.Sheet["Sheet1"].Range["B1"],
    options: new TextToColumnsOptions
    {
        ParsingType = TextToColumnsParsingType.Delimited,
        ColumnsDelimiters = TextToColumnsDelimiters.Comma | TextToColumnsDelimiters.Semicolon,
        ConsecutiveOperatorsAsOne = true,
        TextQualifier = TextToColumnsTextQualifier.DoubleQuote
    }
);
```

#### `TextToColumnsOptions` Properties

| Property | Type | Default | Description |
|---|---|---|---|
| `ParsingType` | `TextToColumnsParsingType` | `Delimited` | `Delimited` or `FixedWidth` |
| `NumberOfCharactersPerColumn` | `int` | — | Width for `FixedWidth` mode |
| `ColumnsDelimiters` | `TextToColumnsDelimiters` | `Tab \| Semicolon \| Comma \| Space` | Flags: `None`, `Tab`, `Semicolon`, `Comma`, `Space`, `Other` |
| `SplitByLineBreak` | `bool` | `false` | Split by line break |
| `OtherSeparator` | `char?` | — | Custom separator (when `Other` flag is set) |
| `ConsecutiveOperatorsAsOne` | `bool` | `true` | Treat consecutive delimiters as one |
| `TextQualifier` | `TextToColumnsTextQualifier` | `None` | `None`, `DoubleQuote`, `SingleQuote` |

---

## Macros and VBA

### ExecuteMacro

```csharp
object result = workbook.ExecuteMacro(
    macroName: "MyMacro",
    macroArguments: new List<object> { "arg1", 42 }
);
```

### InvokeVBA

```csharp
object result = workbook.InvokeVBA(
    codeFilePath: @"C:\macros\script.vba",
    entryMethodname: "ProcessData",
    arguments: new List<object> { "input" }
);
```

---

## Save and Export

### SaveExcelFile

```csharp
workbook.SaveExcelFile();
```

### SaveExcelFileAs

```csharp
workbook.SaveExcelFileAs("output.xlsx", replaceExisting: true, saveAsType: ExcelSaveAsType.OpenXmlWorkbook);
```

**`ExcelSaveAsType` enum:** `OpenXmlWorkbook` (.xlsx), `BinaryWorkbook` (.xlsb), `MacroEnabledWorkbook` (.xlsm), `OldWorkbook` (.xls)

### SaveAsPdf

```csharp
// Simple
workbook.SaveAsPdf("output.pdf");

// With options
workbook.SaveAsPdf(
    filePath: "output.pdf",
    replaceExisting: true,
    startPage: 1,
    endPage: 5,
    saveQuality: PdfSaveQuality.StandardQuality
);
```

**`PdfSaveQuality` enum:** `StandardQuality`, `MinimumQuality`

### ExportExcelToCSV

```csharp
workbook.Sheet["Sheet1"].ExportExcelToSCV("output.csv");
workbook.Sheet["Sheet1"].Range["A1:D10"].ExportExcelToSCV("output.csv");
```

---

## Sensitivity Labels

### AddSensitivityLabel

```csharp
workbook.AddSensitivityLabel(labelObject);
```

### GetSensitivityLabel

```csharp
IExcelLabelObject label = workbook.GetSensitivityLabel();
```

---

## Other Operations

### SelectRange

```csharp
workbook.Sheet["Sheet1"].Range["A1:D10"].SelectRange();
```

### RefreshDataConnections

```csharp
workbook.RefreshDataConnections();
```
