# Auto Fill

`UiPath.Excel.Activities.Business.AutoFillX`

Automatically fills cells downward based on the pattern detected in the specified start range. Works with both regular ranges and Excel tables.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `StartRange` | Start range | InArgument | `IWellDefinedReadRangeRef` | Yes | | Data source to fill cells with. |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Use Excel File">
  <excel:AutoFillX
    StartRange="[myRange]"
    DisplayName="Auto Fill" />
</excel:ExcelApplicationCard>
```

## Notes
- When the start range refers to an Excel table, the activity fills down within the table structure.
- When the start range refers to a regular cell range, the activity uses the address-based auto-fill.
- The range must be a valid, well-defined range; otherwise a runtime error is thrown.
