# Set Transaction Status

`UiPath.Core.Activities.SetTransactionStatus`

Sets the status of a transaction item to Failed or Successful.

**Package:** `UiPath.System.Activities`
**Category:** Queues

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `TransactionItem` | Transaction Item | InArgument | `QueueItem` | Yes | — | The transaction item whose status is to be updated. Must be In Progress. |
| `Status` | Status | InArgument | `ProcessingStatus` | No | Successful | The new status to assign to the transaction item. |
| `Details` | Details | InArgument | `string` | No | null | Additional details about the failure. Visible in the Orchestrator queue item details. Only relevant when `Status` is Failed. |
| `ErrorType` | ErrorType | InArgument | `ErrorType` | No | Business | The category of failure. Only relevant when `Status` is Failed. |
| `Reason` | Reason | InArgument | `string` | No | — | The reason for the failure. Becomes required when `Status` is set to Failed. |
| `AssociatedFilePath` | AssociatedFilePath | InArgument | `string` | No | null | Path to a file to attach to the failed transaction in Orchestrator. |
| `TimeoutMS` | Timeout (milliseconds) | InArgument | `int` | No | — | The maximum time in milliseconds to wait before throwing an error. |
| `ContinueOnError` | Continue On Error | InArgument | `bool` | No | false | When true, execution continues even if the activity throws an error. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Output` | Output | `Dictionary<string, InArgument>` | — | Inline key-value output data to attach to the transaction record in Orchestrator. |
| `OutputVariable` | Output variable | `InArgument<Dictionary<string, object>>` | null | A variable dictionary of output data. Alternative to the inline `Output` dictionary. Toggle via the menu action on `Output`. |
| `Analytics` | Analytics | `Dictionary<string, InArgument>` | — | Inline key-value analytics data to attach to the transaction record. |
| `AnalyticsVariable` | Analytics variable | `InArgument<Dictionary<string, object>>` | null | A variable dictionary of analytics data. Alternative to the inline `Analytics` dictionary. Toggle via the menu action on `Analytics`. |

## Valid Configurations

- `Output` and `OutputVariable` are mutually exclusive display modes for the same underlying data. The designer menu action on `Output` ("Use Expression") switches to `OutputVariable`, and vice versa.
- `Analytics` and `AnalyticsVariable` follow the same mutual exclusion pattern.
- `Reason` becomes required when `Status` is `Failed`.
- `Details`, `ErrorType`, `Reason`, and `AssociatedFilePath` are only meaningful when `Status` is `Failed`. They appear under the **Transaction Error** property category.

### Enum Reference

**ProcessingStatus**

| Value | Description |
|-------|-------------|
| `Successful` | The transaction was processed successfully. |
| `Failed` | The transaction failed. Requires `Reason` and optionally `ErrorType` and `Details`. |

**ErrorType**

| Value | Description |
|-------|-------------|
| `Business` | A business logic error (e.g. invalid invoice data). Does not trigger automatic retry by default. |
| `Application` | A technical/application error (e.g. file not found, network timeout). Triggers automatic retry according to the queue's retry settings in Orchestrator. |

## XAML Example

```xml
<!-- Successful -->
<ui:SetTransactionStatus
    TransactionItem="[transactionItem]"
    Status="Successful"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />

<!-- Failed with Application error -->
<ui:SetTransactionStatus
    TransactionItem="[transactionItem]"
    Status="Failed"
    ErrorType="Application"
    Reason="&quot;Could not connect to SAP&quot;"
    Details="[exception.Message]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

- Requires an active Orchestrator connection. The robot must be connected to Orchestrator at runtime.
- The `TransactionItem` must have status **In Progress**, typically obtained from **Get Transaction Item**, **Add Transaction Item**, or **Wait Queue Item**.
- Choosing `ErrorType.Application` causes Orchestrator to re-queue the item for retry (subject to the queue's maximum retry count configuration).
- Choosing `ErrorType.Business` marks the item as permanently failed with no automatic retry.
- `FolderPath` is an advanced/hidden property that overrides the Orchestrator folder context.
