# Delete Rows

`UiPath.Excel.Activities.Business.DeleteRowsX`

Deletes the specified rows from a sheet, table, or range.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Range` | Source range | InArgument | `IReadWriteRangeRef` | Yes | | The sheet, table, or range from which to delete rows. |
| `DeleteRowsOption` | What to delete | Property | `DeleteRowsOption` | Yes | `Specific` | The type of delete to perform. |

### Configuration
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `RowPositions` | At position | `InArgument<string>` | | The rows to delete when the option 'Specific rows' is selected. |
| `HasHeaders` | Has headers | `bool` | `True` | The first row in the range is not deleted when the option 'All visible rows' is selected. |

## Valid Configurations

- `RowPositions` is only visible when `DeleteRowsOption` is set to `Specific`.
- When `DeleteRowsOption` is `Specific`, `RowPositions` is required and must follow a valid row index format (e.g., `"1"`, `"1-3"`, `"1,3,5"`).

### Enum Reference

#### `DeleteRowsOption`
| Value | Display Name |
|-------|-------------|
| `Specific` | Specific rows |
| `Visible` | All visible rows |
| `Hidden` | All hidden rows |
| `Duplicates` | Duplicate rows |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:DeleteRowsX
    Range="[MyRange]"
    DeleteRowsOption="Specific"
    RowPositions="1,3,5"
    HasHeaders="True"
    DisplayName="Delete Rows" />
</excel:ExcelApplicationCard>
```

## Notes
- A design-time warning is displayed if this activity is placed inside an `ExcelForEachRowX` activity when both target the same range. Use a filter and delete all visible rows instead.
- When targeting a table, the first row (header) is always preserved, and row deletion operates on the data rows.
- When `HasHeaders` is `True` on a non-table range, the first row is preserved during deletion.
- The `RowPositions` format supports individual rows (`1,3,5`) and ranges (`2-5`).
- The activity cannot delete the current row when used with a `CurrentRow` reference.
