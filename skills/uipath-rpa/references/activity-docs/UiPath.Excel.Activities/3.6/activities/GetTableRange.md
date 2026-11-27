# Get Table Range Workbook

`UiPath.Excel.Activities.GetTableRange`

Extracts the range of an Excel table from a specified spreadsheet.

**Package:** `UiPath.Excel.Activities`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `WorkbookPath` | File (local path) | InArgument | `string` | | | The full local path of the workbook. Alternative to `WorkbookPathResource` — use one or the other |
| `WorkbookPathResource` | File | InArgument | `IResource` | | | A resource reference (e.g. a local file, remote file, or abstract resource). Alternative to `WorkbookPath` — use one or the other |
| `SheetName` | SheetName | InArgument | `string` | Yes | | The name of the sheet from the workbook |
| `TableName` | TableName | InArgument | `string` | Yes | | The name of the table |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `IsPivot` | IsPivot | `bool` | | Indicates whether the table is a pivot table |
| `Password` | Password | `InArgument<string>` | | The password of the workbook, if necessary |
| `Workbook` | Workbook | `InArgument<Workbook>` | | Existing workbook object to use instead of a file path |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Range` | Range | `string` | The range of the specified table (e.g. "A1:D10") |

## XAML Example

```xml
<excel:GetTableRange
  DisplayName="Get Table Range Workbook"
  WorkbookPath="[&quot;report.xlsx&quot;]"
  SheetName="[&quot;Sheet1&quot;]"
  TableName="[&quot;SalesTable&quot;]"
  Range="[tableRange]" />
```

## Notes

- Uses the file-based workbook engine (not Excel Interop). Works cross-platform.
- `WorkbookPath` and `WorkbookPathResource` are mutually exclusive — set one or the other.
- Set `IsPivot` to `True` when the target table is a pivot table.
