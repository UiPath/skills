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
| `CommitType` | Commit Type | InArgument | `CommitTypeEnum` | No | `AllOrNothing` | Controls how failures during the bulk upload are handled. Accepts a literal value or a bound expression. |

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
    QueueName="InvoiceProcessing"
    QueueItemsDataTable="[invoiceTable]"
    CommitType="AllOrNothing"
    Result="[failedItems]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Reserved Column Names

Orchestrator's bulk-add endpoint treats a small set of column names as **queue item metadata** rather than `SpecificContent`. If your DataTable contains any of these (case-insensitive match), the values populate the item's top-level fields instead of being merged into the JSON payload:

| Column name | Maps to | Type expected |
|-------------|---------|---------------|
| `Reference` | Item's `Reference` field | String |
| `Priority` | Item's `Priority` field | String (`Low` / `Normal` / `High`) |
| `DeferDate` | Item's `DeferDate` field (postpone-until) | DateTime |
| `DueDate` | Item's `DueDate` field (deadline) | DateTime |
| `Progress` | Item's `Progress` notes field | String |

Every other column lands in `SpecificContent`. If you need to store a literal field called e.g. `Reference` inside the item's specific data, rename it (e.g. `RefCode`) before calling Bulk Add.

## Type mapping (with `AutoDetectTypes`)

When `GenerateDataTable` or another producer infers typed columns (e.g. `Amount` as `Double`, `Approved` as `Boolean`), the bulk-add endpoint preserves those types in the SpecificContent JSON payload — numbers serialize as JSON numbers, booleans as JSON booleans, `DateTime` values as ISO-8601 strings. Stringly-typed columns (`AutoDetectTypes = false`) are serialized as JSON strings even when the value looks numeric.

## Notes

- Requires an active Orchestrator connection. The robot must be connected to Orchestrator at runtime.
- Each DataTable row becomes one queue item. Column names become the specific data field keys, except for the reserved names above.
- All items are created with status **New**.
- When `CommitType` is `ProcessAllIndependently`, inspect the `Result` DataTable after execution to handle failed rows.
