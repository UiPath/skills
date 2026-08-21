# Trigger Scope

`UiPath.Core.Activities.TriggerScope`

Runs an action when one of its contained triggers fires.

**Package:** `UiPath.System.Activities`
**Category:** Triggers

## Properties

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `SchedulingMode` | Scheduling Mode | `ActionSchedulingMode` | `Sequential` | Controls how trigger events are queued and how action executions overlap. |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue On Error | `InArgument` | `bool` | `null` | When `true`, child trigger or handler faults are logged, marked as handled, and the trigger scope is stopped so the workflow can continue after the scope. When `false`, the fault propagates. |

### Trigger and Action Containers

| Name | Type | Description |
|------|------|-------------|
| `Triggers` | `List<Activity>` | Trigger activities monitored by the scope. Hidden from the property grid and configured by the designer. |
| `Action` | `ActivityDelegate` | Activities executed when a trigger event is received. The delegate argument is `TriggerArgs`. |
| `Variables` | `Collection<Variable>` | Variables scoped to the trigger scope. |

## Enum Reference

**`ActionSchedulingMode`**

| Value | Description |
|-------|-------------|
| `Sequential` | Runs one action at a time and queues events. Redundant events from filterable triggers can be collapsed. |
| `Concurrent` | Starts a new action execution for each event. |
| `OneTime` | Runs once for the first event, then cancels the running triggers. |
| `SequentialCollapse` | Runs one action at a time and keeps only the latest queued event. |
| `SequentialDrop` | Cancels the currently running handler when a new event arrives, then runs the latest event. |

## XAML Example

```xml
<ui:TriggerScope
    DisplayName="Trigger Scope"
    SchedulingMode="Sequential">
  <ui:TriggerScope.Triggers>
    <ui:RepeatTrigger Interval="[TimeSpan.FromMinutes(5)]" />
  </ui:TriggerScope.Triggers>
  <ui:TriggerScope.Action>
    <ActivityAction x:TypeArguments="ut:TriggerArgs">
      <Sequence DisplayName="Action" />
    </ActivityAction>
  </ui:TriggerScope.Action>
</ui:TriggerScope>
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`
`xmlns:ut="clr-namespace:UiPath.Platform.Triggers;assembly=UiPath.Platform"`

## Notes

- The scope requires at least one trigger; validation fails when `Triggers` is empty.
- Use **Break** inside the action to stop the running trigger scope.
- The scope creates non-persistent bookmarks and can induce idle while waiting for trigger events.
