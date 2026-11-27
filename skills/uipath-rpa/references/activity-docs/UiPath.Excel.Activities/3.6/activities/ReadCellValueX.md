# Read Cell Value

`UiPath.Excel.Activities.Business.ReadCellValueX`

Reads the value from a specified Excel cell. Can return either the formatted display value or the raw underlying value.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Cell` | Cell | InArgument | `IReadCellRef` | Yes | | The address of the cell from which to read the value. |

### Options
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `GetFormattedText` | Get formatted text | Property | `bool` | No | `True` | Retrieves value including any formatting applied in Excel. If false, the raw value is retrieved. |

### Output
| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `SaveTo` | Save to | OutArgument | `object` | Where to save the value read from the cell. |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Use Excel File">
  <excel:ReadCellValueX
    Cell="[cellRef]"
    GetFormattedText="True"
    SaveTo="[cellValue]"
    DisplayName="Read Cell Value" />
</excel:ExcelApplicationCard>
```

## Notes
- The `SaveTo` output is a non-generic `OutArgument` and can hold any type (string, number, date, etc.).
- When `GetFormattedText` is `True`, the value as displayed in Excel (e.g., "$1,234.56") is returned.
- When `GetFormattedText` is `False`, the raw underlying value (e.g., `1234.56`) is returned.
- The `Cell` must be a valid single-cell reference; otherwise a runtime error is thrown.
