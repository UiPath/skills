# Return

`UiPath.Core.Activities.Return`

Ends the current workflow and resumes the process immediately after the point where the workflow was invoked. Compatible with Robots version 23.8 and above.

**Package:** `UiPath.System.Activities`
**Category:** Workflow.Control

## Properties

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|

_This activity has no configurable properties._

## XAML Example

```xml
<ui:Return DisplayName="Return"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

`Return` cancels the current workflow instance by calling `IWorkflowRuntime.CancelWorkflow`. Execution resumes in the parent process at the activity immediately following the `Invoke Workflow File` or equivalent invocation point.

If the robot runtime does not support the `CancelWorkflow` feature (versions earlier than 23.8), the activity throws a `PlatformNotSupportedException`.

Unlike `Break`, `Return` is not limited to loops — it exits the entire workflow regardless of nesting depth.
