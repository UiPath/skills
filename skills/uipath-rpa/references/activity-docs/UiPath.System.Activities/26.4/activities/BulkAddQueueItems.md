# Bulk Add Queue Items

`UiPath.Core.Activities.BulkAddQueueItems`

Adds a collection of items from a Data Table to a queue. The status of the items will be New.

**Package:** `UiPath.System.Activities`
**Category:** Queues

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `QueueName` | Queue name | InArgument | `string` | Yes | — | The name of the queue to add items to. |
| `QueueItemsDataTable` | Data Table | InArgument | `DataTable` | Yes | — | The DataTable whose rows are uploaded as queue items. Each column becomes a specific data field. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `CommitType` | Commit Type | `CommitTypeEnum` | AllOrNothing | Controls how failures during the bulk upload are handled. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `DataTable` | A DataTable containing the rows that failed to be added to the queue. Empty when all items succeeded. |

## Valid Configurations

- The `CommitType` property controls transactional behaviour:
  - `AllOrNothing` — the entire upload is rolled back if any item fails.
  - `ProcessAllIndependently` — each item is committed independently; failed rows are returned in `Result`.

### Enum Reference

**CommitTypeEnum**

| Value | Description |
|-------|-------------|
| `AllOrNothing` | All items are added or none are. If any item fails, the whole batch is rolled back. |
| `ProcessAllIndependently` | Items are processed independently. Failed items are returned in the output DataTable. |

## XAML Example

```xml
<ui:BulkAddQueueItems
    QueueName="&quot;InvoiceProcessing&quot;"
    QueueItemsDataTable="[invoiceTable]"
    CommitType="AllOrNothing"
    Result="[failedItems]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

- Requires an active Orchestrator connection. The robot must be connected to Orchestrator at runtime.
- Each DataTable row becomes one queue item. Column names become the specific data field keys.
- All items are created with status **New**.
- When `CommitType` is `ProcessAllIndependently`, inspect the `Result` DataTable after execution to handle failed rows.
