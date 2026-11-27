# Invoke VBScript

`UiPath.Core.Activities.InvokeVBScript`

Executes a specified VBScript, optionally passing it a list of input parameters.

**Package:** `UiPath.System.Activities`
**Category:** System.VBScript
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| FileName | VBScript file name | InArgument | `string` | Yes | — | The full file path of the `.vbs` script to execute. |
| TimeoutMS | Timeout | InArgument | `int` | No | — | Maximum time in milliseconds to wait for the script to finish. Only applies when `WaitForOutput` is `True`. |
| KillOnTimeout | KillOnTimeout | InArgument | `bool` | No | `False` | When `True`, forcibly terminates the VBScript process if the timeout is reached. |
| RunInBatchMode | HidePopups | InArgument | `bool` | No | `False` | When `True`, suppresses display alerts, scripting errors, and input dialogs (runs silently). |
| UnicodeSupport | UnicodeSupport | InArgument | `bool` | No | `False` | When `True`, enables correct handling of non-ASCII characters (e.g., Japanese) in arguments and output. |
| WaitForOutput | WaitForOutput | InArgument | `bool` | No | `True` | When `True`, the activity waits for the script to complete before proceeding. When `False`, the script runs asynchronously and `TimeoutMS` is ignored. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| Arguments | Arguments | `List<InArgument<string>>` | `[]` | Ordered list of string arguments passed to the VBScript at runtime. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| Result | Result | OutArgument | `string` | The standard output produced by the VBScript execution. |

## XAML Example

```xml
<ui:InvokeVBScript WaitForOutput="True" TimeoutMS="10000" KillOnTimeout="True">
  <ui:InvokeVBScript.FileName>
    <InArgument x:TypeArguments="x:String">"C:\Scripts\MyScript.vbs"</InArgument>
  </ui:InvokeVBScript.FileName>
  <ui:InvokeVBScript.Arguments>
    <InArgument x:TypeArguments="x:String">arg1</InArgument>
    <InArgument x:TypeArguments="x:String">arg2</InArgument>
  </ui:InvokeVBScript.Arguments>
  <ui:InvokeVBScript.Result>
    <OutArgument x:TypeArguments="x:String">[scriptOutput]</OutArgument>
  </ui:InvokeVBScript.Result>
</ui:InvokeVBScript>
```

## Notes

- This activity is only supported on Windows; it relies on the Windows Script Host (`cscript.exe`).
- Arguments are passed positionally; access them in the script via `WScript.Arguments(0)`, `WScript.Arguments(1)`, etc.
- When `WaitForOutput` is `False`, the `Result` output will be empty because the process has not yet completed.
- `RunInBatchMode` (`HidePopups`) uses the `/B` switch of `cscript`, suppressing all UI interaction from the script.
