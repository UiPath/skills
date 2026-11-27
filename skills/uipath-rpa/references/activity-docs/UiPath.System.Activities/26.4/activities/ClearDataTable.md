# Clear Data Table

`UiPath.Core.Activities.ClearDataTable`

Clears the specified DataTable of all data.

**Package:** `UiPath.System.Activities`
**Category:** Programming > DataTable

## Properties

### Input/Output

> These properties require a **variable** binding — the activity reads the incoming value and writes an updated value back. Do not use literal expressions.

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| DataTable | Data Table | InOutArgument | DataTable | Yes | — | The DataTable to clear. All rows are removed; the schema (columns) is preserved. The variable is updated in place. |

## Notes

- This activity removes all rows from the DataTable but retains the column definitions.
- The DataTable variable passed in is modified directly via the `InOutArgument` binding.

## XAML Example

```xml
<ui:ClearDataTable DisplayName="Clear Data Table"
                   xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:ClearDataTable.DataTable>
    <InOutArgument x:TypeArguments="sd:DataTable">[myDataTable]</InOutArgument>
  </ui:ClearDataTable.DataTable>
</ui:ClearDataTable>
```
