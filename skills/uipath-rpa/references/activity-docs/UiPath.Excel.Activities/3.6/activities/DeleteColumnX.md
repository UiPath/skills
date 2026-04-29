# Delete Column

`UiPath.Excel.Activities.Business.DeleteColumnX`

Deletes a specified column from a sheet, table or range.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Range` | Source range | InArgument | `IReadWriteRangeRef` | Yes | | Source range. |
| `ColumnName` | Column name | InArgument | `string` | Yes | | The column to delete. |

### Configuration
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `HasHeaders` | Has headers | `bool` | `True` | Indicates the first row in the range is a header row. |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:DeleteColumnX
    Range="[MyRange]"
    ColumnName="Email"
    HasHeaders="True"
    DisplayName="Delete Column" />
</excel:ExcelApplicationCard>
```

## Notes
- When `HasHeaders` is `True`, the `ColumnName` refers to the header value of the column to delete.
- When `HasHeaders` is `False`, the `ColumnName` refers to column letter addresses (e.g. `A`, `B:D`). Multiple column ranges can be specified.
- For tables, the column is deleted by its name directly from the table structure.
- The range must be valid and `ColumnName` must not be empty; otherwise, an exception is thrown.
