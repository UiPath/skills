# Write Cell

`UiPath.Excel.Activities.Business.WriteCellX`

Writes a value or formula to a specified Excel cell. Supports an auto-increment row feature for use inside loops.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Value` | What to write | InArgument | `object` | Yes | | The value or formula to enter into the cell. |

### Destination
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Cell` | Where to write | InArgument | `IReadWriteCellRef` | Yes | | The cell in which to write the value or formula. |

### Options
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `AutoIncrementRow` | Auto increment row | Property | `bool` | No | `False` | When inside a For Each activity, relative cell references (no $) will automatically increase the row number each iteration. |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Use Excel File">
  <excel:WriteCellX
    Cell="[cellRef]"
    Value="[valueToWrite]"
    AutoIncrementRow="False"
    DisplayName="Write Cell" />
</excel:ExcelApplicationCard>
```

## Notes
- This activity extends `NativeActivity` (not `ExcelBusinessActivity`) to support the auto-increment row tracking state across iterations.
- When `AutoIncrementRow` is enabled, each subsequent execution targeting the same cell address within the same workbook/sheet automatically offsets to the next row.
- The `Cell` must be a valid single-cell reference with read-write access; otherwise a runtime error is thrown.
- Both values and formulas (starting with `=`) can be written.
