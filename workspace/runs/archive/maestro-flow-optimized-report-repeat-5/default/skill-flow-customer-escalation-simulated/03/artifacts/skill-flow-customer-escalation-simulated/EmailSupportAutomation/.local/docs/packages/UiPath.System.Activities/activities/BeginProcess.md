# Run Parallel Process

`UiPath.Core.Activities.BeginProcess`

Starts a UiPath process in the background via Orchestrator without waiting for it to complete. The calling workflow continues immediately after the process is launched. Only input arguments are passed to the target process; output arguments are not supported.

**Package:** `UiPath.System.Activities`
**Category:** Workflow > Invoke

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ProcessName` | Process name / Package name | `InArgument` | `string` | Yes | — | The name of the Orchestrator process (when `UsePackage` is `False`) or the package name (when `UsePackage` is `True`). Supports auto-complete from available processes in the configured folder. |
| `FolderPath` | Folder Path | `InArgument` | `string` | No | — | The Orchestrator folder containing the process or package. Leave empty to use the folder of the current process. |
| `EntryPointPath` | Entry point | `InArgument` | `string` | No | — | The entry point `.xaml` path within the package. Only applicable when `UsePackage` is `True`. Cannot be used when `UsePackage` is `False`. |
| `Arguments` | Arguments | `Dictionary<string, InArgument>` | — | No | `{}` | A dictionary of input arguments to pass to the launched process. Use the **Import Arguments** menu action to auto-populate from the selected process's schema. Only `In` direction arguments are supported. Use the **Use an expression** menu action to switch to expression mode. |
| `ArgumentsVariable` | Arguments variable | `InArgument` | `Dictionary<string, object>` | No | — | An expression-based alternative to `Arguments`. When set, this takes precedence over the `Arguments` dictionary at runtime. Use the **Use arguments** menu action to switch back to the literal dictionary. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `UsePackage` | Use package | `bool` | `True` | When `True`, the process is identified by its package name and optional entry point. When `False`, the process is identified by its Orchestrator process name. |
| `TargetSession` | Target session | `InvokeProcessTargetSession` | `Current` | The session in which the child process is started. |

## Valid Configurations

| `UsePackage` | `ProcessName` | `EntryPointPath` |
|---|---|---|
| `False` (by process name) | Orchestrator process name | Not allowed (validation error if set) |
| `True` (by package name) | Package name | Optional `.xaml` entry point path |

## XAML Example

```xml
<!-- Start a process by Orchestrator process name (fire and forget) -->
<ui:BeginProcess
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Run Parallel Process"
    UsePackage="False">
  <ui:BeginProcess.ProcessName>
    <InArgument x:TypeArguments="x:String">
      <VisualBasicValue x:TypeArguments="x:String" ExpressionText="&quot;InvoiceProcessor&quot;" />
    </InArgument>
  </ui:BeginProcess.ProcessName>
  <ui:BeginProcess.FolderPath>
    <InArgument x:TypeArguments="x:String">
      <VisualBasicValue x:TypeArguments="x:String" ExpressionText="&quot;Finance/Shared&quot;" />
    </InArgument>
  </ui:BeginProcess.FolderPath>
</ui:BeginProcess>
```

```xml
<!-- Start a process by package name with a specific entry point -->
<ui:BeginProcess
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Run Parallel Process"
    UsePackage="True">
  <ui:BeginProcess.ProcessName>
    <InArgument x:TypeArguments="x:String">
      <VisualBasicValue x:TypeArguments="x:String" ExpressionText="&quot;MyPackage&quot;" />
    </InArgument>
  </ui:BeginProcess.ProcessName>
  <ui:BeginProcess.EntryPointPath>
    <InArgument x:TypeArguments="x:String">
      <VisualBasicValue x:TypeArguments="x:String" ExpressionText="&quot;Main.xaml&quot;" />
    </InArgument>
  </ui:BeginProcess.EntryPointPath>
</ui:BeginProcess>
```

## Notes

- **Fire and forget** — unlike **Invoke Process** or **Run Job**, `BeginProcess` does not wait for the launched process to finish. The calling workflow immediately continues after the child process is started.
- Only `In` direction arguments are supported in `Arguments`. Output arguments from the child process are not accessible.
- `Arguments` and `ArgumentsVariable` are mutually exclusive in the designer. Use the menu action on either property to toggle between the literal argument dictionary and a single expression variable. At runtime, `ArgumentsVariable` takes precedence over `Arguments` when both are set.
- Requires an active Orchestrator connection and the target process to be published and available in the specified folder.
- `EntryPointPath` is only valid when `UsePackage` is `True`. Setting it when `UsePackage` is `False` causes a validation error.
- The **Import Arguments** menu action on the `Arguments` property auto-populates the argument dictionary from Orchestrator when a valid `ProcessName` (and optionally `EntryPointPath`) is set to a literal string.
