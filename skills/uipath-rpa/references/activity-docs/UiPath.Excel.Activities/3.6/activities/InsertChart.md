# Insert Chart Workbook

`UiPath.Excel.Activities.InsertChart`

Inserts a chart into a workbook based on data from a sheet range or named table.

**Package:** `UiPath.Excel.Activities`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `WorkbookPath` | File (local path) | InArgument | `string` | | | The full local path of the workbook. Alternative to `WorkbookPathResource` — use one or the other |
| `WorkbookPathResource` | File | InArgument | `IResource` | | | A resource reference (e.g. a local file, remote file, or abstract resource). Alternative to `WorkbookPath` — use one or the other |
| `UseTableSource` | Use table source | Property | `bool` | | `False` | When True, uses a named table as the data source instead of sheet/range |
| `SourceSheet` | Source sheet | InArgument | `string` | | | The sheet containing the chart data. Visible when `UseTableSource` is False |
| `SourceRange` | Source range | InArgument | `string` | | | The range of source data. Visible when `UseTableSource` is False |
| `SourceTable` | Source table name | InArgument | `string` | | | Name of the source table. Visible when `UseTableSource` is True |
| `SheetName` | Insert into sheet | InArgument | `string` | Yes | `"Sheet1"` | The sheet where the chart will be placed |
| `ChartCategory` | Chart category | Property | `ExcelChartCategory` | Yes | `Column` | The chart category (e.g. Column, Bar, Line, Pie) |
| `ChartType` | Chart type | Property | `ExcelChartType` | Yes | `xlColumnClustered` | The specific chart type within the selected category |
| `ChartHeight` | Chart height | InArgument | `int` | Yes | `211` | The height of the chart in pixels |
| `ChartWidth` | Chart width | InArgument | `int` | Yes | `355` | The width of the chart in pixels |
| `Left` | Chart left | InArgument | `int` | Yes | `60` | The left position of the chart in pixels |
| `Top` | Chart top | InArgument | `int` | Yes | `20` | The top position of the chart in pixels |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Password` | Password | `InArgument<string>` | | The password of the workbook, if necessary |
| `Workbook` | Workbook | `InArgument<Workbook>` | | Existing workbook object to use instead of a file path |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `ChartName` | Save chart to | `string` | The name of the inserted chart, for use with Update Chart |

## Valid Configurations

This activity supports two data source modes controlled by `UseTableSource`:

**Mode A — Sheet Range** (default): Set `SourceSheet` and `SourceRange`. `SourceTable` is hidden.
**Mode B — Named Table**: Set `UseTableSource` to True and provide `SourceTable`. `SourceSheet` and `SourceRange` are hidden.

### Conditional Properties

- **`ChartType`** — The available chart types change based on the selected `ChartCategory`. When `ChartCategory` changes, the `ChartType` dropdown is filtered to show only types in that category.

## XAML Example

```xml
<excel:InsertChart
  DisplayName="Insert Chart Workbook"
  WorkbookPath="[&quot;report.xlsx&quot;]"
  SourceSheet="[&quot;Data&quot;]"
  SourceRange="[&quot;A1:C10&quot;]"
  SheetName="[&quot;Charts&quot;]"
  ChartCategory="Column"
  ChartType="xlColumnClustered"
  ChartHeight="[400]"
  ChartWidth="[600]"
  Left="[10]"
  Top="[10]"
  ChartName="[insertedChartName]" />
```

## Notes

- Uses the file-based workbook engine (not Excel Interop). Works cross-platform.
- `WorkbookPath` and `WorkbookPathResource` are mutually exclusive — set one or the other.
