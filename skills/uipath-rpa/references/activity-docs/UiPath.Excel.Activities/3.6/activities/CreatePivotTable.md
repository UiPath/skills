# Create Pivot Table Workbook

`UiPath.Excel.Activities.CreatePivotTable`

Creates a pivot table in a workbook from a specified data source (sheet range or table).

**Package:** `UiPath.Excel.Activities`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `WorkbookPath` | File (local path) | InArgument | `string` | | | The full local path of the workbook. Alternative to `WorkbookPathResource` — use one or the other |
| `WorkbookPathResource` | File | InArgument | `IResource` | | | A resource reference (e.g. a local file, remote file, or abstract resource). Alternative to `WorkbookPath` — use one or the other |
| `UseTableSource` | Use table source | Property | `bool` | | `False` | When True, uses a named table as source instead of sheet/range |
| `SourceSheet` | Source sheet | InArgument | `string` | | | The sheet containing the source data. Visible when `UseTableSource` is False |
| `SourceRange` | Source range | InArgument | `string` | | | The range of source data. Visible when `UseTableSource` is False |
| `SourceTable` | Source table name | InArgument | `string` | | | Name of the source table for the pivot. Visible when `UseTableSource` is True |
| `SheetName` | Pivot sheet name | InArgument | `string` | Yes | | The sheet where the pivot table will be placed |
| `PlacementCell` | Pivot placement cell | InArgument | `string` | | | Cell specifying where the pivot table will be created |
| `PivotTableName` | Pivot table name | InArgument | `string` | Yes | | Name of the new pivot table |
| `PivotTableFields` | Pivot table fields | Property | `List<InArgument<PivotTableField>>` | | | The pivot table field definitions (static list) |
| `PivotTableFieldsVariable` | Pivot table fields variable | InArgument | `IEnumerable<PivotTableField>` | | | The pivot table field definitions (variable/expression) |
| `LayoutRowType` | Layout | InArgument | `PivotTableLayoutRowType` | | | The layout style for pivot table rows |
| `ValuesMode` | Values added as | InArgument | `PivotTableValuesMode` | | | How values are displayed in the pivot table |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Password` | Password | `InArgument<string>` | | The password of the workbook, if necessary |
| `Workbook` | Workbook | `InArgument<Workbook>` | | Existing workbook object to use instead of a file path |

## Valid Configurations

This activity supports two data source modes controlled by `UseTableSource`:

**Mode A — Sheet Range** (default): Set `SourceSheet` and `SourceRange`. `SourceTable` is hidden.
**Mode B — Named Table**: Set `UseTableSource` to True and provide `SourceTable`. `SourceSheet` and `SourceRange` are hidden.

`PivotTableFields` and `PivotTableFieldsVariable` are alternative input modes (static list vs. expression).

## XAML Example

```xml
<excel:CreatePivotTable
  DisplayName="Create Pivot Table Workbook"
  WorkbookPath="[&quot;report.xlsx&quot;]"
  SourceSheet="[&quot;Data&quot;]"
  SourceRange="[&quot;A1:E100&quot;]"
  SheetName="[&quot;PivotSheet&quot;]"
  PlacementCell="[&quot;A1&quot;]"
  PivotTableName="[&quot;SalesPivot&quot;]" />
```

## Notes

- Uses the file-based workbook engine (not Excel Interop). Works cross-platform.
- `WorkbookPath` and `WorkbookPathResource` are mutually exclusive — set one or the other.
