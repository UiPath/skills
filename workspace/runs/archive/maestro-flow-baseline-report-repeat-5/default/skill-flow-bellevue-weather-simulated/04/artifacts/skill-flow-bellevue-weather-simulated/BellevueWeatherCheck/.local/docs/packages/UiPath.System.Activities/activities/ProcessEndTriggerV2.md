# Process End Trigger

`UiPath.Core.Activities.ProcessEndTriggerV2`

Triggers when a process whose name matches the configured pattern ends.

**Package:** `UiPath.System.Activities`
**Category:** Triggers

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ProcessName` | Process name | `InArgument` | `string` | Yes | - | Process name or wildcard pattern to monitor. Matching is case-insensitive. |

### Output

| Name | Type | Description |
|------|------|-------------|
| `ProcessInfo` | `ProcessInfo` | Trigger argument containing information about the process that ended. |

## XAML Example

```xml
<ui:ProcessEndTriggerV2
    DisplayName="Process End Trigger"
    ProcessName="notepad*" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This trigger is implemented for Windows runtime.
- Use this activity inside a trigger scope or a trigger-enabled workflow surface.
