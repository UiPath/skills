# Get Sheets Workbook

`UiPath.Excel.Activities.GetSheets`

Gets the list of sheet names from a workbook.

**Package:** `UiPath.Excel.Activities`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `WorkbookPath` | File (local path) | InArgument | `string` | | | The full local path of the workbook. Alternative to `WorkbookPathResource` — use one or the other |
| `WorkbookPathResource` | File | InArgument | `IResource` | | | A resource reference (e.g. a local file, remote file, or abstract resource). Alternative to `WorkbookPath` — use one or the other |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `OnlyVisibleSheets` | Visible sheets only | `bool` | `False` | When True, only returns visible sheets (excludes hidden and very hidden sheets) |
| `Password` | Password | `InArgument<string>` | | The password of the workbook, if necessary |
| `Workbook` | Workbook | `InArgument<Workbook>` | | Existing workbook object to use instead of a file path |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Result` | Sheets | `IEnumerable<string>` | The list of sheet names in the workbook |

## XAML Example

```xml
<excel:GetSheets
  DisplayName="Get Sheets Workbook"
  WorkbookPath="[&quot;report.xlsx&quot;]"
  Result="[sheetNames]" />
```

## Notes

- Uses the file-based workbook engine (not Excel Interop). Works cross-platform.
- `WorkbookPath` and `WorkbookPathResource` are mutually exclusive — set one or the other.
- `SheetName` is not used by this activity (hidden in the designer).
