# Get Test Data Queue Item

Retrieves the next available test data item from a Test Data Queue in Orchestrator and returns its fields as a `Dictionary<String, Object>`. Optionally marks the item as consumed to prevent other test cases from claiming it.

**Class:** `UiPath.Testing.Activities.GetTestDataQueueItem`
**Assembly:** `UiPath.Testing.Activities`
**Category:** Testing > Test Data Queues

```xml
xmlns:uta="clr-namespace:UiPath.Testing.Activities;assembly=UiPath.Testing.Activities"
```

---

## Input

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `QueueName` | `InArgument<String>` | Yes | — | The name of the Test Data Queue to consume an item from. |
| `MarkConsumed` | `Boolean` | No | `true` | If `true`, the retrieved item is marked as consumed in Orchestrator so it is not returned again by subsequent calls. |

## Output

| Property | Type | Description |
|----------|------|-------------|
| `Output` | `OutArgument<Dictionary<String, Object>>` | The retrieved queue item as a key-value dictionary. Keys are the field names defined in the queue schema; values are the field values cast to `Object`. |

## Common

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `FolderPath` | `InArgument<String>` | No | `null` | Orchestrator folder path. If not set, uses the folder of the running process. |
| `ContinueOnError` | `InArgument<Boolean>` | No | `false` | If `true`, execution continues when the activity throws an error. |
| `TimeoutMs` | `InArgument<Int32>` | No | — | Timeout in milliseconds for the Orchestrator API call. |

---

## XAML Example

```xml
<uta:GetTestDataQueueItem
  DisplayName="Get Test Data Queue Item"
  QueueName="&quot;MyTestQueue&quot;"
  MarkConsumed="True"
  Output="[itemData]"
  ContinueOnError="False" />
```

> After execution, access individual field values via `itemData("FieldName")`.
