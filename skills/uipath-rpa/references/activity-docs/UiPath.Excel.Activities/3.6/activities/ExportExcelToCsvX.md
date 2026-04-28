# Export to CSV

`UiPath.Excel.Activities.Business.ExportExcelToCsvX`

Exports the specified range, table, pivotTable or sheet to a CSV file.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FilePath` | Write to what file | InArgument | `string` | Yes | | The file path where the CSV file will be written. |
| `TargetRange` | Write from | InArgument | `IReadRangeRef` | Yes | | The range, table, pivot table, or sheet to export. |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:ExportExcelToCsvX
    FilePath="[&quot;C:\Output\data.csv&quot;]"
    TargetRange="[MyRange]"
    DisplayName="Export to CSV" />
</excel:ExcelApplicationCard>
```

## Notes
- The file path must point to a valid location with an existing parent folder; otherwise, an exception is thrown.
- For sheets, the entire sheet is exported as CSV. For ranges, tables, and pivot tables, only the specified data is exported.
- The target range must be valid; otherwise, an `ArgumentNullException` is thrown.
