# Get Cell Color Workbook

`UiPath.Excel.Activities.GetCellColor`

Gets the background color of a specified cell in a spreadsheet.

**Package:** `UiPath.Excel.Activities`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `WorkbookPath` | File (local path) | InArgument | `string` | | | The full local path of the workbook. Alternative to `WorkbookPathResource` — use one or the other |
| `WorkbookPathResource` | File | InArgument | `IResource` | | | A resource reference (e.g. a local file, remote file, or abstract resource). Alternative to `WorkbookPath` — use one or the other |
| `SheetName` | SheetName | InArgument | `string` | Yes | | The name of the sheet from the workbook |
| `Cell` | Cell | InArgument | `string` | Yes | | The cell to get the color from (e.g. "A1") |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Password` | Password | `InArgument<string>` | | The password of the workbook, if necessary |
| `Workbook` | Workbook | `InArgument<Workbook>` | | Existing workbook object to use instead of a file path |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Color` | Color | `System.Drawing.Color` | The background color of the specified cell |

## XAML Example

```xml
<excel:GetCellColor
  DisplayName="Get Cell Color Workbook"
  WorkbookPath="[&quot;report.xlsx&quot;]"
  SheetName="[&quot;Sheet1&quot;]"
  Cell="[&quot;A1&quot;]"
  Color="[cellColor]" />
```

## Notes

- Uses the file-based workbook engine (not Excel Interop). Works cross-platform.
- `WorkbookPath` and `WorkbookPathResource` are mutually exclusive — set one or the other.
