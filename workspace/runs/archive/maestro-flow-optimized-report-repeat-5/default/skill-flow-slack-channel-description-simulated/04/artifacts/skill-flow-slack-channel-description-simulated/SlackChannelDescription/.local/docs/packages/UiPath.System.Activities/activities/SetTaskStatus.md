# Set Task Status

`UiPath.Core.Activities.ProcessTracking.SetTaskStatus`

Sets the status of a Task.

**Package:** `UiPath.System.Activities`
**Category:** Process Tracking

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Status` | Status | InArgument | `TaskStatus` | Yes | — | The status value to assign to the task. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `TaskGuid` | Task | `string` | — | The identifier of the task to update. Selected via auto-complete from tasks visible in the current scope. If omitted, targets the current task within the enclosing Process Tracking Scope. |

## XAML Example

```xml
<ui:SetTaskStatus
    xmlns:ui="clr-namespace:UiPath.Core.Activities.ProcessTracking;assembly=UiPath.System.Activities"
    DisplayName="Set Task Status"
    TaskGuid="myTaskScope"
    Status="[TaskStatus.Completed]" />
```

## Notes

- **Set Task Status** is typically placed inside a **Process Tracking Scope** to set the outcome of the task being tracked.
- `TaskGuid` is selected from tasks defined by enclosing **Process Tracking Scope** activities using an auto-complete expression widget. It does not accept a free-form GUID string in normal usage.
- `Status` accepts values from the `TaskStatus` enum provided by the UiPath.System.Activities package. Common values include `Completed`, `Failed`, and `Unfinished`.
- Setting the task status does not automatically close the enclosing trace. To close the trace, use **Set Trace Status**.
