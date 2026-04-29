# Read Cell Formula Workbook

`UiPath.Excel.Activities.ReadCellFormula`

Reads the formula of a cell from a spreadsheet as a string.

**Package:** `UiPath.Excel.Activities`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `WorkbookPath` | File (local path) | InArgument | `string` | | | The full local path of the workbook. Alternative to `WorkbookPathResource` — use one or the other |
| `WorkbookPathResource` | File | InArgument | `IResource` | | | A resource reference (e.g. a local file, remote file, or abstract resource). Alternative to `WorkbookPath` — use one or the other |
| `SheetName` | SheetName | InArgument | `string` | Yes | | The name of the sheet from the workbook |
| `Cell` | Cell | InArgument | `string` | Yes | | The cell to read the formula from (e.g. "A1") |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Password` | Password | `InArgument<string>` | | The password of the workbook, if necessary |
| `Workbook` | Workbook | `InArgument<Workbook>` | | Existing workbook object to use instead of a file path |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Result` | Result | `string` | The formula from the specified cell as a string (e.g. "=SUM(A1:A10)") |

## XAML Example

```xml
<excel:ReadCellFormula
  DisplayName="Read Cell Formula Workbook"
  WorkbookPath="[&quot;report.xlsx&quot;]"
  SheetName="[&quot;Sheet1&quot;]"
  Cell="[&quot;B5&quot;]"
  Result="[formula]" />
```

## Notes

- Uses the file-based workbook engine (not Excel Interop). Works cross-platform.
- `WorkbookPath` and `WorkbookPathResource` are mutually exclusive — set one or the other.
- Returns the formula string (e.g. "=SUM(A1:A10)"), not the computed value.
