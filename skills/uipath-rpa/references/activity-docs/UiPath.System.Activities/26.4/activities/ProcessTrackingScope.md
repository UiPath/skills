# Process Tracking Scope

`UiPath.Core.Activities.ProcessTracking.ProcessTrackingScope`

Enables Process Tracking. This will track the execution of a Sequence as a Task in Process Mining. You can configure this scope using properties panel and control how the execution gets tracked as part of a Task and Process within Process Mining.

**Package:** `UiPath.System.Activities`
**Category:** Process Tracking

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `TaskName` | Task name | InArgument | `string` | No | — | The name to assign to the tracked task in Process Mining. |
| `ObjectId` | Object ID | InArgument | `string` | No* | — | The identifier of the object associated with the current task. Required when `ProcessLogMode` is `ExistingTrace`. Used to continue a trace started in a previous automation. |
| `ObjectType` | Object type | InArgument | `string` | No* | — | The type of the object associated with the current task (e.g., `"invoice"`, `"document"`). Required when `ProcessLogMode` is `ExistingTrace`. |
| `ObjectInteraction` | Object interaction | InArgument | `PTSObjectInteraction` | No | `null` | The interaction type of the object for this task. Visible when `ProcessLogMode` is `ExistingTrace`. |
| `ProcessCaseName` | Process name | InArgument | `string` | No* | — | The business process name for a new trace. Groups related tasks within the Process Tracking Service. Required when `ProcessLogMode` is `NewTrace`. |
| `ProcessCaseNameToSwitchTo` | Process name | InArgument | `string` | No* | — | The name of an existing trace to track this task in. Required when `ProcessLogMode` is `ExistingTrace`. |

*Required dynamically based on `ProcessLogMode` value.

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `IsPTSEnabled` | Process tracking | `bool` | — | Enables or disables process tracking for this scope. Only visible when the Process Mining service is connected. |
| `ProcessLogMode` | How to track | `ProcessTrackingMode` | `ProcessTrackingMode.CurrentTrace` | Determines in which Process Mining trace the task execution is recorded. |

## Valid Configurations

The properties shown and required depend on the `ProcessLogMode` value:

| `ProcessLogMode` | Visible / Required properties |
|---|---|
| `CurrentTrace` | `TaskName`, `ProcessLogMode`. Tracks in the currently active trace. No object or process identification required. |
| `NewTrace` | `TaskName`, `ProcessLogMode`, `ProcessCaseName` (required). Starts a new trace for the specified business process. |
| `ExistingTrace` | `TaskName`, `ProcessLogMode`, `ProcessCaseNameToSwitchTo` (required), `ObjectId` (required), `ObjectType` (required), `ObjectInteraction` (optional). Continues tracking in an existing trace identified by process name and object. |

### Enum Reference

**`ProcessTrackingMode`**

| Value | Description |
|-------|-------------|
| `CurrentTrace` | Track the task in the currently active Process Mining trace. |
| `NewTrace` | Create a new trace for the given process name and track this task in it. |
| `ExistingTrace` | Switch to an existing trace (identified by process name and object) and track this task in it. |

## XAML Example

```xml
<!-- Track in the current trace -->
<ui:ProcessTrackingScope
    xmlns:ui="clr-namespace:UiPath.Core.Activities.ProcessTracking;assembly=UiPath.System.Activities"
    DisplayName="Process Tracking Scope"
    IsPTSEnabled="True"
    TaskName="[&quot;ProcessInvoice&quot;]"
    ProcessLogMode="CurrentTrace">
  <Sequence>
    <!-- automation activities here -->
  </Sequence>
</ui:ProcessTrackingScope>
```

```xml
<!-- Start a new trace -->
<ui:ProcessTrackingScope
    xmlns:ui="clr-namespace:UiPath.Core.Activities.ProcessTracking;assembly=UiPath.System.Activities"
    DisplayName="Process Tracking Scope"
    IsPTSEnabled="True"
    TaskName="[&quot;ValidateInvoice&quot;]"
    ProcessLogMode="NewTrace"
    ProcessCaseName="[&quot;InvoiceProcessing&quot;]">
  <Sequence>
    <!-- automation activities here -->
  </Sequence>
</ui:ProcessTrackingScope>
```

## Notes

- **Process Tracking Scope** is a container activity. All activities inside its body are tracked as part of the named task in Process Mining.
- `IsPTSEnabled` is only visible in the designer when the Process Mining service is connected to the Studio project.
- Use **Track Object** activities inside the scope to associate domain objects (invoices, documents, etc.) with the tracked task.
- Use **Set Task Status** to explicitly set the outcome status of the task, and **Set Trace Status** to close and set the status of the enclosing trace.
- `ObjectId` and `ObjectType` being required for `ExistingTrace` mode is enforced dynamically at runtime — the designer indicates this via the `IsRequired` flag on the respective properties.
