# Invoke Code

`UiPath.Core.Activities.InvokeCode`

Synchronously invokes VB.NET or C# code, optionally passing it a list of input arguments. This activity can also return out arguments to the caller workflow.

**Package:** `UiPath.System.Activities`
**Category:** Programming

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| ContinueOnError | Continue on error | InArgument | `bool` | No | — | When `True`, execution continues to the next activity even if this activity throws an error. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| Code | Code | `string` | — | The VB.NET or C# source code to execute. Required. Supports only string literals and String variables. |
| Language | Language | `NetLanguage` | `NetLanguage.VBNet` | The programming language of the code snippet (`VBNet` or `CSharp`). |
| Arguments | Arguments | `Dictionary<string, Argument>` | — | Named input/output argument bindings that make workflow variables available inside the code and allow returning values back to the workflow. |

### Output

_No dedicated output arguments. Return values are passed back through the `Arguments` dictionary using `OutArgument` or `InOutArgument` entries._

## Enum Reference

### NetLanguage

| Value | Description |
|-------|-------------|
| `VBNet` | Visual Basic .NET (default) |
| `CSharp` | C# |

## XAML Example

```xml
<ui:InvokeCode Language="VBNet">
  <ui:InvokeCode.Code>
    <x:String>
      result = input * 2
    </x:String>
  </ui:InvokeCode.Code>
  <ui:InvokeCode.Arguments>
    <x:Reference>invokeCodeArgs</x:Reference>
  </ui:InvokeCode.Arguments>
</ui:InvokeCode>
```

## Notes

- Argument bindings in the `Arguments` dictionary use the variable name as the key; direction (`In`, `Out`, `InOut`) determines data flow.
- The code snippet is compiled and executed at runtime in the same process as the robot; it has access to all .NET BCL types.
- Use `InArgument` entries to pass data into the code and `OutArgument` entries to receive results back.
- Both `VBNet` and `CSharp` are supported; choose the language that matches your Studio project settings for consistency.
