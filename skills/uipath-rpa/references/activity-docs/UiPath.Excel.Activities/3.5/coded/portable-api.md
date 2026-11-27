# Excel — Portable API

Lightweight cross-platform API using `excel.UseWorkBook(...)` returning `IWorkHandle`. Works without COM interop. For general info see [excel.md](excel.md).

---

## Opening Workbooks

### `excel.UseWorkBook(string path)`

```csharp
using var wb = excel.UseWorkBook("data.xlsx");
```

### `excel.UseWorkBook(WorkbookOptions options)`

```csharp
using var wb = excel.UseWorkBook(new WorkbookOptions
{
    Path = "data.xlsx",
    Password = "secret",
    CreateNew = true
});
```

#### `WorkbookOptions` Properties

| Property | Type | Default | Description |
|---|---|---|---|
| `Path` | `string` | — | Path of the workbook |
| `Password` | `string` | `null` | Password if needed |
| `CreateNew` | `bool` | `true` | Create the workbook if it does not exist |

---

## Reading Data

### ReadRange

```csharp
DataTable dt = wb.ReadRange("Sheet1", "A1:D10", addHeaders: true, preserveFormat: false);
```

### ReadCell

```csharp
object value = wb.ReadCell("Sheet1", "B2", preserveFormat: true);
```

### ReadCellFormula

```csharp
string formula = wb.ReadCellFormula("Sheet1", "B2");
```

### ReadColumn

```csharp
IEnumerable<object> colValues = wb.ReadColumn("Sheet1", "A1", preserveFormat: false);
```

### ReadRow

```csharp
IEnumerable<object> rowValues = wb.ReadRow("Sheet1", "A1", preserveFormat: false);
```

### GetCellColor

```csharp
Color cellColor = wb.GetCellColor("Sheet1", "A1");
```

---

## Writing Data

### WriteRange

```csharp
wb.WriteRange("Sheet1", "A1", dataTable, addHeaders: true);
```

### WriteCell

```csharp
wb.WriteCell("Sheet1", "A1", "Hello");
```

### AppendRange

```csharp
wb.AppendRange("Sheet1", dataTable);
```

### SetRangeColor

```csharp
wb.SetRangeColor("Sheet1", "A1:C5", Color.Yellow);
```

---

## Table Operations

### GetTableRange

```csharp
string range = wb.GetTableRange("Sheet1", "Table1", isPivot: false);
```

### CreatePivotTable

```csharp
wb.CreatePivotTable("TargetSheet", pivotTableInfo);
```

---

## Extension Methods Summary

All portable API extension methods are called on `IWorkHandle` and require a `sheetName` parameter:

| Method | Signature | Returns |
|---|---|---|
| `ReadRange` | `(sheetName, range, addHeaders, preserveFormat)` | `DataTable` |
| `WriteRange` | `(sheetName, startingCell, table, addHeaders)` | — |
| `AppendRange` | `(sheetName, table)` | — |
| `ReadCell` | `(sheetName, cell, preserveFormat)` | `object` |
| `ReadCellFormula` | `(sheetName, cell)` | `string` |
| `ReadColumn` | `(sheetName, startingCell, preserveFormat)` | `IEnumerable<object>` |
| `ReadRow` | `(sheetName, startingCell, preserveFormat)` | `IEnumerable<object>` |
| `WriteCell` | `(sheetName, cell, text)` | — |
| `GetTableRange` | `(sheetName, tableName, isPivot)` | `string` |
| `GetCellColor` | `(sheetName, cell)` | `Color` |
| `SetRangeColor` | `(sheetName, range, color)` | — |
| `CreatePivotTable` | `(targetSheet, pivotTableInfo)` | — |

---

## CSV Operations (Static Methods)

These are static methods on `ExcelOperations` — accessible without a workbook handle.

### ReadCsvFile

```csharp
DataTable dt = ExcelOperations.ReadCsvFile(
    filePath: "data.csv",
    delimiter: DelimitatorOptions.Comma,
    includeColumnNames: true,
    encodingStr: "utf-8",
    ignoreQuotes: false
);
```

### WriteCsvFile

```csharp
ExcelOperations.WriteCsvFile(
    filePath: "output.csv",
    data: dataTable,
    delimiter: DelimitatorOptions.Comma,
    addHeaders: true,
    encodingStr: "utf-8",
    shouldQuote: true
);
```

### AppendCsvFile

```csharp
ExcelOperations.AppendCsvFile(
    filePath: "data.csv",
    data: dataTable,
    delimiter: DelimitatorOptions.Comma,
    encodingStr: "utf-8"
);
```

**`DelimitatorOptions` enum:** `Comma`, `Semicolon`, `Pipe`, `Caret`, `Tab`
