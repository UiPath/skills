# Duplicate Sheet

`UiPath.Excel.Activities.Business.DuplicateSheetX`

Creates a copy of the specified sheet in an Excel file.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `SheetToDuplicate` | Sheet to duplicate | InArgument | `ISheetRef` | Yes | | The sheet to copy. |
| `NewSheetName` | Rename to | InArgument | `string` | Yes | `"New Sheet"` | Name of the new copy. |

## XAML Example
```xml
<excel:DuplicateSheetX
  DisplayName="Duplicate Sheet"
  SheetToDuplicate="[sourceSheet]"
  NewSheetName="[&quot;Sheet1 Copy&quot;]" />
```

## Notes
- The new sheet is inserted after the source sheet.
- The `NewSheetName` defaults to `"New Sheet"` if not specified.
- Throws `ArgumentNullException` if the sheet reference is null or the new name is empty.
