# Copy/Paste Range

`UiPath.Excel.Activities.Business.CopyPasteRangeX`

Copies a range or sheet and optionally pastes it to another location in the current workbook or a different one.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `SourceRange` | Source range | InArgument | `IReadRangeRef` | Yes | | The range to copy. |
| `DestinationRange` | Destination | InArgument | `IReadWriteRangeRef` | Yes | | Where to put the copied range. |
| `PasteOptions` | What to copy | Property | `CopyPasteRangeOptions` | No | `All` | The value formatting to insert. |
| `ExcludeHeaders` | Exclude header from source range | Property | `bool` | No | `False` | Excludes the header row from the source range when copying. |
| `ExcludeHeaderFromSourceTable` | Exclude headers from source table | Property | `bool` | No | `True` | Excludes headers from the source table when copying. |
| `Transpose` | Transpose | Property | `bool` | No | `False` | Inserts columns as rows and rows as columns. |

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
  <excel:CopyPasteRangeX
    SourceRange="[SourceRange]"
    DestinationRange="[DestRange]"
    PasteOptions="All"
    ExcludeHeaders="False"
    ExcludeHeaderFromSourceTable="True"
    Transpose="False"
    DisplayName="Copy/Paste Range" />
</excel:ExcelApplicationCard>
```

## Notes
- Either `SourceRange` or `DestinationRange` can be a clipboard placeholder, but not both simultaneously.
- When the destination is a clipboard placeholder, the source is copied to the system clipboard. When the source is a clipboard placeholder, the clipboard contents are pasted at the destination.
- If the destination covers an entire sheet, the paste target defaults to cell A1.
- Both source and destination must be valid ranges or clipboard placeholders; otherwise, an `ArgumentNullException` is thrown.
