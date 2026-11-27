# Get Selected Range

`UiPath.Excel.Activities.Windows.Business.GetSelectedRangeX`

Get the selected range from the target Excel file.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Workbook` | Target Workbook | InArgument | `IWorkbookQuickHandle` | Yes | | The workbook from which to get selected range. |

### Output
| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Range` | Range | `OutArgument<IReadRangeRef>` | The selected range. |

## XAML Example
```xml
<excelwin:GetSelectedRangeX
  Workbook="[CurrentWorkbook]"
  Range="[SelectedRange]"
  DisplayName="Get Selected Range"
  xmlns:excelwin="clr-namespace:UiPath.Excel.Activities.Windows.Business;assembly=UiPath.Excel.Activities" />
```

## Notes
- The `Workbook` property is auto-filled from the parent `ExcelApplicationCard` scope.
- Returns the currently selected range in the active workbook as an `IReadRangeRef` that can be passed to other range activities.
