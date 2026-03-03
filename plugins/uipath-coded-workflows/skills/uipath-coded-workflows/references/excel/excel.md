# Excel Activities API Reference

Reference for the `excel` service from `UiPath.Excel.Activities` package.

**Required package:** `"UiPath.Excel.Activities": "[3.3.1]"`

**Auto-imported namespaces:** `System`, `System.Collections.Generic`, `System.Data`, `UiPath.Excel`, `UiPath.Excel.Activities`, `UiPath.Excel.Activities.API`, `UiPath.Excel.Activities.API.Models`

**Service accessor:** `excel` (type `IExcelService`)

---

## Two API Layers

The Excel API has two layers:

1. **Windows (Interop) API** — uses `excel.UseExcelFile(...)` returning `IWorkbookQuickHandle`. This is the modern, full-featured API that opens Excel via COM interop. Supports sheets, ranges, cells, tables, charts, pivot tables, filtering, sorting, macros, etc. See [windows-api.md](windows-api.md).

2. **Portable API** — uses `excel.UseWorkBook(...)` returning `IWorkHandle`. This is a lightweight API that works cross-platform using a non-interop engine. Supports basic read/write/append operations and CSV operations. See [portable-api.md](portable-api.md).

**Always prefer the Windows API (`UseExcelFile`) unless cross-platform compatibility is required.**

For full coded workflow examples, see [examples.md](examples.md).

---

## Key Enum Reference Summary

| Enum | Values |
|---|---|
| `ReadFormattingOptions` | `Default`, `RawValue`, `DisplayValue` |
| `ResizeWindowOptions` | `None`, `Minimize`, `Maximize` |
| `EmptyRowBehavior` | `Stop`, `StopAfterThreeConsecutiveEmptyRows`, `Skip`, `Process` |
| `CopyPasteRangeOptions` | `All`, `Values`, `Formulas`, `Formats` |
| `FindReplaceOptions` | `Find`, `Replace`, `ReplaceAll` |
| `LookInOptions` | `Values`, `Formulas` |
| `InsertRowPosition` | `Start`, `End`, `Specific` |
| `DeleteRowsOption` | `Specific`, `Visible`, `Hidden`, `Duplicates` |
| `ColumnRelativePosition` | `Before`, `After` |
| `ColumnsCompare` | `IndividualColumns`, `AllColumns` |
| `MatchType` | `LargestValueLessOrEqual`, `ExactlyEqual`, `SmallestValueGreaterOrEqual` |
| `LastRowConfiguration` | `LastPopulatedRow`, `FirstEmptyRow` |
| `LogicalOperator` | `And`, `Or` |
| `PdfSaveQuality` | `StandardQuality`, `MinimumQuality` |
| `ExcelSaveAsType` | `OpenXmlWorkbook`, `BinaryWorkbook`, `MacroEnabledWorkbook`, `OldWorkbook` |
| `ExcelLabelOperation` | `None`, `Add`, `Clear` |
| `DelimitatorOptions` | `Comma`, `Semicolon`, `Pipe`, `Caret`, `Tab` |
| `PivotTableLayoutRowType` | `Compact`, `Tabular`, `Outline` |
| `ExcelChartAction` | `CopyToClipboard`, `SaveAsPicture` |
