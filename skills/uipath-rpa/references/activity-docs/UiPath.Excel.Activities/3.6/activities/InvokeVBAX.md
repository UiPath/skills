# Invoke VBA

`UiPath.Excel.Activities.Business.InvokeVBAX`

Invokes a macro from an external file containing VBA code and runs it against an Excel file.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Workbook` | Target workbook | InArgument | `IWorkbookQuickHandle` | Yes | | Workbook on which to execute the VBA function. |
| `EntryMethodName` | Entry method name | InArgument | `string` | Yes | `"Main"` | The Sub/Function name to be invoked. Must be implemented in the code file. |
| `CodeFilePath` | Code file path | InArgument | `string` | Yes | | Full path to the (text) file containing the necessary VBA Sub/Function definitions. |

### Designer Controls (Not Mapped to XAML)
| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `AddVBAArgument` | Add VBA Argument | Action Button | Inserts a new `InvokeVBAArgumentX` child activity to pass an argument to the VBA function. |

### Output
| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Result` | Output | `OutArgument` | Entry method return value, if any. |

## Child Activity: InvokeVBAArgumentX

`UiPath.Excel.Activities.Business.InvokeVBAArgumentX`

Each child activity represents a single argument passed to the VBA Sub/Function. Add one per argument using the **Add VBA Argument** button.

| Name | Display Name | Kind | Type | Required | Description |
|------|-------------|------|------|----------|-------------|
| `ArgumentValue` | Argument value | InArgument | `object` | Yes | The value to be passed to the input argument of the VBA Sub/Function. |

## XAML Example
```xml
<excel:InvokeVBAX
  DisplayName="Invoke VBA"
  Workbook="[workbookHandle]"
  EntryMethodName="[&quot;Main&quot;]"
  CodeFilePath="[&quot;C:\Scripts\macro.vb&quot;]"
  Result="[vbaResult]">
  <excel:InvokeVBAX.Body>
    <excel:InvokeVBAArgumentX
      DisplayName="VBA Argument"
      ArgumentValue="[argValue]" />
  </excel:InvokeVBAX.Body>
</excel:InvokeVBAX>
```

## Notes
- This activity supports child `InvokeVBAArgumentX` activities to pass arguments to the VBA function.
- Use the **Add VBA Argument** action button in the designer to add arguments.
- The maximum number of arguments is limited by `ExcelConstants.MaxNumberOfMacroArguments`.
- The `CodeFilePath` must point to a text file containing valid VBA Sub/Function definitions.
- The `EntryMethodName` defaults to `"Main"` if not specified.
- The `Result` output is a non-generic `OutArgument`; the actual type depends on what the VBA function returns.
- COM exceptions during VBA execution are wrapped in `ExcelException` with contextual information.
