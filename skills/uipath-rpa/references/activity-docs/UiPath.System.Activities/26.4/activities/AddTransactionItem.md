# Add Transaction Item

`UiPath.Core.Activities.AddTransactionItem`

Adds a new item in the queue and starts a transaction. The status of the item will be set to InProgress. Returns the item as a QueueItem variable.

**Package:** `UiPath.System.Activities`
**Category:** Queues

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Reference` | Reference | InArgument | `string` | No | — | An external reference tag for the queue item. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `TransactionInformation` | Reference | `Dictionary<string, InArgument>` | null | The inline key-value collection of specific data for the transaction item. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `TransactionItem` | Transaction Item | OutArgument | `QueueItem` | The queue item that was created and immediately set to In Progress. |

## XAML Example

```xml
<ui:AddTransactionItem
    Reference="&quot;TXN-001&quot;"
    TransactionItem="[transactionItem]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

- Requires an active Orchestrator connection. The robot must be connected to Orchestrator at runtime.
- Unlike **Add Queue Item**, this activity immediately sets the new item's status to **In Progress**, making it ready for processing in a single step.
- The returned `QueueItem` should be passed to **Set Transaction Status** when processing is complete.
- `ServiceBaseAddress` is deprecated and ignored.
