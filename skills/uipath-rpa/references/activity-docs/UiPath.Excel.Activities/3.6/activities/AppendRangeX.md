# Append Range

`UiPath.Excel.Activities.Business.AppendRangeX`

Copies the data in a table, range, or sheet and pastes it after existing data in another specified table, range, or sheet.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `SourceRange` | Excel range to append | InArgument | `IReadRangeRef` | Yes | | Excel range to append. |
| `DestinationRange` | Append after range | InArgument | `IReadWriteRangeRef` | Yes | | Target range after which to append the new range. |
| `PasteOptions` | What to copy | Property | `CopyPasteRangeOptions` | No | `All` | The value formatting for the new range. |
| `Transpose` | Transpose | Property | `bool` | No | `False` | Inserts columns as rows and rows as columns. |
| `StartingColumnName` | Starting in column | InArgument | `string` | No | | Append the data starting with the first empty cell in the specified column. |

### Configuration
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `HasHeaders` | Exclude source headers | `bool` | `False` | First row from the selected range will not be written to the destination. |
| `DestinationHasHeaders` | Destination has headers | `bool` | `False` | If true, the first row of the destination range contains column names and will be used to identify the Starting Column. |

### Enum Reference

#### `CopyPasteRangeOptions`
| Value | Display Name |
|-------|-------------|
| `All` | All |
| `Values` | Values |
| `Formulas` | Formulas |
| `Formats` | Formats |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:AppendRangeX
    SourceRange="[SourceRange]"
    DestinationRange="[DestRange]"
    PasteOptions="All"
    Transpose="False"
    HasHeaders="False"
    DestinationHasHeaders="False"
    DisplayName="Append Range" />
</excel:ExcelApplicationCard>
```

## Notes
- Both `SourceRange` and `DestinationRange` must be valid ranges; otherwise, an `ArgumentNullException` is thrown at runtime.
- When `StartingColumnName` is specified and `DestinationHasHeaders` is `True`, the activity uses the header row of the destination to locate the column where appending begins.
- If `HasHeaders` is `True`, the first row of the source range is excluded from the appended data.
