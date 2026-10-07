# While

> **On the [Common Activity Card](../../../../common-activity-card.md)** — prefer the card for routine authoring.

`UiPath.Core.Activities.InterruptibleWhile`

Executes contained activities while the condition is True.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Condition` | Condition | `Activity` | `bool` | No | — | The Boolean condition evaluated before each iteration. The loop continues while this is `True`. Set via the `<ui:InterruptibleWhile.Condition>` property element containing a `<VisualBasicValue x:TypeArguments="x:Boolean">` in VB projects or `<CSharpValue x:TypeArguments="x:Boolean">` in modern C# projects directly — **no `<InArgument>` wrapper**, because `Condition` is `Activity<bool>`, not `InArgument<bool>`. |
| `MaxIterations` | Max Iterations | `InArgument` | `int` | No | — | Maximum number of iterations. A value of `0` means unlimited. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `CurrentIndex` | Current Index | `OutArgument` | `int` | The zero-based index of the current iteration. |

## XAML Example

```xml
<ui:InterruptibleWhile
    xmlns:ui="http://schemas.uipath.com/workflow/activities"
    DisplayName="While">
  <ui:InterruptibleWhile.Condition>
    <VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="counter &lt; 10" />
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
