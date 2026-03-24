# Application Event Trigger

`UiPath.UIAutomationNext.Activities.NNativeEventTrigger`1`

Setup a trigger on a given event on the indicated UI Element.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Application
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  | The UI element to perform the action on. |
| `MatchSync` | Match sync | Property | `bool` |  | `false` |  | Indicates whether the matching of the target element selector is done synchronously or asynchronously. |
| `Selectors` | Selectors | InArgument | `IEnumerable<string>` |  |  |  | Optional collection of selectors to monitor for the indicated event; these selectors will be monitored alongside the indicated target. |

### Configuration

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `IncludeChildren` | Include children | InArgument | `bool` |  |  | When selected, the children of the specified UI element are also monitored. By default, this check box is selected. |
| `SchedulingMode` | Scheduling mode | Property | `TriggerActionSchedulingMode` |  |  | It specifies how to execute the actions when a trigger is fired. Sequential: actions are executed one after another; Concurrent: actions execution can overlap; OneTime: executes one action and exits monitoring. For Sequential and Concurrent modes the monitoring continues until either the user stops the execution or a Break activity is met. |

## XAML Example

```xml
<ua:NApplicationCard
    xmlns:ua="clr-namespace:UiPath.UIAutomationNext.Activities;assembly=UiPath.UIAutomationNext.Activities"
    DisplayName="Use Application/Browser"
    Version="V2">
  <ua:NNativeEventTrigger
      DisplayName="Application Event Trigger"
      IncludeChildren="True"
      Version="V5">
    <ua:NNativeEventTrigger.Target>
      <ua:TargetAnchorable
          FullSelectorArgument="[&quot;&lt;webctrl tag='DIV' id='content' /&gt;&quot;]"
          SearchSteps="Selector"
          Version="V6" />
    </ua:NNativeEventTrigger.Target>
    <!-- Handler activities go here -->
  </ua:NNativeEventTrigger>
</ua:NApplicationCard>
```

## Notes

- This activity requires a parent `Use Application/Browser` scope.
- Use this activity to set up triggers based on native application events on a specified UI element.
- The `Match sync` property controls whether target element matching occurs synchronously or asynchronously.
- Additional selectors can be provided via the `Selectors` property to monitor multiple elements for the same event.
- The `Scheduling mode` controls how multiple trigger firings are handled (sequentially, concurrently, or one-time).
