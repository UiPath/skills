# Set Range Color Workbook

`UiPath.Excel.Activities.SetRangeColor`

Sets the background color of a specified range of cells in a spreadsheet.

**Package:** `UiPath.Excel.Activities`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `WorkbookPath` | File (local path) | InArgument | `string` | | | The full local path of the workbook. Alternative to `WorkbookPathResource` — use one or the other |
| `WorkbookPathResource` | File | InArgument | `IResource` | | | A resource reference (e.g. a local file, remote file, or abstract resource). Alternative to `WorkbookPath` — use one or the other |
| `SheetName` | SheetName | InArgument | `string` | Yes | | The name of the sheet from the workbook |
| `Range` | Range | InArgument | `string` | Yes | | The range to color (e.g. "A1:B10") |
| `Color` | Color | InArgument | `System.Drawing.Color` | Yes | | The color to apply to the range |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Password` | Password | `InArgument<string>` | | The password of the workbook, if necessary |
| `Workbook` | Workbook | `InArgument<Workbook>` | | Existing workbook object to use instead of a file path |

## XAML Example

```xml
<excel:SetRangeColor
  DisplayName="Set Range Color Workbook"
  WorkbookPath="[&quot;report.xlsx&quot;]"
  SheetName="[&quot;Sheet1&quot;]"
  Range="[&quot;A1:D10&quot;]"
  Color="[System.Drawing.Color.Yellow]" />
```

## Notes

- Uses the file-based workbook engine (not Excel Interop). Works cross-platform.
- `WorkbookPath` and `WorkbookPathResource` are mutually exclusive — set one or the other.
