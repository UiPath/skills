# Read Cell Formula

`UiPath.Excel.Activities.Business.ReadCellFormulaX`

Reads the formula from a specified Excel cell and saves it as a string. The returned formula includes the leading `=` sign.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Cell` | Cell | InArgument | `IReadCellRef` | Yes | | The address of the cell from which to read the formula. |

### Output
| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `SaveTo` | Save to | OutArgument | `string` | Where to save the formula read from the cell. |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Use Excel File">
  <excel:ReadCellFormulaX
    Cell="[cellRef]"
    SaveTo="[formulaResult]"
    DisplayName="Read Cell Formula" />
</excel:ExcelApplicationCard>
```

## Notes
- If the cell does not contain a formula, an empty string is returned.
- The returned formula string is prefixed with `=` (e.g., `=SUM(A1:A10)`).
- The `Cell` must be a valid single-cell reference; otherwise a runtime error is thrown.
