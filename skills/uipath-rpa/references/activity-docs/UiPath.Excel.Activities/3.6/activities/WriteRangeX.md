# Write Range

`UiPath.Excel.Activities.Business.WriteRangeX`

Write Range is intended for writing data from external Data Table sources into Excel.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Source` | What to write | InArgument | `DataTable` | Yes | | Write Range is intended for writing data from external Data Table sources into Excel. Use the 'Copy/Paste Range' activity when moving data between locations in Excel. |

### Output
| Name | Display Name | Kind | Type | Required | Description |
|------|-------------|------|------|----------|-------------|
| `Destination` | Destination | InArgument | `IReadWriteRangeRef` | Yes | Where to write the data. |

### Configuration
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Append` | Append | `bool` | `False` | Append the new data starting at the first blank row in the indicated range. |
| `ExcludeHeaders` | Exclude headers | `bool` | `False` | Indicates any headers (or the first row in the selected range) will not be written to the destination range. |
| `IgnoreEmptySource` | Ignore empty source | `bool` | `False` | When checked, if the source data table is empty it will be ignored. Otherwise it will throw an error. |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:WriteRangeX
    Source="[MyDataTable]"
    Destination="[DestRange]"
    Append="False"
    ExcludeHeaders="False"
    IgnoreEmptySource="False"
    DisplayName="Write Range" />
</excel:ExcelApplicationCard>
```

## Notes
- The `Destination` property is categorized as "Output" in the activity class but functions as an input specifying where data is written (it is an `InArgument`, not an `OutArgument`).
- When `Append` is `True`, data is written starting at the first blank row in the destination range.
- When `IgnoreEmptySource` is `False` (default), an empty `DataTable` (no rows and no columns, or no rows when headers are excluded) throws an error.
- Use the 'Copy/Paste Range' activity instead when moving data between locations within Excel.
