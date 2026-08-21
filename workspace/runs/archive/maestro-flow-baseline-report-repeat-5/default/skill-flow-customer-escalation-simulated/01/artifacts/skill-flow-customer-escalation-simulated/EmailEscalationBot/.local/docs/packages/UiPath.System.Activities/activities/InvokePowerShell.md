# Invoke PowerShell

`UiPath.Core.Activities.InvokePowerShell<TResult>`

Runs a PowerShell command or script and returns the pipeline output converted to `TResult`.

**Package:** `UiPath.System.Activities`
**Category:** System > PowerShell

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `CommandText` | Command Text | `InArgument` | `string` | Yes | `null` | PowerShell command text or script text to execute. |
| `Input` | Input | `InArgument` | `Collection<PSObject>` | No | `null` | Pipeline input objects passed to the command. |
| `Parameters` | Parameters | Property | `Dictionary<string, InArgument>` | No | Empty | PowerShell parameters passed by name. Boolean parameters can be used as switch parameters. |
| `PowerShellVariables` | PowerShell Variables | Property | `Dictionary<string, Argument>` | No | Empty | Variables made available to the PowerShell runspace. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `IsScript` | Is Script | `bool` | `false` | When `true`, treats `CommandText` as script text instead of a command name. |
| `PowerShellProcess` | PowerShell Process | `PowerShellProcessVersion` | `PowerShellCore` | Selects the PowerShell host process on Windows builds. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Output` | Output | `OutArgument` | `Collection<TResult>` | Pipeline output converted from each `PSObject.BaseObject` to `TResult`. |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue On Error | `InArgument` | `bool` | `false` | When `true`, suppresses execution exceptions and continues the workflow. |

## XAML Example

```xml
<ui:InvokePowerShell x:TypeArguments="x:String"
    DisplayName="Invoke PowerShell"
    CommandText="Get-Process | Select-Object -First 1 -ExpandProperty ProcessName"
    IsScript="True"
    Output="[processNames]" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This activity is Windows-only.
- Use `IsScript = true` when `CommandText` contains a full script or pipeline.
- `Output` contains a collection, even when the command returns a single object.
