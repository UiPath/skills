# Fill Range

`UiPath.Excel.Activities.Business.FillRangeX`

Enters a formula or value in all the cells in a range.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `DestinationRange` | Where to write | InArgument | `IWellDefinedReadWriteRangeRef` | Yes | | Range to fill with the formula or value. |
| `Value` | What to write | InArgument | `object` | Yes | | Formula or value to add to the cells in the range. |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:FillRangeX
    DestinationRange="[MyRange]"
    Value="=SUM(A1:A10)"
    DisplayName="Fill Range" />
</excel:ExcelApplicationCard>
```

## Notes
- The `Value` property accepts both literal values and Excel formulas (prefixed with `=`).
- The value is converted to a string representation before being written to each cell in the range.
- The destination range must be a well-defined range (not an entire sheet); otherwise, a validation error is raised.
- The activity supports cancellation and checks for cancellation requests during execution.
