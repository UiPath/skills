# Remove Duplicate Rows

`UiPath.Core.Activities.RemoveDuplicateRows`

Removes the duplicate rows from a specified DataTable, keeping only the first occurrence.

**Package:** `UiPath.System.Activities`
**Category:** Programming > DataTable

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| DataTable | Data Table | InArgument | DataTable | Yes | — | The DataTable from which duplicate rows will be removed. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| OutputDataTable | Data Table | OutArgument | DataTable | A new DataTable containing only the unique rows, preserving the first occurrence of each duplicate group. |

## Notes

- Duplicate detection considers all columns. Two rows are duplicates if every column value is equal.
- The original DataTable is not modified. The deduplicated result is placed in `OutputDataTable`.
- Row order is preserved; the first occurrence of each unique row is kept.

## XAML Example

```xml
<ui:RemoveDuplicateRows DisplayName="Remove Duplicate Rows"
                        xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:RemoveDuplicateRows.DataTable>
    <InArgument x:TypeArguments="sd:DataTable">[myDataTable]</InArgument>
  </ui:RemoveDuplicateRows.DataTable>
  <ui:RemoveDuplicateRows.OutputDataTable>
    <OutArgument x:TypeArguments="sd:DataTable">[uniqueTable]</OutArgument>
  </ui:RemoveDuplicateRows.OutputDataTable>
</ui:RemoveDuplicateRows>
```
