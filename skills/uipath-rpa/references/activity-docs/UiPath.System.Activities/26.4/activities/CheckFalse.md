# Check False

`UiPath.Core.Activities.CheckFalse`

Checks if a given boolean expression is false and generates an error with a specified message when the expression is true.

**Package:** `UiPath.System.Activities`
**Category:** Workflow.Checkpoint

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Expression` | Expression | `InArgument` | `bool` | Yes | — | The boolean expression to evaluate. The activity passes when this evaluates to `False`. |
| `ErrorMessage` | ErrorMessage | `InArgument` | `string` | No | — | The message included in the thrown exception when `Expression` evaluates to `True`. If omitted, a default checkpoint failure message is used. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | `OutArgument` | `bool` | Set to `True` when the expression passes (i.e. the condition is `False`). Not set (remains `False`) when the assertion fails because the exception is thrown before the result is written. |

## XAML Example

```xml
<ui:CheckFalse DisplayName="Check False"
    Expression="[hasError]"
    ErrorMessage="[&quot;An error was detected&quot;]"
    Result="[checkResult]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

When `Expression` is `True`, the activity sets `Result` to `False` and immediately throws a `CheckpointException` (a subclass of `Exception`) with the provided `ErrorMessage`. The workflow is aborted unless the exception is caught by an enclosing Try/Catch.

Use `Check False` to assert that an error flag or undesirable condition is not set, and surface a clear diagnostic message when it is.

`Check False` is the logical inverse of `Check True`: it succeeds when the expression is `False` and fails when it is `True`.
