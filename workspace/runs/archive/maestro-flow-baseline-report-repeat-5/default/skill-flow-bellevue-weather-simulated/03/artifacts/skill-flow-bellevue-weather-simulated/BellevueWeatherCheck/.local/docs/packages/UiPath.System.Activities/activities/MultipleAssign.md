# Multiple Assign

`UiPath.Core.Activities.MultipleAssign`

Assigns values to multiple variables in sequence.

**Package:** `UiPath.System.Activities`
**Category:** Workflow > Control

## Properties

### Configuration

| Name | Display Name | Type | Required | Default | Description |
|------|-------------|------|----------|---------|-------------|
| `AssignOperations` | Assign Operations | `List<AssignOperation>` | Yes | One empty assignment | The ordered list of assignments configured by the designer. This property is hidden in the property grid. |

Each assignment contains:

| Name | Kind | Type | Required | Description |
|------|------|------|----------|-------------|
| `To` | `OutArgument` | Inferred | Yes | The variable or argument to assign to. |
| `Value` | `InArgument` | Inferred | Yes | The expression to assign. |

## XAML Example

```xml
<ui:MultipleAssign DisplayName="Multiple Assign">
  <ui:MultipleAssign.AssignOperations>
    <ui:AssignOperation To="[firstName]" Value="[&quot;Ada&quot;]" />
    <ui:AssignOperation To="[lastName]" Value="[&quot;Lovelace&quot;]" />
    <ui:AssignOperation To="[age]" Value="[36]" />
  </ui:MultipleAssign.AssignOperations>
</ui:MultipleAssign>
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- Assignments execute in list order.
- If an assignment fails, the activity wraps the original exception with a message that identifies the failed value and target expressions.
- `Value` and `To` types must be compatible.
- `AssignOperation.Value` and `AssignOperation.To` are **untyped** `InArgument` / `OutArgument`. Their effective type is inferred at design time from the bound expression on either side. In XAML, always use the bracketed VB-expression form for these attributes (e.g. `Value="[&quot;Ada&quot;]"` for a string literal, `Value="[someVariable]"` for a variable reference, `Value="[36]"` for a numeric literal). The plain-literal attribute form is reserved for typed `InArgument<T>` properties — using it on an untyped argument causes the value to be parsed as a VB identifier (variable reference) instead of a literal, which usually fails at runtime.
