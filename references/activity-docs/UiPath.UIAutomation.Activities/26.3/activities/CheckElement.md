# Check Element

`UiPath.UIAutomationNext.Activities.NCheckElement`

Checks if an element is enabled or disabled.

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
| `HealingAgentBehavior` | Healing Agent mode | InArgument | `NChildHealingAgentBehavior` |  |  | Configures the Healing Agent actions if they are allowed by Governance or Orchestrator process/job/trigger level settings |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Result` | Is enabled | `bool` | A true or false value indicating the detected state of the element. |
| `OutUiElement` | Output element | `UiElement` | Output a UI Element to use in other activities as an Input UI Element. |

### Common

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` |  |  | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `Timeout` | Timeout | InArgument | `double` |  |  | The amount of time (in seconds) to wait for the operation to be performed before generating an error. The default value is 30 seconds. |

## XAML Example

```xml
<uix:NApplicationCard
    xmlns:uix="http://schemas.uipath.com/workflow/activities/uix"
    DisplayName="Use Application/Browser"
    Version="V2">
  <uix:NCheckElement
      DisplayName="Check Element 'Submit'"
      Result="[isEnabled]"
      Version="V5">
    <uix:NCheckElement.Target>
      <uix:TargetAnchorable
          FullSelectorArgument="[&quot;&lt;webctrl tag='BUTTON' id='submit' /&gt;&quot;]"
          SearchSteps="Selector"
          Version="V6" />
    </uix:NCheckElement.Target>
  </uix:NCheckElement>
</uix:NApplicationCard>
```

## Notes

- This activity must be placed inside a **Use Application/Browser** (`NApplicationCard`) scope.
- Returns `true` if the target element is enabled, `false` if it is disabled.
- The `DelayBefore` and `DelayAfter` properties are hidden in this activity's designer.
