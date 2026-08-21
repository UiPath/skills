# Global Variable Changed Trigger

`UiPath.Core.Activities.GlobalVariableChangedTrigger`

Triggers when the selected global variable is notified as changed.

**Package:** `UiPath.System.Activities`
**Category:** Triggers

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `VariableName` | Variable Name | `InArgument` | `object` | Yes | - | Expression that references the global variable to subscribe to. |

### Output

| Name | Type | Description |
|------|------|-------------|
| `Value` | `object` | The value supplied with the global variable change notification. |

## XAML Example

```xml
<ui:GlobalVariableChangedTrigger
    DisplayName="Global Variable Changed Trigger"
    VariableName="[GlobalVariables.ApprovalState]" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- The global variables platform feature must be available at runtime.
- The activity parses the `VariableName` expression text to identify the subscribed global variable.
- Use **Notify Global Variable Changed** to force a notification for a global variable.
