# XAML Excel Activities

Excel activity patterns for `UiPath.Excel.Activities`. Always get full XAML from `uip rpa get-default-activity-xaml --use-studio` — this file covers confirmed patterns from real workflows only.

## Package

`UiPath.Excel.Activities`

## Two Distinct Styles

| Style | Namespace prefix | Scope required | Activities |
|-------|-----------------|---------------|------------|
| **Modern** (`ueab:`) | `xmlns:ueab="clr-namespace:UiPath.Excel.Activities.Business;assembly=UiPath.Excel.Activities"` | Yes — `ExcelApplicationCard` | `ReadRangeX`, `WriteRangeX`, `ExcelForEachRowX`, etc. |
| **Classic** (`ui:`) | `xmlns:ui="http://schemas.uipath.com/workflow/activities"` | No — standalone | `ReadRange`, `WriteRange`, `AppendRange`, `ForEachRow` |

Both styles also need:
```xml
xmlns:ue="clr-namespace:UiPath.Excel;assembly=UiPath.Excel.Activities"
```
(for `IWorkbookQuickHandle`, `ISheetRef`, `CurrentRowQuickHandle`, `WorksheetQuickHandle`, `IChartRef` types)

Additional sub-namespaces (modern only, add when using the relevant activities):
```xml
xmlns:ueabf="clr-namespace:UiPath.Excel.Activities.Business.Filter;assembly=UiPath.Excel.Activities"
xmlns:ueabc="clr-namespace:UiPath.Excel.Activities.Business.ChartModifications;assembly=UiPath.Excel.Activities"
```

Namespace imports needed in `TextExpression.NamespacesForImplementation`:
- `UiPath.Excel`
- `UiPath.Excel.Activities.Business`

## Key Patterns

| Pattern | Notes |
|---------|-------|
| Modern scope | `ueab:ExcelApplicationCard` with `ActivityAction<ue:IWorkbookQuickHandle>`, argument name `"Excel"` |
| Sheet reference (modern) | `Excel.Sheet("SheetName")` — used in `Range`, `Destination`, `WhereToSearch` etc. |
| Cell range (modern) | `Excel.Sheet("SheetName").Range("A1:B10")` |
| Direct cell (modern) | `Excel.Sheet("SheetName").Cell("A1")` — used in `WriteCellX`, `ReadCellValueX` |
| Pivot table reference | `Excel.Sheet("SheetName").PivotTable("PivotName")` |
| Row field access (modern) | `CurrentRow.ByField("ColumnName")` or `CurrentRow.ByIndex(0)` (0-based) |
| `ExcelForEachRowX` | Two args: `Argument1` (`ue:CurrentRowQuickHandle` `"CurrentRow"`) + `Argument2` (`x:Int32` `"CurrentIndex"`) |
| `ForEachSheetX` | Two args: `Argument1` (`ue:WorksheetQuickHandle` `"CurrentSheet"`) + `Argument2` (`x:Int32` `"CurrentIndex"`); `CurrentSheet.Name` for sheet name |
| Filter sub-namespace | Add `xmlns:ueabf="clr-namespace:UiPath.Excel.Activities.Business.Filter;assembly=UiPath.Excel.Activities"` for `FilterX`, `FilterPivotTableX` |
| Chart sub-namespace | Add `xmlns:ueabc="clr-namespace:UiPath.Excel.Activities.Business.ChartModifications;assembly=UiPath.Excel.Activities"` for `UpdateChartX` modifications |
| Handle variable types | `ue:ISheetRef` (InsertSheetX output), `ue:IChartRef` (InsertExcelChartX output) |
| Classic standalone | No scope — `WorkbookPath` on each activity; set `WorkbookPathResource="{x:Null}"` |
| `ForEachRow` (classic) | One arg: `DelegateInArgument x:TypeArguments="sd:DataRow" Name="CurrentRow"` |
| Full XAML | Always use `uip rpa get-default-activity-xaml --use-studio` for complete activity XAML |

## Common Pitfalls

- Classic activities: `WorkbookPath` and `WorkbookPathResource` are mutually exclusive. Set the unused one to `{x:Null}`.
- Modern activities must always be nested inside `ExcelApplicationCard`.
