# Read Column Workbook

`UiPath.Excel.Activities.ReadColumn`

Reads the values from a column beginning from the cell specified in the StartingCell field, and stores them in an IEnumerable<object> variable.

**Package:** `UiPath.Excel.Activities`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `WorkbookPath` | File (local path) | InArgument | `string` | | | The full local path of the workbook. Alternative to `WorkbookPathResource` — use one or the other |
| `WorkbookPathResource` | File | InArgument | `IResource` | | | A resource reference (e.g. a local file, remote file, or abstract resource). Alternative to `WorkbookPath` — use one or the other |
| `SheetName` | SheetName | InArgument | `string` | Yes | | The name of the sheet from the workbook |
| `StartingCell` | StartingCell | InArgument | `string` | Yes | | The cell from which to start reading the column (e.g. "A1") |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `PreserveFormat` | Use display format | `bool` | | Preserves the cell formatting when reading values |
| `Password` | Password | `InArgument<string>` | | The password of the workbook, if necessary |
| `Workbook` | Workbook | `InArgument<Workbook>` | | Existing workbook object to use instead of a file path |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Result` | Result | `IEnumerable<object>` | The values read from the column |

## XAML Example

```xml
<excel:ReadColumn
  DisplayName="Read Column Workbook"
  WorkbookPath="[&quot;report.xlsx&quot;]"
  SheetName="[&quot;Sheet1&quot;]"
  StartingCell="[&quot;A1&quot;]"
  Result="[columnValues]" />
```

## Notes

- Uses the file-based workbook engine (not Excel Interop). Works cross-platform.
- `WorkbookPath` and `WorkbookPathResource` are mutually exclusive — set one or the other.
- Reads from the starting cell downward until empty cells are encountered.
