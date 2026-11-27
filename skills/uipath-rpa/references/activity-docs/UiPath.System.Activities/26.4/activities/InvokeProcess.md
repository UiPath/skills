# Invoke Process

`UiPath.Core.Activities.InvokeProcess`

Starts the specified process within the current robot execution. It waits for the invoked process to finish before resuming the execution. It returns output arguments.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ProcessName` | Process Name / Package Name | `InArgument` | `string` | Yes | — | The name of the Orchestrator process (when invoking by process name) or the package name (when invoking by package name). The display name changes based on the `Invoke Process By` selection. |
| `FolderPath` | Folder Path | `InArgument` | `string` | No | — | The Orchestrator folder path used to locate the process. In solution scope, this field becomes read-only when a process is selected by literal name. |
| `EntryPointPath` | Entry point | `InArgument` | `string` | No | — | The entry point `.xaml` path within the package. Only visible when **Invoke Process By** is set to `ByPackageName`. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `UsePackage` | Use package | `bool` | `True` | Determines whether the process is looked up by package name (and entry point) or by Orchestrator process name. |
| `TargetSession` | Target Session | `InvokeProcessTargetSession` | `Current` | The session in which the process executes. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `OutputArguments` | Output Arguments | `OutArgument` | `Dictionary<string, object>` | A dictionary containing the output arguments returned by the invoked process after it completes. |

## Valid Configurations

| `UsePackage` | Visible fields |
|---|---|
| `False` (by process name) | `ProcessName` (as "Process Name"), `FolderPath`, `NotMappedEntryPointPath` (read-only placeholder showing the detected entry point) |
| `True` (by package name) | `ProcessName` (as "Package Name"), `FolderPath`, `EntryPointPath`, deprecation warning info box |

## XAML Example

```xml
<ui:InvokeProcess
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Invoke Process"
    UsePackage="False">
  <ui:InvokeProcess.ProcessName>
    <InArgument x:TypeArguments="x:String">
      <VisualBasicValue x:TypeArguments="x:String" ExpressionText="&quot;MyAutomation&quot;" />
    </InArgument>
  </ui:InvokeProcess.ProcessName>
  <ui:InvokeProcess.FolderPath>
    <InArgument x:TypeArguments="x:String">
      <VisualBasicValue x:TypeArguments="x:String" ExpressionText="&quot;Shared&quot;" />
    </InArgument>
  </ui:InvokeProcess.FolderPath>
  <ui:InvokeProcess.OutputArguments>
    <OutArgument x:TypeArguments="scg:Dictionary(x:String, x:Object)" />
  </ui:InvokeProcess.OutputArguments>
</ui:InvokeProcess>
```

## Notes

- The activity waits synchronously for the invoked process to finish before execution continues in the calling workflow.
- **Invoke Process By** (`InvokeProcessBy`) is a designer-only radio-group control (`notMapped`) that sets `UsePackage` on the underlying activity and switches between process-name and package-name modes.
- When invoking by package name, a deprecation warning info box is shown in the designer (`InvokeProcessInfoBox`).
- In solution scope, `FolderPath` is automatically set from the selected process and becomes read-only; it is cleared if the process selection changes to a non-literal expression.
- `Arguments` (the input/output argument dictionary passed to the process) is populated automatically by importing arguments from Orchestrator when a valid process and, if applicable, entry point are selected. Use the **Use an expression** menu action to switch to `ArgumentsVariable`, a single expression-based alternative. At runtime, `ArgumentsVariable` takes precedence over `Arguments` when both are set.
- On non-Windows/Portable target frameworks, an incompatible target framework warning is displayed when a Legacy or Windows process is selected in solution scope.
