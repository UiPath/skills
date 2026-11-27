# Read Range

`UiPath.Excel.Activities.Business.ReadRangeX`

Reads the value of an Excel range as a DataTable.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Range` | Range | InArgument | `IReadRangeRef` | Yes | | Range to read. |

### Configuration
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ReadFormatting` | Read formatting | `ReadFormattingOptions?` | `null` (same as project) | Choose what formatting should be applied to the values. Any value other than 'Default' will result in much slower performance. Null means that the formatting options are the same as for the parent card. |
| `HasHeaders` | Has headers | `bool` | `True` | First row in the range is a header row. |
| `VisibleOnly` | Visible rows only | `bool` | `True` | Read only the visible rows. Ignores filtered and hidden values. |

### Output
| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `SaveTo` | Save to | `OutArgument<DataTable>` | The DataTable where to save the contents of the range. To paste the data from the clipboard use Copy/Paste Range or other dedicated Paste activities. |

## Enum Reference

### `ReadFormattingOptions`
| Value | Description |
|-------|-------------|
| `Default` (0) | Overrides the project setting. Takes the default formatting returned by the COM API. |
| `RawValue` (1) | Overrides the project setting. Always retrieves the raw value and ignores all formatting. |
| `DisplayValue` (2) | Overrides the project setting. Takes the value as displayed in Excel. Truncated values (e.g. `####`) are returned as-is. |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:ReadRangeX
    Range="[MyRange]"
    HasHeaders="True"
    VisibleOnly="True"
    SaveTo="[OutputDataTable]"
    DisplayName="Read Range" />
</excel:ExcelApplicationCard>
```

## Notes
- When the range is a single cell, the activity reads the entire sheet starting from that cell (backward-compatible behavior).
- Setting `ReadFormatting` to `null` inherits the formatting option from the parent `ExcelApplicationCard`.
- The `VisibleOnly` flag is useful when reading from filtered data -- it ignores hidden and filtered rows.
