# Get Queue Items

`UiPath.Core.Activities.GetQueueItems`

Retrieves a list of transactions from an indicated queue, according to multiple filters, such as creation date, priority, state and reference.

**Package:** `UiPath.System.Activities`
**Category:** Queues

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `QueueName` | Queue name | InArgument | `string` | Yes | — | The name of the queue from which to retrieve items. |
| `Filter` | Filter | InArgument | `string` | No | null | An OData filter expression string applied to the query. Used when `FilterBuilder` is not active. |
| `Skip` | Skip | InArgument | `int` | No | — | The number of items to skip for pagination. |
| `Top` | Top | InArgument | `int` | No | — | The maximum number of items to return. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `FilterBuilder` | Filter Builder | `QueueItemFilterSettings` | null | A structured filter built using the visual Filter Builder widget. Supports filtering by Status, Priority, Reference, Duration, and date fields. |
| `FilterByCurrentRobot` | Filter By Current Robot | `bool` | false | When true, only returns items processed by the current robot. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `IEnumerable<QueueItem>` | The list of queue items matching the specified filters. |

## Valid Configurations

- Either the `Filter` (OData string) or `FilterBuilder` (visual widget) may be used to apply filter criteria. The designer provides a toggle to switch between the two modes.
- `FilterBuilder` supports the following criteria fields: **Status**, **Priority**, **Reference**, **Duration**, **CreationTime**, **StartProcessing**, **EndProcessing**.
- `Skip` and `Top` provide pagination. Use them together to page through large result sets.

### Enum Reference

**QueueItemFilterCriteria** (available in FilterBuilder)

| Criteria | Supported Operators |
|----------|---------------------|
| `Status` | Equals, NotEquals, OneOf, OneOfVariable |
| `Priority` | Equals, NotEquals, EqualsVariable |
| `Reference` | Equals, StartsWith, Contains, EndsWith |
| `Duration` | LessThan, MoreThan, LessThanOrEqual, MoreThanOrEqual |
| `CreationTime` | OlderThan, NewerThan, OlderThanOrEqual, NewerThanOrEqual |
| `StartProcessing` | OlderThan, NewerThan, OlderThanOrEqual, NewerThanOrEqual |
| `EndProcessing` | OlderThan, NewerThan, OlderThanOrEqual, NewerThanOrEqual |

## XAML Example

```xml
<ui:GetQueueItems
    QueueName="&quot;InvoiceProcessing&quot;"
    Top="[50]"
    Result="[queueItems]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

- Requires an active Orchestrator connection. The robot must be connected to Orchestrator at runtime.
- This activity retrieves queue items for reporting or inspection purposes. It does not change the status of items.
- The legacy filter properties (`Duration`, `From`, `To`, `Priority`, `QueueItemStates`, `FilterStrategy`, `Reference`) are hidden in the designer. Existing workflows using those properties have their values automatically imported into `FilterBuilder` on first open.
- `FolderPath` is an advanced/hidden property that overrides the Orchestrator folder resolved from the robot context.
