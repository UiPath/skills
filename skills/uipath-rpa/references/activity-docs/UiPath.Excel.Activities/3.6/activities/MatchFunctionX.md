# Match

`UiPath.Excel.Activities.Business.MatchFunctionX`

Searches for a specified item in a range of cells, and then returns the relative position of that item in the range.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ValueToMatch` | Value to match | InArgument | `object` | Yes | | The value to match in the indicated range. |
| `InRange` | In range | InArgument | `IWellDefinedReadRangeRef` | Yes | | Range to search for the value to match. Must be a single row or single column. |
| `MatchFunctionType` | Match type | Property | `MatchType` | No | `LargestValueLessOrEqual` | Used to specify how we are matching the value to match with values in given range. The default value for this argument is 1. |

### Output
| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `SaveTo` | Save to | `OutArgument<int>` | Save the value returned by the Match function. The value returned is the position of the matched value within the range, not the value itself. |

## Enum Reference

### `MatchType`
| Value | Description |
|-------|-------------|
| `LargestValueLessOrEqual` (1) | MATCH finds the largest value that is less than or equal to the lookup value. The values in the range must be in ascending order. |
| `ExactlyEqual` (0) | MATCH finds the first value that is exactly equal to the lookup value. The values in the range can be in any order. |
| `SmallestValueGreaterOrEqual` (-1) | MATCH finds the smallest value that is greater than or equal to the lookup value. The values in the range must be in descending order. |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:MatchFunctionX
    ValueToMatch="[SearchValue]"
    InRange="[LookupRange]"
    MatchFunctionType="ExactlyEqual"
    SaveTo="[MatchPosition]"
    DisplayName="Match" />
</excel:ExcelApplicationCard>
```

## Notes
- The `InRange` must be one-dimensional (single row or single column); a multi-dimensional range throws an error.
- The returned position is 1-based relative to the start of the range.
- This activity mirrors the behavior of Excel's native `MATCH` function.
