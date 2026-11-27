# Get Cell Color

`UiPath.Excel.Activities.GetCellColorX`

Reads the background color of a specified Excel cell and outputs it as a `System.Drawing.Color` value.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Cell` | Cell | InArgument | `IReadCellRef` | Yes | | The address of the cell from which to read the value. |

### Output
| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `OutputColor` | Saved Color | OutArgument | `System.Drawing.Color` | Where to save the Color of the specified cell. |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Use Excel File">
  <excel:GetCellColorX
    Cell="[cellRef]"
    OutputColor="[outputColor]"
    DisplayName="Get Cell Color" />
</excel:ExcelApplicationCard>
```

## Notes
- The `Cell` must be a valid single-cell reference; otherwise a runtime error is thrown.
