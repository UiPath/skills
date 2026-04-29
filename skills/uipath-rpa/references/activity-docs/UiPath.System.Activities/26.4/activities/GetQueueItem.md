# Get Transaction Item

`UiPath.Core.Activities.GetQueueItem`

Gets an item from the queue so that you can process it (start the transaction) and sets its status to In Progress.

**Package:** `UiPath.System.Activities`
**Category:** Queues

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `QueueType` | Queue name | InArgument | `string` | Yes | — | The name of the queue from which to retrieve the next item. |
| `Reference` | Reference | InArgument | `string` | No | null | Filters retrieved items by reference value. Used together with `FilterStrategy`. |
| `FolderPath` | Folder Path | InArgument | `string` | No | null | The Orchestrator folder path to use. Overrides the robot's default folder. |
| `TimeoutMS` | Timeout (milliseconds) | InArgument | `int` | No | — | The maximum time to wait for the activity to complete before throwing an error. |
| `ContinueOnError` | Continue On Error | InArgument | `bool` | No | false | When true, execution continues even if the activity throws an error. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `FilterStrategy` | Filter Strategy | `ReferenceFilterStrategy` | StartsWith | Determines how the `Reference` filter is applied. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `TransactionItem` | Transaction Item | OutArgument | `QueueItem` | The retrieved queue item, now set to In Progress. Returns null if the queue is empty. |
| `SpecificData` | Specific Data | OutArgument | `object` | The raw specific data payload of the retrieved queue item. |

## Valid Configurations

- If the queue contains no items with status **New**, `TransactionItem` is set to null and no error is thrown.
- `Reference` and `FilterStrategy` work together: only items whose reference matches the filter are considered.

### Enum Reference

**ReferenceFilterStrategy**

| Value | Description |
|-------|-------------|
| `StartsWith` | The item's reference must start with the specified value. |
| `Equals` | The item's reference must exactly match the specified value. |

## XAML Example

```xml
<ui:GetQueueItem
    QueueType="&quot;InvoiceProcessing&quot;"
    TransactionItem="[transactionItem]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

- Requires an active Orchestrator connection. The robot must be connected to Orchestrator at runtime.
- The retrieved item is immediately set to status **In Progress**. Use **Set Transaction Status** to mark it as Successful or Failed after processing.
- If the queue is empty, `TransactionItem` is null. Always null-check the output before processing.
- Use **Wait Queue Item** if you need the activity to block until an item becomes available.
