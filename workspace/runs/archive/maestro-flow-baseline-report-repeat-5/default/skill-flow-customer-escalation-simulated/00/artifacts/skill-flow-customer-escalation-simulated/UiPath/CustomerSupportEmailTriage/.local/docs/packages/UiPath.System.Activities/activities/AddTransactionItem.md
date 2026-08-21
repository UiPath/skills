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
| `TransactionInformationVariable` | Transaction information variable | InArgument | `Dictionary<string, object>` | No | null | A bound dictionary expression supplying the transaction's specific data at runtime. Mutually exclusive with `TransactionInformation` — the designer surfaces both via a menu action; the runtime prefers the variable when it has a bound expression. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `TransactionInformation` | Transaction information | `Dictionary<string, InArgument>` | empty dict | The inline key-value collection of specific data for the transaction item. Used when `TransactionInformationVariable` is not bound. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `TransactionItem` | Transaction item | OutArgument | `QueueItem` | The queue item that was created and immediately set to In Progress. |

## Valid Configurations

- Supply transaction data via **either** `TransactionInformation` (inline key/value editor in the designer) **or** `TransactionInformationVariable` (a `Dictionary<string, object>` expression). The two are presented as alternatives in the designer through a menu action.
- If both are set, `TransactionInformationVariable` wins — the inline dictionary is ignored. The selection is by *binding* (is the variable's expression set?), not by *value* (the variable evaluating to `null` does not fall back to the dict).
- If neither is set, `SpecificContent` is posted as an empty object (`{}`). This is **intentional** — it mirrors the pre-existing behaviour of passing an empty `TransactionInformation` dictionary and is a valid use-case when no specific data is required for the queue item.

## XAML Example

```xml
<ui:AddTransactionItem
    QueueType="InvoiceQueue"
    Reference="TXN-001"
    TransactionInformationVariable="[transactionData]"
    TransactionItem="[transactionItem]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

- Requires an active Orchestrator connection. The robot must be connected to Orchestrator at runtime.
- Unlike **Add Queue Item**, this activity immediately sets the new item's status to **In Progress**, making it ready for processing in a single step.
- The returned `QueueItem` should be passed to **Set Transaction Status** when processing is complete.
- `ServiceBaseAddress` is deprecated and ignored.
