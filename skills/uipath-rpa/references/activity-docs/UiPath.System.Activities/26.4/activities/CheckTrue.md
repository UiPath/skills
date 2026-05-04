# Check True

`UiPath.Core.Activities.CheckTrue`

Checks if a given boolean expression is true and generates an error with a specified message when the expression is false.

**Package:** `UiPath.System.Activities`
**Category:** Workflow.Checkpoint

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Expression` | Expression | `InArgument` | `bool` | Yes | — | The boolean expression to evaluate. The activity passes when this evaluates to `True`. |
| `ErrorMessage` | ErrorMessage | `InArgument` | `string` | No | — | The message included in the thrown exception when `Expression` evaluates to `False`. If omitted, a default checkpoint failure message is used. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | `OutArgument` | `bool` | Set to `True` when the expression passes. Not set (remains `False`) when the assertion fails because the exception is thrown before the result is written. |

## XAML Example

```xml
<ui:CheckTrue DisplayName="Check True"
    Expression="[myValue &gt; 0]"
    ErrorMessage="[&quot;Value must be positive&quot;]"
    Result="[checkResult]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

When `Expression` is `False`, the activity sets `Result` to `False` and immediately throws a `CheckpointException` (a subclass of `Exception`) with the provided `ErrorMessage`. The workflow is aborted unless the exception is caught by an enclosing Try/Catch.

Use `Check True` to assert preconditions or postconditions within a workflow and surface clear diagnostic messages when invariants are violated.
