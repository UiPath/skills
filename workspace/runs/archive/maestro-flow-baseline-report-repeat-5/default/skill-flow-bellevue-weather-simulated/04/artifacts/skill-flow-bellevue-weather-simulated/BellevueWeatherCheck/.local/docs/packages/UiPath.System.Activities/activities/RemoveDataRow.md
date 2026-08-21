# Remove Data Row

`UiPath.Core.Activities.RemoveDataRow`

Removes a DataRow from a specified DataTable.

**Package:** `UiPath.System.Activities`
**Category:** Programming > DataTable

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| Row | Row | InArgument | DataRow | Yes* | — | The DataRow object to remove from the DataTable. Mutually exclusive with **Row Index**. |
| RowIndex | Row Index | InArgument | Int32 | Yes* | — | The zero-based index of the row to remove. Mutually exclusive with **Row**. |

### Input/Output

> These properties require a **variable** binding — the activity reads the incoming value and writes an updated value back. Do not use literal expressions.

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| DataTable | Data Table | InOutArgument | DataTable | Yes | — | The DataTable from which the row will be removed. The variable is updated in place. |

\* Exactly one of `Row` or `RowIndex` must be provided (overload groups).

## Valid Configurations

| Mode | Required properties |
|------|-------------------|
| Remove by DataRow | `DataTable` + `Row` |
| Remove by index | `DataTable` + `RowIndex` |

## XAML Example

```xml
<!-- Remove by DataRow object -->
<ui:RemoveDataRow DisplayName="Remove Data Row"
                  xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:RemoveDataRow.DataTable>
    <InOutArgument x:TypeArguments="sd:DataTable">[myDataTable]</InOutArgument>
  </ui:RemoveDataRow.DataTable>
  <ui:RemoveDataRow.Row>
    <InArgument x:TypeArguments="sd:DataRow">[rowToRemove]</InArgument>
  </ui:RemoveDataRow.Row>
</ui:RemoveDataRow>

<!-- Remove by index -->
<ui:RemoveDataRow DisplayName="Remove Data Row"
                  xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:RemoveDataRow.DataTable>
    <InOutArgument x:TypeArguments="sd:DataTable">[myDataTable]</InOutArgument>
  </ui:RemoveDataRow.DataTable>
  <ui:RemoveDataRow.RowIndex>
    <InArgument x:TypeArguments="x:Int32">[0]</InArgument>
  </ui:RemoveDataRow.RowIndex>
</ui:RemoveDataRow>
```
