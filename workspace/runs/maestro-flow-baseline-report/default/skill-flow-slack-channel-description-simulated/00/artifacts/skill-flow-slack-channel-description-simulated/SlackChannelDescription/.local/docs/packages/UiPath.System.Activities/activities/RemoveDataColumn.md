# Remove Data Column

`UiPath.Core.Activities.RemoveDataColumn`

Removes a DataColumn from a specified DataTable.

**Package:** `UiPath.System.Activities`
**Category:** Programming > DataTable

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| ColumnName | Column Name | InArgument | String | Yes* | — | The name of the column to remove. Mutually exclusive with **Column Number**. |
| ColumnIndex | Column Number | InArgument | Int32 | Yes* | — | The zero-based index of the column to remove. Mutually exclusive with **Column Name**. |

### Input/Output

> These properties require a **variable** binding — the activity reads the incoming value and writes an updated value back. Do not use literal expressions.

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| DataTable | From Data Table | InOutArgument | DataTable | Yes | — | The DataTable from which the column will be removed. Modified in place. |

\* Exactly one of `ColumnName` (overload group `ColumnName`) or `ColumnIndex` (overload group `ColumnIndex`) must be provided. `Column` (DataColumn object) exists in the source but is hidden in the designer (`isVisible: false`).

## Valid Configurations

| Mode | Required properties |
|------|-------------------|
| Remove by column name | `DataTable` + `ColumnName` |
| Remove by column index | `DataTable` + `ColumnIndex` |

## Notes

- `Column` (DataColumn object overload) is present in the activity source but hidden in the designer (`isVisible: false`). Use `ColumnName` or `ColumnIndex` instead.
- The DataTable variable is modified in place via `InOutArgument`. All rows lose the removed column's data.
- Removing a column that does not exist throws an exception at runtime.

## XAML Example

```xml
<!-- Remove column by name -->
<ui:RemoveDataColumn DisplayName="Remove Data Column"
                     xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:RemoveDataColumn.DataTable>
    <InOutArgument x:TypeArguments="sd:DataTable">[myDataTable]</InOutArgument>
  </ui:RemoveDataColumn.DataTable>
  <ui:RemoveDataColumn.ColumnName>
    <InArgument x:TypeArguments="x:String">"TempColumn"</InArgument>
  </ui:RemoveDataColumn.ColumnName>
</ui:RemoveDataColumn>

<!-- Remove column by index -->
<ui:RemoveDataColumn DisplayName="Remove Data Column"
                     xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:RemoveDataColumn.DataTable>
    <InOutArgument x:TypeArguments="sd:DataTable">[myDataTable]</InOutArgument>
  </ui:RemoveDataColumn.DataTable>
  <ui:RemoveDataColumn.ColumnIndex>
    <InArgument x:TypeArguments="x:Int32">3</InArgument>
  </ui:RemoveDataColumn.ColumnIndex>
</ui:RemoveDataColumn>
```
