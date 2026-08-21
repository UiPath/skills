# Process Start Trigger

`UiPath.Core.Activities.ProcessStartTriggerV2`

Triggers when a process whose name matches the configured pattern starts.

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
| `ProcessInfo` | `ProcessInfo` | Trigger argument containing information about the process that started. |

## XAML Example

```xml
<ui:ProcessStartTriggerV2
    DisplayName="Process Start Trigger"
    ProcessName="notepad*" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This trigger is implemented for Windows runtime.
- Use this activity inside a trigger scope or a trigger-enabled workflow surface.
