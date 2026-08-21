# Get Row Item

`UiPath.Core.Activities.GetRowItem`

Gets a value from a DataRow variable according to a specified column.

**Package:** `UiPath.System.Activities`
**Category:** Programming > DataTable

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| Row | Row | InArgument | DataRow | Yes | — | The DataRow from which to read the value. |
| ColumnName | Column Name | InArgument | String | No* | — | The name of the column whose value to retrieve. |
| ColumnIndex | Column Number | InArgument | Int32 | No* | — | The zero-based index of the column whose value to retrieve. |

\* One of `ColumnName` or `ColumnIndex` should be provided to identify the target cell. `Column` (a DataColumn object) is a third option available in the source but hidden in the designer (`isVisible: false`).

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| Value | Value | OutArgument | Object | The value of the cell at the specified column in the given row. The type is `Object`; cast as needed. |

## Notes

- `Column` (DataColumn object overload) is present in the activity source but hidden in the designer (`isVisible: false`). Use `ColumnName` or `ColumnIndex` instead.
- The returned `Value` is typed as `Object`. Use `.ToString()` or `CType(Value, T)` / `DirectCast` to convert to the desired type.
- This activity does not support a typed `TypeArgument` at runtime; the value is always returned as `Object`.

## XAML Example

```xml
<!-- Get value by column name -->
<ui:GetRowItem DisplayName="Get Row Item"
               xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:GetRowItem.Row>
    <InArgument x:TypeArguments="sd:DataRow">[CurrentRow]</InArgument>
  </ui:GetRowItem.Row>
  <ui:GetRowItem.ColumnName>
    <InArgument x:TypeArguments="x:String">"FirstName"</InArgument>
  </ui:GetRowItem.ColumnName>
  <ui:GetRowItem.Value>
    <OutArgument x:TypeArguments="x:Object">[cellValue]</OutArgument>
  </ui:GetRowItem.Value>
</ui:GetRowItem>

<!-- Get value by column index -->
<ui:GetRowItem DisplayName="Get Row Item"
               xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:GetRowItem.Row>
    <InArgument x:TypeArguments="sd:DataRow">[CurrentRow]</InArgument>
  </ui:GetRowItem.Row>
  <ui:GetRowItem.ColumnIndex>
    <InArgument x:TypeArguments="x:Int32">0</InArgument>
  </ui:GetRowItem.ColumnIndex>
  <ui:GetRowItem.Value>
    <OutArgument x:TypeArguments="x:Object">[cellValue]</OutArgument>
  </ui:GetRowItem.Value>
</ui:GetRowItem>
```
