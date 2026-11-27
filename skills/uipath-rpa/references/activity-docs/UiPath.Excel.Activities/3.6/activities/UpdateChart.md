# Update Chart Workbook

`UiPath.Excel.Activities.UpdateChart`

Updates an existing chart in a workbook by applying modifications such as changing the data range, title, axis labels, or legend visibility.

**Package:** `UiPath.Excel.Activities`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `WorkbookPath` | File (local path) | InArgument | `string` | | | The full local path of the workbook. Alternative to `WorkbookPathResource` — use one or the other |
| `WorkbookPathResource` | File | InArgument | `IResource` | | | A resource reference (e.g. a local file, remote file, or abstract resource). Alternative to `WorkbookPath` — use one or the other |
| `ChartName` | Chart | InArgument | `string` | Yes | | The name of the chart to update |
| `SheetName` | SheetName | InArgument | `string` | | | The sheet containing the chart |
| `Modifications` | Chart modifications | Property | `List<InArgument<IChartModification>>` | | | Chart modifications to apply (static list of modification activities) |
| `ModificationsVariable` | Chart modifications variable | InArgument | `IEnumerable<IChartModification>` | | | Chart modifications to apply (variable/expression) |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Password` | Password | `InArgument<string>` | | The password of the workbook, if necessary |
| `Workbook` | Workbook | `InArgument<Workbook>` | | Existing workbook object to use instead of a file path |

## XAML Example

```xml
<excel:UpdateChart
  DisplayName="Update Chart Workbook"
  WorkbookPath="[&quot;report.xlsx&quot;]"
  SheetName="[&quot;Charts&quot;]"
  ChartName="[&quot;SalesChart&quot;]" />
```

## Notes

- Uses the file-based workbook engine (not Excel Interop). Works cross-platform.
- `WorkbookPath` and `WorkbookPathResource` are mutually exclusive — set one or the other.
- `Modifications` and `ModificationsVariable` are alternative input modes (static list vs. expression).
- Available chart modification types include: ChangeDataRange, ModifyChartTitle, ShowHideDataLabels, ShowHideLegend, UpdateAxisBounds, UpdateAxisTitle.
