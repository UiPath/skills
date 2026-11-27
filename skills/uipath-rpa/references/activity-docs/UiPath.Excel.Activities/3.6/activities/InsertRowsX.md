# Insert Rows

`UiPath.Excel.Activities.Business.InsertRowsX`

Inserts one or more rows in a table, range, or sheet at the specified location.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Range` | Source range | InArgument | `IReadWriteRangeRef` | Yes | | The sheet, range, or table in which to insert the new rows. |
| `NbOfRows` | Number of rows | InArgument | `int` | Yes | | Number of rows to insert. |
| `InsertPosition` | Insert position | Property | `InsertRowPosition` | No | `End` | Where in the range to insert the new rows. |

### Configuration
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `SpecificIndex` | Specific index | `InArgument<int>` | | Row number in the range after which to insert the new rows if 'At position' is set to 'Specific index'. |
| `HasHeaders` | Has headers | `bool` | `True` | The first row in the range is a header row. |

## Valid Configurations

- `SpecificIndex` is only visible when `InsertPosition` is set to `Specific`.
- When `InsertPosition` is `Specific`, `SpecificIndex` is required; a validation error is raised if it is not set.

### Enum Reference

#### `InsertRowPosition`
| Value | Display Name |
|-------|-------------|
| `Start` | Start |
| `End` | End |
| `Specific` | Specific index |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:InsertRowsX
    Range="[MyRange]"
    NbOfRows="3"
    InsertPosition="End"
    HasHeaders="True"
    DisplayName="Insert Rows" />
</excel:ExcelApplicationCard>
```

## Notes
- The `NbOfRows` must be a positive integer; otherwise, an `ArgumentException` is thrown.
- When `InsertPosition` is `Specific`, the `SpecificIndex` must be within the bounds of the range (1 to number of rows); otherwise, an `IndexOutOfRangeException` is thrown.
- For tables, rows are inserted using table-specific operations. For regular ranges, the `HasHeaders` setting offsets the insertion position by one row when `True`.
- When inserting at the `End` of a sheet, the range is clipped to the used range before determining the insertion point.
