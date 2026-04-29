# Save As PDF

`UiPath.Excel.Activities.Business.SaveAsPdfX`

Saves an Excel file as a PDF file.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Workbook` | Workbook | InArgument | `IWorkbookQuickHandle` | Yes | | Excel file to save to PDF format. |
| `DestinationPdfPath` | Destination pdf path | InArgument | `string` | Yes | | Name of the new PDF file. |
| `StartPage` | Start page | InArgument | `int?` | No | | Start export at this page. |
| `EndPage` | End page | InArgument | `int?` | No | | Stop export at this page. |

### Configuration
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `SaveQuality` | Save quality | `PdfSaveQuality` | `StandardQuality` | Quality of the PDF file. Higher quality creates a bigger file. |
| `ReplaceExisting` | Replace existing | `bool` | `True` | If a file with this name already exists, replace it. Otherwise an error will occur if the file already exists. |

### Enum Reference

#### `PdfSaveQuality`
| Value | Description |
|-------|-------------|
| `StandardQuality` | Standard quality |
| `MinimumQuality` | Minimum quality |

## XAML Example
```xml
<excel:SaveAsPdfX
  DisplayName="Save As PDF"
  Workbook="[workbookHandle]"
  DestinationPdfPath="[&quot;C:\Output\report.pdf&quot;]"
  StartPage="[1]"
  EndPage="[5]"
  SaveQuality="StandardQuality"
  ReplaceExisting="True" />
```

## Notes
- If the destination path does not include a `.pdf` extension, it is added automatically.
- `StartPage` and `EndPage` must be positive integers (greater than 0) when specified.
- `StartPage` must be less than or equal to `EndPage` when both are specified.
- The destination folder must already exist; the activity does not create directories.
- The `DestinationPdfPath` category in the designer is **File**.
