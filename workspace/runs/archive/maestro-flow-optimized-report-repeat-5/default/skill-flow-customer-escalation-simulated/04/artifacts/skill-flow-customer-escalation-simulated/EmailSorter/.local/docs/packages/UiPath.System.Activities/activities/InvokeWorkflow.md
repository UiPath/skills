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
| `Elevated` | Elevated | `bool` | `False` | When `True`, the isolated child executor runs at MediumPlus integrity. Requires `Isolated` to be `True` (validated at design time), and requires the robot to set the `UIPATH_MEDIUMPLUS_INVOKE` machine environment variable; otherwise the flag is silently ignored. Available for all target sessions. |
| `TargetSession` | Target Session | `InvokeWorkflowTargetSession` | `Current` | The session in which the invoked workflow executes. |

## XAML Example

```xml
<ui:InvokeWorkflowFile
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Invoke Workflow File"
    WorkflowFileName="Workflows\Process.xaml">
  <ui:InvokeWorkflowFile.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument"
                    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib">
      <InArgument x:TypeArguments="x:String" x:Key="in_InvoiceId">[invoiceId]</InArgument>
      <InArgument x:TypeArguments="x:Double" x:Key="in_Amount">[amount]</InArgument>
      <OutArgument x:TypeArguments="x:Boolean" x:Key="out_Success">[wasSuccessful]</OutArgument>
    </scg:Dictionary>
  </ui:InvokeWorkflowFile.Arguments>
</ui:InvokeWorkflowFile>
```

Author the `Arguments` dictionary inline. Each entry maps to one of the invoked workflow's declared arguments — `InArgument` for inputs, `OutArgument` for outputs, `InOutArgument` for round-trip. An opaque `<x:Reference>` to a separate dictionary node is not portable.

## Notes

- **Invoke Workflow File** is a container/scope activity in the sense that it passes arguments to and receives output from the invoked workflow file.
- The invoked workflow runs **synchronously** — the current workflow pauses until the invoked one finishes.
- `Arguments` is a dictionary of input/output arguments mapped to the invoked workflow's declared arguments; it is populated automatically from the target `.xaml` file when a valid `WorkflowFileName` is provided.
- Setting `Isolated` (`UnSafe`) to `True` runs the invoked workflow in a separate process for fault isolation; this incurs additional overhead.
- `Elevated` is enabled in the designer only while `Isolated` is `True`; clearing `Isolated` disables the checkbox and clears the value. Setting `Elevated=True` with `Isolated=False` produces a design-time validation error. It is available for every target session.
- `Elevated` opts a single isolated child executor into MediumPlus / UIAccess integrity without elevating the parent executor. It depends on the robot exposing `RuntimeFeatures.ElevatedInvoke`, which is advertised only when the machine env var `UIPATH_MEDIUMPLUS_INVOKE` is set; on robots that do not opt in, the flag is silently dropped. The legacy `UIPATH_MEDIUMPLUS_EXECUTOR` env var (which elevates the whole executor tree and breaks COM-based activities) is independent and unchanged.
- `TargetSession` controls which robot session executes the invoked workflow (e.g. `Current`, `Main`, `PictureInPicture`).
- `AssemblyName` is a non-browsable internal property and is not intended for manual configuration.
