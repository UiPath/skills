# VLookup

`UiPath.Excel.Activities.Business.VLookupX`

Finds data in a range or sheet using Excel's VLOOKUP function.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `SourceRange` | In range | InArgument | `IReadRangeRef` | Yes | | Range to search for the value to lookup. |
| `Label` | Value to lookup | InArgument | `object` | Yes | | The value to lookup in the indicated range. |
| `ColumnIndex` | Column index | InArgument | `int` | No | | The column number in the range containing the value to return. If not specified, defaults to the last column in the range. |
| `ExactMatch` | Exact match | Property | `bool` | No | `True` | Return only exact matches. Otherwise approximate matches are returned. |

### Output
| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Value` | Output to | `OutArgument` | Save the value returned by the VLOOKUP. |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:VLookupX
    SourceRange="[LookupRange]"
    Label="[SearchValue]"
    ColumnIndex="3"
    ExactMatch="True"
    Value="[Result]"
    DisplayName="VLookup" />
</excel:ExcelApplicationCard>
```

## Notes
- The `Label` property accepts any object type; the value is compared to entries in the first column of the `SourceRange`.
- If `ColumnIndex` is not specified or is `0`, the activity returns the value from the last column in the range.
- When `ExactMatch` is `False`, the first column of `SourceRange` must be sorted in ascending order for correct approximate matching behavior.
- The `Value` output is an untyped `OutArgument` and can hold any value type returned by the lookup.
