# Save Excel File

`UiPath.Excel.Activities.Business.SaveExcelFileX`

Saves any pending changes in the selected Excel file.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Workbook` | Workbook | InArgument | `IWorkbookQuickHandle` | Yes | | File to save any pending changes to. |

## XAML Example
```xml
<excel:SaveExcelFileX
  DisplayName="Save Excel File"
  Workbook="[workbookHandle]" />
```

## Notes
- This activity saves the workbook in place (overwrites the existing file).
- Use `SaveExcelFileAsX` if you need to save to a different path or format.
