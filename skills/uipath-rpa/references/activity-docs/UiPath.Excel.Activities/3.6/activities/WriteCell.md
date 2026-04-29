# Write Cell Workbook

`UiPath.Excel.Activities.WriteCell`

Writes a text value into a cell in a spreadsheet. If the sheet does not exist, a new one is created with the SheetName value. If a value exists, it is overwritten. Changes are immediately saved.

**Package:** `UiPath.Excel.Activities`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `WorkbookPath` | File (local path) | InArgument | `string` | | | The full local path of the workbook. Alternative to `WorkbookPathResource` — use one or the other |
| `WorkbookPathResource` | File | InArgument | `IResource` | | | A resource reference (e.g. a local file, remote file, or abstract resource). Alternative to `WorkbookPath` — use one or the other |
| `SheetName` | SheetName | InArgument | `string` | Yes | `"Sheet1"` | The name of the destination sheet. Category: Destination |
| `Cell` | Cell | InArgument | `string` | Yes | `"A1"` | The destination cell (e.g. "A1"). Category: Destination |
| `Text` | Text | InArgument | `string` | Yes | | The value to write into the cell |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Password` | Password | `InArgument<string>` | | The password of the workbook, if necessary |
| `Workbook` | Workbook | `InArgument<Workbook>` | | Existing workbook object to use instead of a file path |

## XAML Example

```xml
<excel:WriteCell
  DisplayName="Write Cell Workbook"
  WorkbookPath="[&quot;report.xlsx&quot;]"
  SheetName="[&quot;Sheet1&quot;]"
  Cell="[&quot;A1&quot;]"
  Text="[&quot;Hello World&quot;]" />
```

## Notes

- Uses the file-based workbook engine (not Excel Interop). Works cross-platform.
- `WorkbookPath` and `WorkbookPathResource` are mutually exclusive — set one or the other.
