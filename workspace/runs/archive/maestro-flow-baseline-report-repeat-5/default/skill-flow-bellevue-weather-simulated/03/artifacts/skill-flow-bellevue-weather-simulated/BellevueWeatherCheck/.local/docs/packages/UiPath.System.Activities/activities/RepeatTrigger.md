# Repeat Trigger

`UiPath.Core.Activities.RepeatTrigger`

Triggers repeatedly at the configured time interval.

**Package:** `UiPath.System.Activities`
**Category:** Triggers

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Interval` | Interval | `InArgument` | `TimeSpan` | Yes | - | Time between trigger events. |

### Output

| Name | Type | Description |
|------|------|-------------|
| `EventTimestamp` | `DateTime` | Timestamp generated when the trigger event fires. |

## XAML Example

```xml
<ui:RepeatTrigger
    DisplayName="Repeat Trigger"
    Interval="[TimeSpan.FromMinutes(5)]" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- The first event is raised after one full `Interval`.
- Use this activity inside a trigger scope or a trigger-enabled workflow surface.
