# New Item Added to Queue

`UiPath.Core.Activities.QueueTrigger`

Start a job when a new item is added to the specified queue.

**Package:** `UiPath.System.Activities`
**Category:** Triggers

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `QueueName` | Queue name | Property | `string` | Yes | — | The name of the Orchestrator queue used to trigger the job. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `FolderPath` | Folder Path | `string` | `null` | The Orchestrator folder containing the queue. Leave empty to use the folder of the current process. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `TransactionItem` | Transaction Item | OutArgument | `QueueItem` | The new queue item that triggered the job. |
| `ExtractedQueueItem` | Specific Data | OutArgument | `object` | The specific data payload extracted from the queue item. |

## XAML Example

```xml
<ui:QueueTrigger
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="New Item Added to Queue"
    QueueName="InvoiceProcessingQueue"
    TransactionItem="{x:Reference transactionItem}" />
```

## Notes

- **Type: integration trigger.** `uip rpa activities find` returns `isTrigger: true, triggerType: "integration"` (Orchestrator-native queue subscription — no IS `ConnectionId` required, though the robot must be connected to Orchestrator at runtime).
- **Placement: strict.** Place `New Item Added to Queue` as the first activity in the workflow's root `Sequence`. Do **NOT** wrap in `ui:TriggerScope`. The handler — the transaction processing logic — is the rest of the `Sequence` that follows. When the package is published to Orchestrator, this trigger is detected and a Queue Trigger can be created from it.
- See [trigger-pattern-guide.md](../../../../trigger-pattern-guide.md) for the full placement contract.
- Requires an active Orchestrator connection. The robot must be connected to Orchestrator and the specified queue must exist in the configured folder.
- `TransactionItem` gives access to the full `QueueItem` object including all metadata, `ExtractedQueueItem` gives direct access to the item's specific data.
- The `FolderPath` property supports Orchestrator modern folder paths (e.g., `Finance/Invoices`).
