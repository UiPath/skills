# Rename Sheet

`UiPath.Excel.Activities.Business.RenameSheetX`

Renames a sheet in an Excel file.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `From` | From | InArgument | `ISheetRef` | Yes | | The sheet to rename. |
| `To` | To | InArgument | `string` | Yes | | New name to give the selected sheet. |

## XAML Example
```xml
<excel:RenameSheetX
  DisplayName="Rename Sheet"
  From="[sheetReference]"
  To="[&quot;RenamedSheet&quot;]" />
```

## Notes
- Throws `ArgumentNullException` if the sheet reference is null or the new name is empty.
