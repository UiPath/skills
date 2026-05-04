# Lookup

`UiPath.Excel.Activities.Business.LookupX`

Finds data in a range or sheet using Excel's LOOKUP function.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `SourceRange` | Range | InArgument | `IReadRangeRef` | Yes | | Range to search for the value to lookup. |
| `ResultRange` | Source of results | InArgument | `IReadRangeRef` | No | | Range from where value is returned. Must be a single row or single column if provided. |
| `Label` | Value to lookup | InArgument | `object` | Yes | | The value to lookup in the indicated range. |

### Output
| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Value` | Result | `OutArgument` | Save the value returned by the LOOKUP. |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:LookupX
    SourceRange="[SearchRange]"
    ResultRange="[ReturnRange]"
    Label="[SearchValue]"
    Value="[Result]"
    DisplayName="Lookup" />
</excel:ExcelApplicationCard>
```

## Notes
- The `Label` property accepts any object type; the value is compared to entries in the `SourceRange`.
- If `ResultRange` is not provided, the result is returned from the same range as the source.
- The `ResultRange` must be one-dimensional (single row or single column); a multi-dimensional range throws an error.
- The `Value` output is an untyped `OutArgument` and can hold any value type returned by the lookup.
