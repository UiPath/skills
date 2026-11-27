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
| `Reference` | Reference | InArgument | `string` | No | null | An external reference tag for the queue item. |
| `ItemInformationCollection` | Item Collection | InArgument | `Dictionary<string, object>` | No | null | A variable dictionary containing the item's specific data. Used when item data is bound at runtime. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Priority` | Priority | `QueueItemPriority` | Normal | The priority of the queue item. |
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

```xml
<ui:AddQueueItem
    QueueType="&quot;InvoiceProcessing&quot;"
    Priority="Normal"
    Reference="&quot;INV-2024-001&quot;"
    DueDate="[DateTime.Now.AddDays(1)]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

- Requires an active Orchestrator connection. The robot must be connected to Orchestrator at runtime.
- The item is created with status **New**. To immediately begin processing, use **Add Transaction Item** instead.
- `FolderPath` is an advanced/hidden property that overrides the Orchestrator folder resolved from the robot context.
- `ServiceBaseAddress` is deprecated and ignored.
