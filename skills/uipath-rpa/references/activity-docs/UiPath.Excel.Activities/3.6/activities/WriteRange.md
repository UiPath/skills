# Write Range Workbook

`UiPath.Excel.Activities.WriteRange`

Writes the data from a DataTable to a spreadsheet starting from StartingCell. If StartingCell isn't specified, writing begins at A1. If the sheet does not exist, a new one is created with the SheetName value. All cells within the DataTable range are overwritten. Changes are immediately saved.

**Package:** `UiPath.Excel.Activities`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `WorkbookPath` | File (local path) | InArgument | `string` | | | The full local path of the workbook. Alternative to `WorkbookPathResource` — use one or the other |
| `WorkbookPathResource` | File | InArgument | `IResource` | | | A resource reference (e.g. a local file, remote file, or abstract resource). Alternative to `WorkbookPath` — use one or the other |
| `SheetName` | SheetName | InArgument | `string` | Yes | `"Sheet1"` | The name of the destination sheet. Category: Destination |
| `StartingCell` | StartingCell | InArgument | `string` | | `"A1"` | The starting cell (in range format) from which the input will be written. Category: Destination |
| `DataTable` | DataTable | InArgument | `DataTable` | Yes | | The DataTable to write to the spreadsheet |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `AddHeaders` | Add headers | `bool` | `True` | Specifies if the first row written should be the column names from the DataTable input |
| `Password` | Password | `InArgument<string>` | | The password of the workbook, if necessary |
| `Workbook` | Workbook | `InArgument<Workbook>` | | Existing workbook object to use instead of a file path |

## XAML Example

```xml
<excel:WriteRange
  DisplayName="Write Range Workbook"
  WorkbookPath="[&quot;report.xlsx&quot;]"
  SheetName="[&quot;Sheet1&quot;]"
  StartingCell="[&quot;A1&quot;]"
  DataTable="[dataToWrite]"
  AddHeaders="True" />
```

## Notes

- Uses the file-based workbook engine (not Excel Interop). Works cross-platform.
- `WorkbookPath` and `WorkbookPathResource` are mutually exclusive — set one or the other.
- If the target sheet does not exist, it is created automatically.
