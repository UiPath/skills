# Copy/Save Chart

`UiPath.Excel.Activities.Business.CopyChartToClipboardX`

Copies an Excel chart to the clipboard or saves it as a picture file, depending on the selected action.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Chart` | Chart | InArgument | `IChartRef` | Yes | | Choose the chart. |
| `Action` | Action | Property | `ExcelChartAction` | Yes | `CopyToClipboard` | Action to apply to the selected chart. |
| `FilePath` | File name | InArgument | `string` | Conditional | | File where the chart will be saved. Only visible and required when Action is SaveAsPicture. |
| `ReplaceFile` | Replace existing file | Property | `bool` | No | `True` | Whether to replace an existing file at the specified path. Only visible when Action is SaveAsPicture. |

## Conditional Visibility

- `FilePath` and `ReplaceFile` are only visible when `Action` is `SaveAsPicture`.
- When `Action` is `SaveAsPicture`, `FilePath` is required (validated at design time).

### Enum Reference

#### `ExcelChartAction`
| Value | Display Name |
|-------|-------------|
| `CopyToClipboard` | Copy to clipboard |
| `SaveAsPicture` | Save as picture |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Use Excel File">
  <excel:CopyChartToClipboardX
    Chart="[chartRef]"
    Action="CopyToClipboard"
    DisplayName="Copy Chart to Clipboard" />
</excel:ExcelApplicationCard>
```

### Save as picture variant
```xml
<excel:ExcelApplicationCard DisplayName="Use Excel File">
  <excel:CopyChartToClipboardX
    Chart="[chartRef]"
    Action="SaveAsPicture"
    FilePath="[&quot;C:\output\chart.png&quot;]"
    ReplaceFile="True"
    DisplayName="Save Chart as Picture" />
</excel:ExcelApplicationCard>
```

## Notes
- The chart reference is typically obtained from the output of `InsertExcelChartX` or by referencing an existing chart in the workbook.
- When saving as picture, the file path must be a valid absolute path; an error is thrown if the folder does not exist.
