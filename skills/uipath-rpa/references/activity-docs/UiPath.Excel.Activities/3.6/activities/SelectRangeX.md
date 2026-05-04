# Select Range

`UiPath.Excel.Activities.Windows.Business.SelectRangeX`

Selects a range in the specified Excel file.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Range` | Range | InArgument | `IReadRangeRef` | Yes | | Range to select. |

## XAML Example
```xml
<excelwin:SelectRangeX
  Range="[TargetRange]"
  DisplayName="Select Range"
  xmlns:excelwin="clr-namespace:UiPath.Excel.Activities.Windows.Business;assembly=UiPath.Excel.Activities" />
```

## Notes
- This activity selects the specified range in the Excel UI, making it the active selection.
- The range must be valid; an invalid range throws an `ArgumentNullException`.
