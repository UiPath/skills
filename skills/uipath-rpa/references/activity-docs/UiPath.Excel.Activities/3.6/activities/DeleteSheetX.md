# Delete Sheet

`UiPath.Excel.Activities.Business.DeleteSheetX`

Deletes a specified sheet from an Excel file.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Sheet` | Select sheet | InArgument | `ISheetRef` | Yes | | The sheet to delete from the Excel workbook. |

## XAML Example
```xml
<excel:DeleteSheetX
  DisplayName="Delete Sheet"
  Sheet="[sheetReference]" />
```

## Notes
- The `Sheet` property must reference an existing sheet in the workbook.
- Throws `ArgumentNullException` if the sheet reference is null.
