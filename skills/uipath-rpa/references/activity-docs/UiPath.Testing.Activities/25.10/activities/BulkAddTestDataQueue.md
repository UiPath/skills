# Bulk Add Test Data Queue Items

Adds multiple test data items to a Test Data Queue in Orchestrator from a `DataTable`. Each row in the DataTable becomes one queue item; column names must match the queue's field schema.

**Class:** `UiPath.Testing.Activities.BulkAddTestDataQueue`
**Assembly:** `UiPath.Testing.Activities`
**Category:** Testing > Test Data Queues

```xml
xmlns:uta="clr-namespace:UiPath.Testing.Activities;assembly=UiPath.Testing.Activities"
```

---

## Input

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `QueueName` | `InArgument<String>` | Yes | The name of the Test Data Queue to add items to. |
| `QueueItemsDataTable` | `InArgument<DataTable>` | Yes | DataTable where each row becomes a queue item. Column headers must match the queue's field names. |

## Common

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `FolderPath` | `InArgument<String>` | No | `null` | Orchestrator folder path. If not set, uses the folder of the running process. |
| `ContinueOnError` | `InArgument<Boolean>` | No | `false` | If `true`, execution continues when the activity throws an error. |
| `TimeoutMs` | `InArgument<Int32>` | No | — | Timeout in milliseconds for the Orchestrator API call. |

---

## XAML Example

```xml
<uta:BulkAddTestDataQueue
  DisplayName="Bulk Add Test Data Queue Items"
  QueueName="&quot;MyTestQueue&quot;"
  QueueItemsDataTable="[dtItems]"
  ContinueOnError="False" />
```
