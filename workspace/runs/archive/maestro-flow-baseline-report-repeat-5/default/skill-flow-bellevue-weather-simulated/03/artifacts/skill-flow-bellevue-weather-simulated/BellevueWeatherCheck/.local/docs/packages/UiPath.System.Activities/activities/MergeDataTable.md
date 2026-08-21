# Merge Data Table

`UiPath.Core.Activities.MergeDataTable`

Merges the specified DataTable with the current DataTable, indicating whether to preserve changes and how to handle missing schema in the current DataTable.

**Package:** `UiPath.System.Activities`
**Category:** Programming > DataTable

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| Source | Source | InArgument | DataTable | Yes | — | The DataTable whose rows will be merged into the destination. |

### Input/Output

> These properties require a **variable** binding — the activity reads the incoming value and writes an updated value back. Do not use literal expressions.

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| Destination | Destination | InOutArgument | DataTable | Yes | — | The target DataTable that receives the merged rows. Modified in place. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| MissingSchemaAction | MissingSchemaAction | Property (MissingSchemaAction) | Add | Controls what happens when the source contains columns not present in the destination. See **Enum Reference** below. |

## Enum Reference

### MissingSchemaAction

This is the standard `System.Data.MissingSchemaAction` enumeration.

| Value | Description |
|-------|-------------|
| `Add` | Adds the necessary columns to the destination schema to complete the merge. This is the default. |
| `Ignore` | Ignores the extra columns. Data for those columns is discarded. |
| `Error` | Throws a `SystemException` if a schema mismatch is encountered. |
| `AddWithKey` | Adds the necessary columns and primary key information to complete the merge. |

## Notes

- The merge is performed using `DataTable.Merge(source, preserveChanges: true, missingSchemaAction)`.
- Rows from **Source** are appended to **Destination**. Existing rows in Destination are not removed.
- The **Destination** variable is updated in place via `InOutArgument`.

## XAML Example

```xml
<ui:MergeDataTable DisplayName="Merge Data Table"
                   MissingSchemaAction="Add"
                   xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:MergeDataTable.Source>
    <InArgument x:TypeArguments="sd:DataTable">[sourceTable]</InArgument>
  </ui:MergeDataTable.Source>
  <ui:MergeDataTable.Destination>
    <InOutArgument x:TypeArguments="sd:DataTable">[destinationTable]</InOutArgument>
  </ui:MergeDataTable.Destination>
</ui:MergeDataTable>
```
