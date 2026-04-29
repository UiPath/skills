# Clear Sheet/Range/Table

`UiPath.Excel.Activities.Business.ClearRangeX`

Clears the data from a spreadsheet sheet, range, or table.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `TargetRange` | Range to clear | InArgument | `IReadWriteRangeRef` | Yes | | Accepts a sheet, range or table to clear the data from. |

### Configuration
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `HasHeaders` | Has headers | `bool` | `False` | First row in the range is a header row. |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:ClearRangeX
    TargetRange="[MyRange]"
    HasHeaders="False"
    DisplayName="Clear Sheet/Range/Table" />
</excel:ExcelApplicationCard>
```

## Notes
- When `HasHeaders` is `True`, the first row (header row) of the range is preserved and only the data rows are cleared.
- For pivot tables, the activity clears the pivot table. For tables, it clears the range address. For regular ranges, it builds a range excluding headers if specified.
- The target range must be valid; otherwise, an `ArgumentNullException` is thrown.
