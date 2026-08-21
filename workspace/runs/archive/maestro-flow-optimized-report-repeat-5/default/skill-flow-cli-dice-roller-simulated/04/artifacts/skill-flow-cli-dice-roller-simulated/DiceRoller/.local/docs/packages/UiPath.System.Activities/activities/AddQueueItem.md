# Add Queue Item

`UiPath.Core.Activities.AddQueueItem`

Adds a new item in the queue. The status of the item will be New.

**Package:** `UiPath.System.Activities`
**Category:** Queues

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `QueueType` | Queue name | InArgument | `string` | Yes | — | The name of the queue to add the item to. |
| `DeferDate` | Postpone | InArgument | `DateTime` | No | null | The earliest date and time after which the item may be processed. |
| `DueDate` | Deadline | InArgument | `DateTime` | No | null | The latest date and time by which the item should be processed. |
| `Priority` | Priority | InArgument | `QueueItemPriority` | No | `Normal` | The priority of the queue item. Accepts a literal `QueueItemPriority` value or a bound expression. |
| `Reference` | Reference | InArgument | `string` | No | null | An external reference tag for the queue item. |
| `ItemInformationCollection` | Item Information Collection | InArgument | `Dictionary<string, object>` | No | null | A variable dictionary containing the item's specific data. Used when item data is bound at runtime. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ItemInformation` | Item Information | `Dictionary<string, InArgument>` | — | The inline key-value collection of specific data for the queue item. Keys can be auto-populated from the Orchestrator queue schema. |

## Valid Configurations

- Either `ItemInformation` (inline dictionary) or `ItemInformationCollection` (variable) may be used to supply specific data. Both can be set simultaneously and their values are merged at runtime.
- When `QueueType` is set to a literal queue name, the designer offers a **Refresh Arguments** menu action on `ItemInformation` to auto-populate keys from the Orchestrator queue JSON schema.

### Enum Reference

**QueueItemPriority**

| Value | Description |
|-------|-------------|
| `Low` | Lower than normal priority. |
| `Normal` | Default priority. |
| `High` | Higher than normal priority. |

## XAML Example

Minimal — literal queue name, no specific data:

```xml
<ui:AddQueueItem
    QueueType="InvoiceProcessing"
    Priority="Normal"
    Reference="INV-2024-001"
    DueDate="[DateTime.Now.AddDays(1)]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

With `ItemInformation` carrying mixed-type specific data (string, double, boolean, DateTime):

```xml
<ui:AddQueueItem
    QueueType="InvoiceProcessing"
    Priority="High"
    Reference="INV-2024-002"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib">
  <ui:AddQueueItem.ItemInformation>
    <InArgument x:TypeArguments="x:String" x:Key="InvoiceNumber">"INV-2024-002"</InArgument>
    <InArgument x:TypeArguments="x:Double" x:Key="Amount">1500.0</InArgument>
    <InArgument x:TypeArguments="x:Boolean" x:Key="Approved">True</InArgument>
    <InArgument x:TypeArguments="s:DateTime" x:Key="InvoiceDate">[DateTime.Today]</InArgument>
  </ui:AddQueueItem.ItemInformation>
</ui:AddQueueItem>
```

Each entry's `x:TypeArguments` determines how Orchestrator serializes the field in the item's `SpecificContent`: typed numbers and booleans are preserved as JSON numbers/booleans, and `DateTime` values serialize as ISO-8601 strings. Use `s:DateTime` (not `x:DateTime`) for `DateTime` — see [Postpone Transaction Item](PostponeTransactionItem.md) for the underlying reason.

## Common Runtime Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `OrchestratorHttpException: 404 Not Found — "<QueueName>" does not exist. Error code: 1002` | The queue named in `QueueType` does not exist in the resolved Orchestrator folder. The activity does **not** auto-create queues. | Create the queue in Orchestrator first, or confirm that `FolderPath` (explicit or robot-inherited) points to the folder containing the queue. |
| `OrchestratorHttpException: 409 Conflict — Reference already exists` | A queue item with the same `Reference` already exists and the queue is configured for **Unique References**. | Either use a unique reference for each item or disable Unique References on the queue in Orchestrator. |
| `OrchestratorHttpException: 401 Unauthorized` | The robot is not connected to Orchestrator, or its credentials no longer have permission to write to the queue. | Re-authenticate the robot and verify it has the **Queues: Edit** role on the folder. |

## Notes

- Requires an active Orchestrator connection. The robot must be connected to Orchestrator at runtime.
- The item is created with status **New**. To immediately begin processing, use **Add Transaction Item** instead.
- `FolderPath` is an advanced/hidden property that overrides the Orchestrator folder resolved from the robot context.
- `ServiceBaseAddress` is deprecated and ignored.
