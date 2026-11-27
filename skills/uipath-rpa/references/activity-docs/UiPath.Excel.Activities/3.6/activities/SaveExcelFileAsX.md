# Save Excel File As

`UiPath.Excel.Activities.Business.SaveExcelFileAsX`

Save an Excel file as a different file.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Workbook` | Workbook | InArgument | `IWorkbookQuickHandle` | Yes | | Which workbook to save. |
| `SaveAsFileType` | Save as type | Property | `ExcelSaveAsType` | Yes | `OpenXmlWorkbook` | Format to save the workbook. |
| `FilePath` | Save as file | InArgument | `string` | Yes | | Name of the new file. |

### Configuration
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ReplaceExisting` | Replace existing | `bool` | `True` | Replace existing file of the same name. |

### Enum Reference

#### `ExcelSaveAsType`
| Value | Description |
|-------|-------------|
| `OpenXmlWorkbook` | Normal workbook (.xlsx) |
| `BinaryWorkbook` | Binary workbook (.xlsb) |
| `MacroEnabledWorkbook` | Macro enabled workbook (.xlsm) |
| `OldWorkbook` | Excel 97-2003 workbook (.xls) |

## XAML Example
```xml
<excel:SaveExcelFileAsX
  DisplayName="Save Excel File As"
  Workbook="[workbookHandle]"
  SaveAsFileType="OpenXmlWorkbook"
  FilePath="[&quot;C:\Output\report_copy.xlsx&quot;]"
  ReplaceExisting="True" />
```

## Notes
- If the file path does not end with the correct extension for the selected file type, the extension is appended automatically.
- The destination folder must already exist; the activity does not create directories.
- If `ReplaceExisting` is `False` and a file with the same name already exists, the activity throws an `ArgumentException`.
