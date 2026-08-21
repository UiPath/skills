# Notify Global Variable Changed

`UiPath.Core.Activities.NotifyGlobalVariableChanged`

Forces a change notification for a global variable so subscribed global variable triggers can run.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `VariableName` | Variable Name | `InArgument` | `object` | Yes | - | Expression that references the global variable to notify. |

## XAML Example

```xml
<ui:NotifyGlobalVariableChanged
    DisplayName="Notify Global Variable Changed"
    VariableName="[GlobalVariables.ApprovalState]" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- If the global variables platform feature is unavailable, the activity returns without doing anything.
- The activity parses the `VariableName` expression text to identify the global variable to notify.
