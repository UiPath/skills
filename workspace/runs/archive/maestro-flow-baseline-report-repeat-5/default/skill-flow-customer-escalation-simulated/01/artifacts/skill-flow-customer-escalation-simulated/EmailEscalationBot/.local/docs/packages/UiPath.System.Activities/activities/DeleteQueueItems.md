# Delete Queue Items

`UiPath.Core.Activities.DeleteQueueItems`

Deletes items with the New state from a specified queue.

**Package:** `UiPath.System.Activities`
**Category:** Queues

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FolderPath` | Folder Path | InArgument | `string` | No | — | The Orchestrator folder path to use. Overrides the robot's default folder. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `QueueItems` | Queue Items | `InArgument<IEnumerable<QueueItem>>` | — | The collection of queue items to delete. Only items with status **New** can be deleted. |

## XAML Example

```xml
<ui:DeleteQueueItems
    QueueItems="[itemsToDelete]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

- Requires an active Orchestrator connection. The robot must be connected to Orchestrator at runtime.
- Only queue items with status **New** can be deleted. Attempting to delete items in other states (In Progress, Successful, Failed, etc.) will result in an error.
- Use **Get Queue Items** to retrieve the collection of items to pass to this activity.
- `FolderPath` overrides the Orchestrator folder context for the delete operation.
