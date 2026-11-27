# Delete Test Data Queue Items

Deletes the specified test data queue items from Orchestrator. Accepts a list of `TestDataQueueItem` objects, typically obtained from a prior **Get Test Data Queue Items** activity.

**Class:** `UiPath.Testing.Activities.DeleteTestDataQueueItems`
**Assembly:** `UiPath.Testing.Activities`
**Category:** Testing > Test Data Queues

```xml
xmlns:uta="clr-namespace:UiPath.Testing.Activities;assembly=UiPath.Testing.Activities"
```

---

## Input

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `TestDataQueueItems` | `InArgument<List<TestDataQueueItem>>` | Yes | The list of test data queue items to delete. Typically the `TestDataQueueItems` output of **Get Test Data Queue Items**. |

## Common

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `FolderPath` | `InArgument<String>` | No | `null` | Orchestrator folder path. If not set, uses the folder of the running process. |
| `ContinueOnError` | `InArgument<Boolean>` | No | `false` | If `true`, execution continues when the activity throws an error. |
| `TimeoutMs` | `InArgument<Int32>` | No | — | Timeout in milliseconds for the Orchestrator API call. |

---

## XAML Example

```xml
<uta:DeleteTestDataQueueItems
  DisplayName="Delete Test Data Queue Items"
  TestDataQueueItems="[itemsToDelete]"
  ContinueOnError="False" />
```
