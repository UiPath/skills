# Insert Sheet

`UiPath.Excel.Activities.Business.InsertSheetX`

Inserts a sheet in an Excel file.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Workbook` | Create in workbook | InArgument | `IWorkbookQuickHandle` | Yes | | Excel workbook in which to insert the sheet. |
| `Name` | New sheet name | InArgument | `string` | Yes | | Name of the new sheet. |

### Output
| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `ReferenceNewSheetAs` | Reference new sheet as | `OutArgument<ISheetRef>` | Name you will use to refer to the new sheet in other activities. |

## XAML Example
```xml
<excel:InsertSheetX
  DisplayName="Insert Sheet"
  Workbook="[workbookHandle]"
  Name="[&quot;NewSheet&quot;]"
  ReferenceNewSheetAs="[newSheetRef]" />
```

## Notes
- The `ReferenceNewSheetAs` output provides a sheet reference that can be used by subsequent activities.
- Throws `ArgumentNullException` if the workbook is null or the sheet name is empty.
