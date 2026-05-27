# Invoke Workflow File

`UiPath.Core.Activities.InvokeWorkflowFile`

Synchronously invokes a specified workflow, optionally passing it a list of input arguments.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `WorkflowFileName` | Workflow file name | `InArgument` | `string` | Yes | — | The path to the `.xaml` workflow file to invoke. In normal static calls, serialize as a plain relative path string, not an expression-wrapped string literal. |
| `ArgumentsVariable` | Arguments Variable | `InArgument` | `Dictionary<string, object>` | No | — | Alternative to `Arguments`. When set, the caller passes a single dictionary instead of per-argument bindings. Use this OR `Arguments`, not both. |
| `Timeout` | Timeout | `InArgument` | `TimeSpan` | No | — | Execution timeout. Unset = no timeout. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `UnSafe` | Isolated | `bool` | `False` | When `True`, the invoked workflow runs in an isolated process. Required when `TargetSession` is non-`Current` (otherwise `CacheMetadata` raises a validation error). |
| `TargetSession` | Target Session | `InvokeWorkflowTargetSession` | `Current` | The session in which the invoked workflow executes. Values: `Current` \| `Main` \| `PictureInPicture`. |
| `Arguments` | Arguments | `Dictionary<string, Argument>` | empty | Dictionary of bound arguments keyed by the invoked workflow's declared argument names. Use `InArgument`/`OutArgument`/`InOutArgument` element kinds per argument direction. |

### Log

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `LogEntry` | Log Entry | `InArgument` | `LogEntryType` | `No` | Entry-log mode. Values: `No` \| `OnlyInvocation` \| `WithArguments`. |
| `LogExit` | Log Exit | `InArgument` | `LogExitType` | `No` | Exit-log mode. Values: `No` \| `OnlySuccessfulReturn` \| `WithArguments`. |
| `Level` | Log Level | `InArgument` | `LogLevel` | `Info` | Severity of entry/exit log lines (only emitted when `LogEntry`/`LogExit` are non-`No`). Same enum as `LogMessage.Level`. |

## XAML Example

```xml
<ui:InvokeWorkflowFile
    xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
    xmlns:ui="http://schemas.uipath.com/workflow/activities"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    DisplayName="Invoke Workflow File"
    UnSafe="False"
    WorkflowFileName="Workflows\Process.xaml">
  <ui:InvokeWorkflowFile.Arguments>
    <InArgument x:TypeArguments="x:String" x:Key="in_invoiceId">
      <VisualBasicValue x:TypeArguments="x:String" ExpressionText="invoiceId" />
    </InArgument>
    <OutArgument x:TypeArguments="x:Boolean" x:Key="out_isValid">
      <VisualBasicReference x:TypeArguments="x:Boolean" ExpressionText="isValid" />
    </OutArgument>
  </ui:InvokeWorkflowFile.Arguments>
</ui:InvokeWorkflowFile>
```

## Notes

- **Invoke Workflow File** is a container/scope activity in the sense that it passes arguments to and receives output from the invoked workflow file.
- The invoked workflow runs **synchronously** — the current workflow pauses until the invoked one finishes.
- `WorkflowFileName` must be a plain project-relative path (`Workflows\Process.xaml`), not `[&quot;Workflows\Process.xaml&quot;]` or another expression-wrapped string. See `xaml/common-pitfalls.md` for the path-resolution failure mode.
- When manually populating `Arguments`, use direct `InArgument` / `OutArgument` / `InOutArgument` children with `x:Key` matching the callee argument name. Do **not** wrap populated arguments in `scg:Dictionary`; Studio may clear dictionary-wrapped mappings on load. The empty dictionary returned by `activities get-default-xaml` is only correct for the empty state.
- For C# XAML projects, replace `VisualBasicValue` / `VisualBasicReference` with `CSharpValue` / `CSharpReference` element-body bindings; do not use VB bracket shorthand for argument expressions.
- Setting `Isolated` (`UnSafe`) to `True` runs the invoked workflow in a separate process for fault isolation; this incurs additional overhead.
- `TargetSession` controls which robot session executes the invoked workflow (e.g. `Current`, `Main`, `PictureInPicture`).
- `AssemblyName` is a non-browsable internal property and is not intended for manual configuration.
