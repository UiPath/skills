# Run Presentation Macro

`UiPath.Presentations.Activities.RunMacro`

Runs a specified macro in a macro-enabled PowerPoint presentation.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint.Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Presentation` | Presentation name | InArgument | `IPresentationQuickHandle` | Yes | | | Presentation containing the macro to run |
| `MacroName` | Macro name | InArgument | `string` | Yes | | | Name of the macro to run |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `AddMacroArgument` | Add Macro Argument | ActionButton | | Designer button to add an argument to pass to the macro |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Result` | Returned value | `object` | The value returned by the macro (if any) |

## Child Activities (Macro Arguments)

When the **Add Macro Argument** button is clicked in the designer, a `RunMacroArgument` child activity is added inside the `RunMacro` scope. Each child represents one positional argument passed to the macro.

| Child Activity Class | Properties |
|---------------------|------------|
| `RunMacroArgument` | `ArgumentValue` (InArgument `object`, required) — the value to pass to the macro's input argument |

Multiple `RunMacroArgument` children can be stacked; they are passed to the macro in order.

## XAML Example

```xml
<pres:RunMacro
    DisplayName="Run Presentation Macro"
    Presentation="[presentation]"
    MacroName="[&quot;Module1.FormatAllSlides&quot;]"
    Result="[macroResult]">
    <pres:RunMacroArgument
        DisplayName="Macro Argument"
        ArgumentValue="[&quot;Slide1&quot;]" />
    <pres:RunMacroArgument
        DisplayName="Macro Argument"
        ArgumentValue="[42]" />
</pres:RunMacro>
```

## Notes

- Windows only — requires Desktop PowerPoint
- Must be placed inside a `PowerPointApplicationScope`
- The presentation must be macro-enabled (.pptm format)
- Macro arguments are added via the designer's Add Macro Argument button; each argument creates a child activity element in XAML
- Arguments are passed to the macro in the order they appear
- The macro name should include the module name (e.g., `Module1.MacroName`)
