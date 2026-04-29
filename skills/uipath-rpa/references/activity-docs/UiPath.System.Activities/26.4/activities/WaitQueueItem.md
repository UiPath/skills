# Wait Queue Item

`UiPath.Core.Activities.WaitQueueItem`

Waits for an item in the queue to be available so that you can process it (start the transaction) and sets its status to In Progress.

**Package:** `UiPath.System.Activities`
**Category:** Queues

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `QueueName` | Queue name | InArgument | `string` | Yes | — | The name of the queue to monitor for available items. |
| `Reference` | Reference | InArgument | `string` | No | — | Filters the item to wait for by reference value. Used together with `FilterStrategy`. |
| `PollTimeMS` | PollTime (milliseconds) | InArgument | `int` | No | — | The interval in milliseconds between polling attempts while waiting for an item. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `FilterStrategy` | Filter Strategy | `ReferenceFilterStrategy` | — | Determines how the `Reference` filter value is matched against queue item references. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `QueueItem` | The queue item that became available, now set to In Progress. |

## Valid Configurations

- `Reference` and `FilterStrategy` work together: only items whose reference matches the filter strategy are considered.
- If `PollTimeMS` is not set, a default polling interval is used.

### Enum Reference

**ReferenceFilterStrategy**

| Value | Description |
|-------|-------------|
| `StartsWith` | The item's reference must start with the specified value. |
| `Equals` | The item's reference must exactly match the specified value. |

## XAML Example

```xml
<ui:WaitQueueItem
    QueueName="&quot;InvoiceProcessing&quot;"
    PollTimeMS="[5000]"
    Result="[transactionItem]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

- Requires an active Orchestrator connection. The robot must be connected to Orchestrator at runtime.
- Unlike **Get Transaction Item**, this activity blocks execution until an item with status **New** becomes available in the queue. It will poll indefinitely unless a timeout is applied externally (e.g. via a wrapping **Parallel** or **Pick** activity).
- The returned item is immediately set to status **In Progress**. Pass it to **Set Transaction Status** when processing is complete.
- Use `PollTimeMS` to control how frequently Orchestrator is queried, balancing responsiveness against API load.
