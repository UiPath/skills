# Set Trace Status

`UiPath.Core.Activities.ProcessTracking.SetTraceStatus`

Sets the status of the current Process Trace and close it. Do not set a status if the Process Trace extends beyond this Task scope.

**Package:** `UiPath.System.Activities`
**Category:** Process Tracking

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Status` | Status | InArgument | `TraceStatus` | Yes | — | The status value to assign to the process trace, which also closes it. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `TraceGuid` | Trace | `string` | — | The identifier of the trace to update. Selected via auto-complete from traces visible in the current scope. If omitted, targets the current trace within the enclosing Process Tracking Scope. |

## XAML Example

```xml
<ui:SetTraceStatus
    xmlns:ui="clr-namespace:UiPath.Core.Activities.ProcessTracking;assembly=UiPath.System.Activities"
    DisplayName="Set Trace Status"
    TraceGuid="myTraceScope"
    Status="[TraceStatus.Completed]" />
```

## Notes

- **Set Trace Status** closes the Process Mining trace and assigns it a final outcome status.
- Use this activity only when the trace lifecycle ends within the current workflow. If the trace is expected to continue in a downstream automation (via `ExistingTrace` mode in a **Process Tracking Scope**), do not call this activity.
- `TraceGuid` is selected from traces defined by enclosing **Process Tracking Scope** activities using an auto-complete expression widget.
- `Status` accepts values from the `TraceStatus` enum provided by the UiPath.System.Activities package. Common values include `Completed`, `Failed`, and `Abandoned`.
- To set only the task outcome without closing the trace, use **Set Task Status** instead.
