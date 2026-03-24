# Keypress Event Trigger

`UiPath.UIAutomationNext.Activities.NKeyboardTrigger`

Setup a key pressed event trigger on the indicated UI Element.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Application
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  | The UI element to perform the action on. |
| `Key` | Key | InArgument | `string` |  |  |  | The key that is monitored. Special keys are supported and you can select them from the activity drop-down list. |

### Configuration

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `KeyModifiers` | Key modifiers | InArgument | `NKeyModifiers` |  |  | Adds a key modifier to the key sequence to be monitored. |
| `BlockEvent` | Block event | InArgument | `bool` |  |  | Specifies whether the event is blocked from acting on the indicated element. If False, the event is executed against the element. If True, the event is blocked and can be later replayed within the activity handler, by using the ReplayUserEvent activity. |
| `IncludeChildren` | Include children | InArgument | `bool` |  |  | When selected, the children of the specified UI element are also monitored. By default, this check box is selected. |
| `Mode` | Trigger mode | InArgument | `NKeyTriggerMode` |  |  | Specifies if the event is triggered on key down or key up. |
| `SchedulingMode` | Scheduling mode | Property | `TriggerActionSchedulingMode` |  |  | It specifies how to execute the actions when a trigger is fired. Sequential: actions are executed one after another; Concurrent: actions execution can overlap; OneTime: executes one action and exits monitoring. For Sequential and Concurrent modes the monitoring continues until either the user stops the execution or a Break activity is met. |

## XAML Example

```xml
<ua:NApplicationCard
    xmlns:ua="clr-namespace:UiPath.UIAutomationNext.Activities;assembly=UiPath.UIAutomationNext.Activities"
    DisplayName="Use Application/Browser"
    Version="V2">
  <ua:NKeyboardTrigger
      DisplayName="Keypress Event Trigger"
      Key="Enter"
      KeyModifiers="None"
      Version="V5">
    <ua:NKeyboardTrigger.Target>
      <ua:TargetAnchorable
          FullSelectorArgument="[&quot;&lt;webctrl tag='INPUT' id='search' /&gt;&quot;]"
          SearchSteps="Selector"
          Version="V6" />
    </ua:NKeyboardTrigger.Target>
    <!-- Handler activities go here -->
  </ua:NKeyboardTrigger>
</ua:NApplicationCard>
```

## Notes

- This activity requires a parent `Use Application/Browser` scope.
- Use the `Key` property to specify which key press to monitor.
- The `Block event` option prevents the key press from reaching the target element, allowing custom handling.
- The `Scheduling mode` controls how multiple trigger firings are handled (sequentially, concurrently, or one-time).
- When `Include children` is enabled, key presses on child elements of the target are also monitored.
