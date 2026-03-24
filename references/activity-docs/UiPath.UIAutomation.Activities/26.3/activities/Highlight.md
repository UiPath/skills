# Highlight

`UiPath.UIAutomationNext.Activities.NHighlight`

Visually highlights a specified UI element by surrounding it in a box.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Application
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  | The UI element to perform the action on. |
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |

### Configuration

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `HighlightTime` | Duration | InArgument | `double` |  |  | The amount of time (in seconds) for which to highlight the target element. The default duration is 2 seconds. |
| `Color` | Color | Property | `Color` |  |  | The color of the box that surrounds the highlighted element. |
| `HealingAgentBehavior` | Healing Agent mode | InArgument | `NChildHealingAgentBehavior` |  |  | Configures the Healing Agent actions if they are allowed by Governance or Orchestrator process/job/trigger level settings |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `OutUiElement` | Output element | `UiElement` | Output a UI Element to use in other activities as an Input UI Element. |

### Common

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` |  |  | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `Timeout` | Timeout | InArgument | `double` |  |  | The amount of time (in seconds) to wait for the operation to be performed before generating an error. The default value is 30 seconds. |
| `DelayAfter` | Delay after | InArgument | `double` |  |  | Delay (in seconds) after this activity is completed, before next activity starts. The default amount of time is 0.3 seconds. |
| `DelayBefore` | Delay before | InArgument | `double` |  |  | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## XAML Example

```xml
<ua:NApplicationCard
    xmlns:ua="clr-namespace:UiPath.UIAutomationNext.Activities;assembly=UiPath.UIAutomationNext.Activities"
    DisplayName="Use Application/Browser"
    Version="V2">
  <ua:NHighlight
      DisplayName="Highlight 'Content'"
      HighlightTime="[2]"
      Color="Red"
      Version="V5">
    <ua:NHighlight.Target>
      <ua:TargetAnchorable
          FullSelectorArgument="[&quot;&lt;webctrl tag='DIV' id='main-content' /&gt;&quot;]"
          SearchSteps="Selector"
          Version="V6" />
    </ua:NHighlight.Target>
  </ua:NHighlight>
</ua:NApplicationCard>
```

## Notes

- This activity must be placed inside a **Use Application/Browser** (`NApplicationCard`) scope.
- The default highlight duration is 2 seconds.
- Useful for debugging and demonstrating which UI elements the automation interacts with.
- The highlight color can be customized using the `Color` property.
