# Update Row Item

`UiPath.Core.Activities.UpdateRowItem`

Assigns the specified value into the indicated column of a DataTable row.

**Package:** `UiPath.System.Activities`
**Category:** Programming > DataTable

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| Row | Row | InArgument | DataRow | Yes | — | The DataRow whose cell value will be updated. The row is modified in place within its parent DataTable. |
| Value | Value | InArgument | Object | Yes | — | The new value to write into the cell. |
| ColumnName | Column Name | InArgument | String | No* | — | The name of the column to update. |
| ColumnIndex | Column Number | InArgument | Int32 | No* | — | The zero-based index of the column to update. |

\* One of `ColumnName` or `ColumnIndex` must be provided to identify the target column.

## Notes

- The DataRow is updated in place. Because a DataRow holds a reference back to its parent DataTable, the change is reflected in the DataTable immediately without needing to re-assign it.
- `Value` is typed as `Object`. Pass any value that is compatible with the column's data type.
- There is no `Column` (DataColumn object) variant exposed in the designer for this activity.

## XAML Example

```xml
<!-- Update by column name -->
<ui:UpdateRowItem DisplayName="Update Row Item"
                  xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:UpdateRowItem.Row>
    <InArgument x:TypeArguments="sd:DataRow">[CurrentRow]</InArgument>
  </ui:UpdateRowItem.Row>
  <ui:UpdateRowItem.ColumnName>
    <InArgument x:TypeArguments="x:String">"Status"</InArgument>
  </ui:UpdateRowItem.ColumnName>
  <ui:UpdateRowItem.Value>
    <InArgument x:TypeArguments="x:Object">"Processed"</InArgument>
  </ui:UpdateRowItem.Value>
</ui:UpdateRowItem>

<!-- Update by column index -->
<ui:UpdateRowItem DisplayName="Update Row Item"
                  xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:UpdateRowItem.Row>
    <InArgument x:TypeArguments="sd:DataRow">[CurrentRow]</InArgument>
  </ui:UpdateRowItem.Row>
  <ui:UpdateRowItem.ColumnIndex>
    <InArgument x:TypeArguments="x:Int32">2</InArgument>
  </ui:UpdateRowItem.ColumnIndex>
  <ui:UpdateRowItem.Value>
    <InArgument x:TypeArguments="x:Object">[newValue]</InArgument>
  </ui:UpdateRowItem.Value>
</ui:UpdateRowItem>
```
