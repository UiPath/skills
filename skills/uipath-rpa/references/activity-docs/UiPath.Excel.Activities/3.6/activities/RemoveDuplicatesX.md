# Remove Duplicates

`UiPath.Excel.Activities.Business.RemoveDuplicatesX`

Delete duplicate rows from a range, table, or sheet by comparing values in specified columns.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Range` | Range | InArgument | `IReadWriteRangeRef` | Yes | | Range from which to remove duplicates. |
| `ColumnsCompareMode` | Compare mode | Property | `ColumnsCompare` | No | `IndividualColumns` | Whether to compare individual columns or all columns when identifying duplicates. Displayed as a radio group in the designer. |
| `Columns` | Columns to compare | Property | `List<InArgument<string>>` | No | | The columns that will be compared to determine if a row is a duplicate. If the values in all of the indicated columns are the same as a previous row, it is considered a duplicate. Visible only when `ColumnsCompareMode` is `IndividualColumns`. |

### Configuration
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `HasHeaders` | Has headers | `bool` | `True` | The first row in the range is a header row. |

### Enum Reference

#### `ColumnsCompare`
| Value | Display Name |
|-------|-------------|
| `IndividualColumns` | Individual columns |
| `AllColumns` | All columns |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:RemoveDuplicatesX
    Range="[MyRange]"
    HasHeaders="True"
    ColumnsCompareMode="IndividualColumns"
    DisplayName="Remove Duplicates">
    <excel:RemoveDuplicatesX.Columns>
      <InArgument x:TypeArguments="x:String">Name</InArgument>
      <InArgument x:TypeArguments="x:String">Email</InArgument>
    </excel:RemoveDuplicatesX.Columns>
  </excel:RemoveDuplicatesX>
</excel:ExcelApplicationCard>
```

## Notes
- When `ColumnsCompareMode` is `IndividualColumns`, at least one column must be specified in the `Columns` list.
- When `ColumnsCompareMode` is `AllColumns`, all columns in the range are used for duplicate comparison and the `Columns` property is hidden.
- Duplicate column names in the `Columns` list are not allowed.
- Empty column entries in the `Columns` list are not allowed.
- Rows are considered duplicates when all compared columns have the same values as a previous row.
