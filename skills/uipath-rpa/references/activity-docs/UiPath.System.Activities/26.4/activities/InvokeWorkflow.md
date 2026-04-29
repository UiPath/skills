# Invoke Workflow File

`UiPath.Core.Activities.InvokeWorkflowFile`

Synchronously invokes a specified workflow, optionally passing it a list of input arguments.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `WorkflowFileName` | Workflow file name | `InArgument` | `string` | Yes | — | The path to the `.xaml` workflow file to invoke. Supports expression auto-complete. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `UnSafe` | Isolated | `bool` | — | When `True`, the invoked workflow runs in an isolated process. |
| `TargetSession` | Target Session | `InvokeWorkflowTargetSession` | `Current` | The session in which the invoked workflow executes. |

## XAML Example

```xml
<ui:InvokeWorkflowFile
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Invoke Workflow File"
    WorkflowFileName="[&quot;Workflows\Process.xaml&quot;]">
  <ui:InvokeWorkflowFile.Arguments>
    <x:Reference>__ReferenceID0</x:Reference>
  </ui:InvokeWorkflowFile.Arguments>
</ui:InvokeWorkflowFile>
```

## Notes

- **Invoke Workflow File** is a container/scope activity in the sense that it passes arguments to and receives output from the invoked workflow file.
- The invoked workflow runs **synchronously** — the current workflow pauses until the invoked one finishes.
- `Arguments` is a dictionary of input/output arguments mapped to the invoked workflow's declared arguments; it is populated automatically from the target `.xaml` file when a valid `WorkflowFileName` is provided.
- Setting `Isolated` (`UnSafe`) to `True` runs the invoked workflow in a separate process for fault isolation; this incurs additional overhead.
- `TargetSession` controls which robot session executes the invoked workflow (e.g. `Current`, `Main`, `PictureInPicture`).
- `AssemblyName` is a non-browsable internal property and is not intended for manual configuration.
