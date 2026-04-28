# Change Pivot Table Data Source

`UiPath.Excel.Activities.Business.ChangePivotTableDataSourceX`

Changes the data source of an existing pivot table to a new range within the same workbook.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `PivotTable` | Pivot table | InArgument | `IPivotTableRef` | Yes | | The original Pivot table to be updated. |
| `NewSourceRange` | New source | InArgument | `IWellDefinedReadRangeRef` | Yes | | The new range to be used as Source for the Pivot Table. |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Use Excel File">
  <excel:ChangePivotTableDataSourceX
    PivotTable="[pivotTableRef]"
    NewSourceRange="[newRange]"
    DisplayName="Change Pivot Table Data Source" />
</excel:ExcelApplicationCard>
```

## Notes
- The pivot table and the new source range must be in the same workbook. Using different workbooks for the source and pivot table is not supported and throws an error.
- The pivot table must exist on the specified worksheet; otherwise an `ArgumentException` is thrown.
- The pivot table reference must include a valid address, worksheet, and parent handle.
