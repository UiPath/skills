# Read Range Workbook

`UiPath.Excel.Activities.ReadRange`

Reads the value of a range from a spreadsheet as a DataTable. If Range isn't specified, the whole spreadsheet is read. If range is specified as a cell, the whole spreadsheet starting from that cell is read.

**Package:** `UiPath.Excel.Activities`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `WorkbookPath` | File (local path) | InArgument | `string` | | | The full local path of the workbook. Alternative to `WorkbookPathResource` — use one or the other |
| `WorkbookPathResource` | File | InArgument | `IResource` | | | A resource reference (e.g. a local file, remote file, or abstract resource). Alternative to `WorkbookPath` — use one or the other |
| `SheetName` | SheetName | InArgument | `string` | Yes | `"Sheet1"` | The name of the sheet from the workbook |
| `Range` | Range | InArgument | `string` | | `"A1:A2"` | The range to read in Excel format (e.g. "A1:B10"). If a single cell is specified, reads from that cell to the end of the sheet |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `AddHeaders` | Add headers | `bool` | `True` | Specifies if the first row of the range should be used as column names in the output DataTable |
| `PreserveFormat` | Use display format | `bool` | `False` | Preserves the cell formatting when reading values |
| `Password` | Password | `InArgument<string>` | | The password of the workbook, if necessary |
| `Workbook` | Workbook | `InArgument<Workbook>` | | Existing workbook object to use instead of a file path |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `DataTable` | DataTable | `DataTable` | The data read from the specified range as a DataTable |

## XAML Example

```xml
<excel:ReadRange
  DisplayName="Read Range Workbook"
  WorkbookPath="[&quot;report.xlsx&quot;]"
  SheetName="[&quot;Sheet1&quot;]"
  Range="[&quot;A1:D10&quot;]"
  AddHeaders="True"
  DataTable="[outputData]" />
```

## Notes

- Uses the file-based workbook engine (not Excel Interop). Works cross-platform.
- `WorkbookPath` and `WorkbookPathResource` are mutually exclusive — set one or the other.
