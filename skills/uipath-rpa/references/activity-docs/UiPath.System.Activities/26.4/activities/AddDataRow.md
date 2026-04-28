# Add Data Row

`UiPath.Core.Activities.AddDataRow`

Adds a DataRow to a specified DataTable.

**Package:** `UiPath.System.Activities`
**Category:** Programming > DataTable

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| ArrayRow | Array Row | InArgument | Object[] | Yes* | — | An array of values whose elements map positionally to each column of the DataTable. Mutually exclusive with **Data Row**. |
| DataRow | Data Row | InArgument | DataRow | Yes* | — | An existing DataRow object to add to the DataTable. Mutually exclusive with **Array Row**. |

### Input/Output

> These properties require a **variable** binding — the activity reads the incoming value and writes an updated value back. Do not use literal expressions.

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| DataTable | Data Table | InOutArgument | DataTable | Yes | — | The DataTable to which the row will be added. The variable is updated in place. |

\* Exactly one of `ArrayRow` or `DataRow` must be provided (overload groups).

## Valid Configurations

| Mode | Required properties |
|------|-------------------|
| Add by array | `DataTable` + `ArrayRow` |
| Add by DataRow | `DataTable` + `DataRow` |

## XAML Example

```xml
<!-- Using ArrayRow -->
<ui:AddDataRow DisplayName="Add Data Row"
               xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:AddDataRow.DataTable>
    <InOutArgument x:TypeArguments="sd:DataTable">[myDataTable]</InOutArgument>
  </ui:AddDataRow.DataTable>
  <ui:AddDataRow.ArrayRow>
    <InArgument x:TypeArguments="x:Object[]">[New Object() {"Alice", 30, "HR"}]</InArgument>
  </ui:AddDataRow.ArrayRow>
</ui:AddDataRow>

<!-- Using DataRow -->
<ui:AddDataRow DisplayName="Add Data Row"
               xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:AddDataRow.DataTable>
    <InOutArgument x:TypeArguments="sd:DataTable">[myDataTable]</InOutArgument>
  </ui:AddDataRow.DataTable>
  <ui:AddDataRow.DataRow>
    <InArgument x:TypeArguments="sd:DataRow">[myDataRow]</InArgument>
  </ui:AddDataRow.DataRow>
</ui:AddDataRow>
```
