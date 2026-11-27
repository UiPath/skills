# Add Test Data Queue Item

Adds a single test data item to a Test Data Queue in Orchestrator. The item is defined as a key-value dictionary of field names to expression values (`ItemInformation`). Requires an Orchestrator instance.

**Class:** `UiPath.Testing.Activities.NewAddTestDataQueueItem`
**Assembly:** `UiPath.Testing.Activities`
**Category:** Testing > Test Data Queues

```xml
xmlns:uta="clr-namespace:UiPath.Testing.Activities;assembly=UiPath.Testing.Activities"
```

---

## Input

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `QueueName` | `InArgument<String>` | Yes | The name of the Test Data Queue to add the item to. |
| `ItemInformation` | `Dictionary<String, InArgument>` | Yes | Key-value pairs representing the item fields and their values. Keys must match the queue's column schema. |

## Common

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `FolderPath` | `InArgument<String>` | No | `null` | Orchestrator folder path. If not set, uses the folder of the running process. |
| `ContinueOnError` | `InArgument<Boolean>` | No | `false` | If `true`, execution continues when the activity throws an error. |
| `TimeoutMs` | `InArgument<Int32>` | No | — | Timeout in milliseconds for the Orchestrator API call. |

---

## XAML Example

```xml
<uta:NewAddTestDataQueueItem
  DisplayName="Add Test Data Queue Item"
  QueueName="&quot;MyTestQueue&quot;"
  ContinueOnError="False" />
```

> **Note:** `ItemInformation` is configured through the activity designer's key-value editor. In XAML it is represented as a child collection — use the designer to configure individual fields.
