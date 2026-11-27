# Append Range Workbook

`UiPath.Excel.Activities.AppendRange`

Appends the data from a DataTable to a spreadsheet. If the sheet does not exist, a new one is created with the SheetName value. Changes are immediately saved.

**Package:** `UiPath.Excel.Activities`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `WorkbookPath` | File (local path) | InArgument | `string` | | | The full local path of the workbook. Alternative to `WorkbookPathResource` — use one or the other |
| `WorkbookPathResource` | File | InArgument | `IResource` | | | A resource reference (e.g. a local file, remote file, or abstract resource). Alternative to `WorkbookPath` — use one or the other |
| `SheetName` | SheetName | InArgument | `string` | Yes | | The name of the sheet from the workbook |
| `DataTable` | DataTable | InArgument | `DataTable` | Yes | | The DataTable object containing the input data to append |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Password` | Password | `InArgument<string>` | | The password of the workbook, if necessary |
| `Workbook` | Workbook | `InArgument<Workbook>` | | Existing workbook object to use instead of a file path |

## XAML Example

```xml
<excel:AppendRange
  DisplayName="Append Range Workbook"
  WorkbookPath="[&quot;report.xlsx&quot;]"
  SheetName="[&quot;Sheet1&quot;]"
  DataTable="[dataToAppend]" />
```

## Notes

- Uses the file-based workbook engine (not Excel Interop). Works cross-platform.
- `WorkbookPath` and `WorkbookPathResource` are mutually exclusive — set one or the other.
- Data is appended after the last row with data in the sheet.
