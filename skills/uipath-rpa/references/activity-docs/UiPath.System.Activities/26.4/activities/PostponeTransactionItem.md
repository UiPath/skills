# Postpone Transaction Item

`UiPath.Core.Activities.PostponeTransactionItem`

Adds time parameters between which a transaction must be processed (not before Postpone Date and no later than Deadline Date).

**Package:** `UiPath.System.Activities`
**Category:** Queues

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `TransactionItem` | Transaction Item | InArgument | `QueueItem` | Yes | — | The transaction item to postpone. Must be an item currently In Progress. |
| `DeferDate` | Postpone | InArgument | `DateTime` | Yes | null | The date after which the queue item may be processed. The item will not be picked up before this date. |
| `DueDate` | Deadline | InArgument | `DateTime` | No | null | The date before which the queue item should be processed. |
| `FolderPath` | Folder Path | InArgument | `string` | No | — | The Orchestrator folder path to use. Overrides the robot's default folder. |
| `TimeoutMS` | Timeout (milliseconds) | InArgument | `int` | No | — | The maximum time in milliseconds to wait for the activity to complete before throwing an error. |
| `ContinueOnError` | Continue On Error | InArgument | `bool` | No | false | When true, execution continues even if the activity throws an error. |

## XAML Example

```xml
<ui:PostponeTransactionItem
    TransactionItem="[transactionItem]"
    DeferDate="[DateTime.Now.AddHours(2)]"
    DueDate="[DateTime.Now.AddDays(1)]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

- Requires an active Orchestrator connection. The robot must be connected to Orchestrator at runtime.
- The `TransactionItem` must have status **In Progress**. This activity is typically called when a transient condition prevents immediate processing (for example, a downstream system is temporarily unavailable).
- After being postponed, the item's status is changed back to **New** in Orchestrator with the specified scheduling window applied. It will not be picked up again until after `DeferDate`.
- `DeferDate` is required. `DueDate` is optional but recommended to prevent indefinite deferral.
