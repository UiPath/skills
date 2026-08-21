# Do While

`UiPath.Core.Activities.InterruptibleDoWhile`

Executes contained activities first and then loops if the condition is True.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `MaxIterations` | Max Iterations | `InArgument` | `int` | No | — | Maximum number of iterations. A value of `0` means unlimited. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Body` | Body | `Activity` | — | The container holding the child activities to execute on each iteration. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `CurrentIndex` | Current Index | `OutArgument` | `int` | The zero-based index of the current iteration. |

## XAML Example

```xml
<ui:InterruptibleDoWhile
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Do While">
  <ui:InterruptibleDoWhile.Body>
    <Sequence DisplayName="Body">
      <!-- child activities go here -->
    </Sequence>
  </ui:InterruptibleDoWhile.Body>
  <ui:InterruptibleDoWhile.Condition>
    <VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="counter &lt; 10" />
  </ui:InterruptibleDoWhile.Condition>
</ui:InterruptibleDoWhile>
```

## Notes

- **Do While** is a container/scope activity. Child activities are placed inside its `Body`.
- Unlike **While**, the body is executed **at least once** — the `Condition` is evaluated **after** each iteration.
- The loop continues as long as `Condition` evaluates to `True`.
- Use a `Break` activity inside the body to exit the loop early; use `Continue` to skip to the next iteration.
- Setting `MaxIterations` provides an upper bound to prevent infinite loops.
