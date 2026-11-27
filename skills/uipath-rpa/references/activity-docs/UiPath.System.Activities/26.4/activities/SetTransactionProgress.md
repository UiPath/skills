# Set Transaction Progress

`UiPath.Core.Activities.SetTransactionProgress`

Helps you create custom progress statuses for your In Progress transactions.

**Package:** `UiPath.System.Activities`
**Category:** Queues

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `TransactionItem` | Transaction Item | InArgument | `QueueItem` | Yes | — | The transaction item whose progress is to be updated. Must be In Progress. |
| `Progress` | Progress | InArgument | `string` | Yes | `""` | A free-text string describing the current processing stage. Visible in the Orchestrator queue item details. |
| `FolderPath` | Folder Path | InArgument | `string` | No | — | The Orchestrator folder path to use. Overrides the robot's default folder. |

## XAML Example

```xml
<ui:SetTransactionProgress
    TransactionItem="[transactionItem]"
    Progress="&quot;Extracting invoice data&quot;"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

- Requires an active Orchestrator connection. The robot must be connected to Orchestrator at runtime.
- The `TransactionItem` must have status **In Progress**.
- This activity does not change the transaction's status — it only updates the progress string visible in Orchestrator. Use it to provide operational visibility into long-running transactions.
- There is no limit imposed by this activity on the number of times progress can be updated for a single transaction.
