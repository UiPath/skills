# Autofit Range

`UiPath.Excel.Activities.Business.AutoFitX`

Fits data in cells.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Range` | Range | InArgument | `IReadRangeRef` | Yes | | Data source. |

### Configuration
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Columns` | Columns | `bool` | `True` | If true, applies autofit only on range's columns. |
| `Rows` | Rows | `bool` | `True` | If true, applies autofit only on range's rows. |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:AutoFitX
    Range="[MyRange]"
    Columns="True"
    Rows="True"
    DisplayName="Autofit Range" />
</excel:ExcelApplicationCard>
```

## Notes
- At least one of `Columns` or `Rows` must be `True`; otherwise, a validation error is raised at design time.
- The activity supports ranges, tables, pivot tables, and entire sheets.
