# Add Data Column

`UiPath.Core.Activities.AddDataColumn`

Adds a DataColumn to a specified DataTable.

**Package:** `UiPath.System.Activities`
**Category:** Programming > DataTable

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| DataTable | Data Table | InArgument | DataTable | Yes | — | The DataTable to which the column will be added. |
| ColumnName | Column Name | InArgument | String | Yes* | — | The name of the new column to create. Mutually exclusive with **Column**. Used when defining a new column by name. |
| Column | Column | InArgument | DataColumn | Yes* | — | An existing DataColumn object to add directly. Mutually exclusive with **Column Name**. |

\* Exactly one of `ColumnName` or `Column` must be provided (overload groups).

### Configuration

When creating a new column by **Column Name**, the following options are available:

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| AllowDBNull | Allow DB Null | InArgument\<Boolean\> | true | Whether the column allows null/DBNull values. |
| AutoIncrement | Auto Increment | InArgument\<Boolean\> | false | Whether the column value auto-increments. Applicable only to numeric types. When true, **Default Value** is hidden. |
| DefaultValue | Default Value | InArgument\<T\> | — | Default value for new rows. Hidden when **Auto Increment** is true. |
| MaxLength | Max Length | InArgument\<Int32\> | 100 | Maximum character length. Visible only when the column type is `String`. |
| Unique | Unique | InArgument\<Boolean\> | false | Whether column values must be unique across all rows. |

The column's data type `T` (TypeArgument) controls which options are relevant:
- `AutoIncrement` is only applicable to numeric types (e.g. `Int32`, `Int64`).
- `MaxLength` is only visible when `T` is `String`.
- When `Column` (existing DataColumn object) is used, all Options properties are ignored.

## Valid Configurations

| Mode | Required properties |
|------|-------------------|
| New column by name | `DataTable` + `ColumnName` (+ optional Options) |
| Existing column object | `DataTable` + `Column` |

## XAML Example

```xml
<!-- New String column with name -->
<ui:AddDataColumn x:TypeArguments="x:String"
                  DisplayName="Add Data Column"
                  xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:AddDataColumn.DataTable>
    <InArgument x:TypeArguments="sd:DataTable">[myDataTable]</InArgument>
  </ui:AddDataColumn.DataTable>
  <ui:AddDataColumn.ColumnName>
    <InArgument x:TypeArguments="x:String">"Department"</InArgument>
  </ui:AddDataColumn.ColumnName>
  <ui:AddDataColumn.AllowDBNull>
    <InArgument x:TypeArguments="x:Boolean">True</InArgument>
  </ui:AddDataColumn.AllowDBNull>
  <ui:AddDataColumn.MaxLength>
    <InArgument x:TypeArguments="x:Int32">100</InArgument>
  </ui:AddDataColumn.MaxLength>
</ui:AddDataColumn>
```
