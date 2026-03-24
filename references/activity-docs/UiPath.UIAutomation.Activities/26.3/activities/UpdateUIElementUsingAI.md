# Update UI Element

`UiPath.Semantic.Activities.NSetValue`

Uses AI to seamlessly update a UI element's state/value.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Semantic
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  |  |
| `Value` | Value | InArgument | `string` |  |  |  | The value that will be set on the field. |
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |

### Configuration

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `EnableValidation` | Enable validation | Property | `bool` | Enables execution validation for the run-time value. An exception will be thrown if the internal validation mechanism detects an invalid value after the execution. |
| `InteractionMode` | Input mode | InArgument | `NChildInteractionMode` | The method used to execute the click. |
| `HealingAgentBehavior` | Healing Agent mode | InArgument | `NChildHealingAgentBehavior` | Configures the Healing Agent actions if they are allowed by Governance or Orchestrator process/job/trigger level settings. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `OutUiElement` | Output element | `UiElement` | Output a UI Element to use in other activities as an Input UI Element. |

### Common

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `Timeout` | Timeout | InArgument | `double` | The amount of time (in seconds) to wait for the operation to be performed before generating an error. The default value is 30 seconds. |
| `DelayAfter` | Delay after | InArgument | `double` | Delay (in seconds) after this activity is completed, before next activity starts. The default amount of time is 0.3 seconds. |
| `DelayBefore` | Delay before | InArgument | `double` | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## XAML Example

```xml
<ua:NApplicationCard
    xmlns:ua="clr-namespace:UiPath.UIAutomationNext.Activities;assembly=UiPath.UIAutomationNext.Activities"
    xmlns:semantic="clr-namespace:UiPath.Semantic.Activities;assembly=UiPath.UIAutomationNext.Activities"
    DisplayName="Use Application/Browser"
    Version="V2">
  <semantic:NSetValue
      DisplayName="Update UI Element"
      Value="[valueToSet]"
      Version="V5">
    <semantic:NSetValue.Target>
      <ua:TargetAnchorable
          FullSelectorArgument="[&quot;&lt;webctrl tag='INPUT' id='email' /&gt;&quot;]"
          SearchSteps="Selector"
          Version="V6" />
    </semantic:NSetValue.Target>
  </semantic:NSetValue>
</ua:NApplicationCard>
```

## Notes

- This activity must be placed inside a **Use Application/Browser** (`NApplicationCard`) scope.
- The `Value` property specifies the string value to set on the target UI element.
- Enable `EnableValidation` to verify that the element was correctly updated after AI execution.
- AI determines the best interaction method to update the UI element based on its type (text field, dropdown, checkbox, etc.).
