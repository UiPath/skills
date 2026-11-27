# Text to Columns

`UiPath.Excel.Activities.Business.TextToColumnsX`

Splits the text from a cell, range, or table into different columns.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `SourceRange` | Source range | InArgument | `IWellDefinedReadRangeRef` | Yes | | Range containing the text to split. |
| `DestinationRange` | Destination | InArgument | `IReadWriteRangeRef` | Yes | | Where the split data will be saved. |

### Configuration
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ParsingType` | Parsing type | `TextToColumnsParsingType` | `Delimited` | Delimited: data is separated by certain characters. Fixed width: data is separated in groups of a certain number of characters. |
| `NumberOfCharactersPerColumn` | Number of characters per column | `InArgument<int>` | | Width of each unit of data to be split. Visible only when `ParsingType` is `FixedWidth`. Required when `ParsingType` is `FixedWidth`. |
| `SplitByTabs` | Split by tabs | `bool` | `True` | Data is separated by a tab. Visible only when `ParsingType` is `Delimited`. |
| `SplitBySemicolon` | Split by semicolon | `bool` | `True` | Data is separated by a semicolon. Visible only when `ParsingType` is `Delimited`. |
| `SplitByComma` | Split by comma | `bool` | `True` | Data is separated by a comma. Visible only when `ParsingType` is `Delimited`. |
| `SplitBySpace` | Split by space | `bool` | `True` | Data is separated by a space. Visible only when `ParsingType` is `Delimited`. |
| `SplitByLineBreak` | Split by new line | `bool` | `False` | Data is separated by a new line. Visible only when `ParsingType` is `Delimited`. Cannot be used together with `SplitByOther`. |
| `SplitByOther` | Split by other | `bool` | `False` | Data is separated by a character not listed. Visible only when `ParsingType` is `Delimited`. |
| `OtherSeparator` | Other delimiter | `char?` | | Enter the character that separates the data. Visible only when `ParsingType` is `Delimited`. Required when `SplitByOther` is `True`. |
| `ConsecutiveOperatorsAsOne` | Consecutive operators as one | `bool` | `True` | Data contains delimiters with multiple characters. Visible only when `ParsingType` is `Delimited`. |
| `TextQualifier` | Text qualifier | `TextToColumnsTextQualifier` | `None` | The character that encloses text in your data. Text between two consecutive text qualifiers is treated as one value. Visible only when `ParsingType` is `Delimited`. |

## Valid Configurations

When `ParsingType` is `Delimited`, the delimiter options (`SplitByTabs`, `SplitBySemicolon`, `SplitByComma`, `SplitBySpace`, `SplitByLineBreak`, `SplitByOther`, `OtherSeparator`, `ConsecutiveOperatorsAsOne`, `TextQualifier`) are visible. When `ParsingType` is `FixedWidth`, only `NumberOfCharactersPerColumn` is visible.

### Enum Reference

#### `TextToColumnsParsingType`
| Value | Display Name |
|-------|-------------|
| `Delimited` | Delimited |
| `FixedWidth` | Fixed Width |

#### `TextToColumnsTextQualifier`
| Value | Display Name |
|-------|-------------|
| `None` | None |
| `DoubleQuote` | Double Quote |
| `SingleQuote` | Single Quote |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:TextToColumnsX
    SourceRange="[SourceRange]"
    DestinationRange="[DestRange]"
    ParsingType="Delimited"
    SplitByComma="True"
    SplitByTabs="False"
    SplitBySemicolon="False"
    SplitBySpace="False"
    SplitByLineBreak="False"
    SplitByOther="False"
    ConsecutiveOperatorsAsOne="True"
    TextQualifier="None"
    DisplayName="Text to Columns" />
</excel:ExcelApplicationCard>
```

## Notes
- Source and destination must be on the same worksheet.
- `SplitByLineBreak` and `SplitByOther` cannot both be `True` at the same time. Internally, line break splitting uses the "Other" mechanism.
- When `ParsingType` is `FixedWidth`, `NumberOfCharactersPerColumn` is required.
- When `SplitByOther` is `True`, `OtherSeparator` must be specified.
