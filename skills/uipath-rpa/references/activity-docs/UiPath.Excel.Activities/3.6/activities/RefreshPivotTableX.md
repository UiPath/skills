# Refresh Pivot Table

`UiPath.Excel.Activities.Business.RefreshPivotTableX`

Refreshes a specified pivot table or all pivot tables in the workbook. Optionally updates the layout row type.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Table` | Pivot table to refresh | InArgument | `IPivotTableRef` | Yes | | The pivot table to refresh. |
| `LayoutRowType` | Layout | Property | `PivotTableLayoutRowType?` | No | `null` | Enhance the pivot table layout and format. The compact form optimizes for readability, while tabular and outline forms include field headers. |

## Enum Reference

#### `PivotTableLayoutRowType`
| Value | Display Name |
|-------|-------------|
| `Compact` | Compact |
| `Tabular` | Tabular |
| `Outline` | Outline |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Use Excel File">
  <excel:RefreshPivotTableX
    Table="[pivotTableRef]"
    LayoutRowType="{x:Null}"
    DisplayName="Refresh Pivot Table" />
</excel:ExcelApplicationCard>
```

## Notes
- If the pivot table reference has the special "Refresh All Pivot Tables" name with empty worksheet and address, all pivot tables in the workbook are refreshed.
- When refreshing a specific pivot table, it must exist on the specified worksheet; otherwise an `ArgumentException` is thrown.
- When `LayoutRowType` is set (not null), the layout is applied before refreshing the data.
- The pivot table reference must include a valid parent handle; otherwise an `ArgumentNullException` is thrown.
