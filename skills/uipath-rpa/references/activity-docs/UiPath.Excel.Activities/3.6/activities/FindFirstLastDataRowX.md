# Find First/Last Data Row

`UiPath.Excel.Activities.Business.FindFirstLastDataRowX`

Finds the first and the last rows containing data in a given sheet, range or table.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Range` | Source range | InArgument | `IReadRangeRef` | Yes | | Range to search. |
| `ColumnName` | Column name | InArgument | `string` | Yes | | Column to search for data values. |
| `FirstRowOffset` | First row offset | Property | `int` | No | `0` | Adds the number specified to the first row containing data. Enables scenarios such as "find the 3rd row containing data". |
| `LastRowOffset` | Last row offset | Property | `int` | No | `0` | Subtracts the number specified to the last row containing data. Enables scenarios such as "find the 4th row from the bottom". |
| `BlankRowsToSkip` | Blank rows to skip | Property | `int` | No | `1` | Consecutive blank rows allowed in the data prior to determining the data in the range has ended. |

### Configuration
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `HasHeaders` | Has headers | `bool` | `True` | Indicates if first row in the range is a header row. |
| `ConfigureLastRowAs` | Configure last row as | `LastRowConfiguration` | `LastPopulatedRow` | Configure whether we want to return the last row as the last populated row or return the first row that is empty. |
| `VisibleRowsOnly` | Visible rows only | `bool` | `False` | Use only the visible rows, taking into account filters applied and ignoring hidden values. |

### Output
| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `FirstRowIndex` | First row index | `int` | Number of the first non-blank row in the range. If no data is found, the value will be -1. |
| `LastRowIndex` | Last row index | `int` | Number of the last non-blank row in the range. If no data is found, the value will be -1. |

### Enum Reference

#### `LastRowConfiguration`
| Value | Display Name |
|-------|-------------|
| `LastPopulatedRow` | Last populated row |
| `FirstEmptyRow` | First empty row |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:FindFirstLastDataRowX
    Range="[MyRange]"
    ColumnName="Name"
    FirstRowOffset="0"
    LastRowOffset="0"
    BlankRowsToSkip="1"
    HasHeaders="True"
    ConfigureLastRowAs="LastPopulatedRow"
    VisibleRowsOnly="False"
    FirstRowIndex="[FirstRow]"
    LastRowIndex="[LastRow]"
    DisplayName="Find First/Last Data Row" />
</excel:ExcelApplicationCard>
```

## Notes
- The `ColumnName` must reference a valid column in the range. For tables, use the table column name. For ranges with headers, use the header value. For ranges without headers, use the column letter.
- If no data is found in the specified column, both `FirstRowIndex` and `LastRowIndex` return `-1`.
- Negative values for `BlankRowsToSkip` are treated as `0`.
- The activity handles ranges, tables, and pivot tables, each resolving the target column address differently.
