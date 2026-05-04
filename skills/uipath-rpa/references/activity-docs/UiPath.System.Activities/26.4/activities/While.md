# While

`UiPath.Core.Activities.InterruptibleWhile`

Executes contained activities while the condition is True.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Condition` | Condition | `InArgument` | `bool` | No | — | The Boolean condition evaluated before each iteration. The loop continues while this is `True`. |
| `MaxIterations` | Max Iterations | `InArgument` | `int` | No | — | Maximum number of iterations. A value of `0` means unlimited. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `CurrentIndex` | Current Index | `OutArgument` | `int` | The zero-based index of the current iteration. |

## XAML Example

```xml
<ui:InterruptibleWhile
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="While">
  <ui:InterruptibleWhile.Condition>
    <InArgument x:TypeArguments="x:Boolean">
      <VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="counter &lt; 10" />
    </InArgument>
  </ui:InterruptibleWhile.Condition>
  <ui:InterruptibleWhile.Body>
    <Sequence DisplayName="Body">
      <!-- child activities go here -->
    </Sequence>
  </ui:InterruptibleWhile.Body>
</ui:InterruptibleWhile>
```

## Notes

- **While** is a container/scope activity. Child activities are placed inside its `Body`.
- The `Condition` is evaluated **before** each iteration. If it is `False` on the first evaluation the body never executes.
- Use a `Break` activity inside the body to exit the loop early; use `Continue` to skip to the next iteration.
- Setting `MaxIterations` provides an upper bound to prevent infinite loops regardless of the condition value.
