# Invoke Com Method

`UiPath.Core.Activities.InvokeComMethod`

Invokes a method of a specified COM object.

**Package:** `UiPath.System.Activities`
**Category:** Programming.Execute
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| MethodName | Method name | InArgument | `string` | Yes | — | The name of the method to invoke on the COM object. |
| CLSID | CLSID | InArgument | `string` | No | — | The class identifier (CLSID) of the COM object to instantiate. Use either `CLSID` or `ProgID` to identify the target object. |
| ProgID | ProgID | InArgument | `string` | No | — | The programmatic identifier (ProgID) of the COM object type. Use either `ProgID` or `CLSID`. |
| ContinueOnError | Continue On Error | InArgument | `bool` | No | — | When `True`, execution continues to the next activity even if this activity throws an error. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| Arguments | Arguments | `Dictionary<string, Argument>` | — | Named parameter bindings passed to the COM method. |
| BindingFlags | Binding flags | `BindingFlags` | — | Reflection binding flags controlling how the method is located and invoked. Supports multi-select. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| Result | Result | OutArgument | `object` | The return value of the invoked COM method. Cast to the appropriate type as needed. |

## Valid Configurations

Provide exactly one of `CLSID` or `ProgID` to identify the COM server:

| Scenario | Use |
|----------|-----|
| Known ProgID (e.g., `"Excel.Application"`) | `ProgID` |
| Known CLSID GUID | `CLSID` |

## XAML Example

```xml
<!-- Invoke a method using ProgID -->
<ui:InvokeComMethod MethodName="Open">
  <ui:InvokeComMethod.ProgID>
    <InArgument x:TypeArguments="x:String">"Excel.Application"</InArgument>
  </ui:InvokeComMethod.ProgID>
  <ui:InvokeComMethod.Result>
    <OutArgument x:TypeArguments="x:Object">[comResult]</OutArgument>
  </ui:InvokeComMethod.Result>
</ui:InvokeComMethod>
```

## Notes

- This activity is only supported on Windows; COM is a Windows-specific technology.
- `CLSID` and `ProgID` are mutually exclusive; supplying both may cause unexpected behaviour.
- The `Result` is typed as `object`; use an Assign or Cast activity to convert it to the expected .NET type.
- `BindingFlags` maps directly to `System.Reflection.BindingFlags`; the default (no flags set) uses standard late-binding invocation suitable for most COM objects.
