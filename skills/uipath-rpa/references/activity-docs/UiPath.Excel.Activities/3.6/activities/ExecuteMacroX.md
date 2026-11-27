# Run Spreadsheet Macro

`UiPath.Excel.Activities.Business.ExecuteMacroX`

Executes a specified macro within a macro-enabled workbook.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Workbook` | Workbook name | InArgument | `IWorkbookQuickHandle` | Yes | | Workbook containing the macro to execute. |
| `MacroName` | Macro name | InArgument | `string` | Yes | | Name of the macro to run. |

### Designer Controls (Not Mapped to XAML)
| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `AddMacroArgument` | Add Macro Argument | Action Button | Inserts a new `ExecuteMacroArgumentX` child activity to pass an argument to the macro. |

### Output
| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Result` | Macro result | `OutArgument` | Save the value returned by the macro (if any). |

## Child Activity: ExecuteMacroArgumentX

`UiPath.Excel.Activities.Business.ExecuteMacroArgumentX`

Each child activity represents a single argument passed to the macro. Add one per argument using the **Add Macro Argument** button.

| Name | Display Name | Kind | Type | Required | Description |
|------|-------------|------|------|----------|-------------|
| `ArgumentValue` | Argument value | InArgument | `object` | Yes | The value to be passed to the input argument of the macro. |

## XAML Example
```xml
<excel:ExecuteMacroX
  DisplayName="Run Spreadsheet Macro"
  Workbook="[workbookHandle]"
  MacroName="[&quot;MyMacro&quot;]"
  Result="[macroResult]">
  <excel:ExecuteMacroX.Body>
    <excel:ExecuteMacroArgumentX
      DisplayName="Macro Argument"
      ArgumentValue="[argValue]" />
  </excel:ExecuteMacroX.Body>
</excel:ExecuteMacroX>
```

## Notes
- This activity supports child `ExecuteMacroArgumentX` activities to pass arguments to the macro.
- Use the **Add Macro Argument** action button in the designer to add arguments.
- The maximum number of macro arguments is limited by `ExcelConstants.MaxNumberOfMacroArguments`.
- The `Result` output is a non-generic `OutArgument`; the actual type depends on what the macro returns.
