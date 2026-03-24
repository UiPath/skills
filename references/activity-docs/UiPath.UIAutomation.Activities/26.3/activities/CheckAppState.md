# Check App State

`UiPath.UIAutomationNext.Activities.NCheckState`

Ensures the automated app is in a specific state, by verifying if a UI element exists or not. A set of user-defined actions are executed based on the detected state.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Application

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  | The UI element to perform the action on. |
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |

### Configuration

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `Timeout` | Timeout (seconds) | InArgument | `double` |  |  | Default value: 5 seconds. The amount of time to wait for the element to appear or disappear, before executing one of the two activity blocks. |
| `Mode` | Wait for (appear/disappear) | Property | `NCheckStateMode` | `WaitAppear` |  | Defines whether to wait for an element to appear or disappear, before executing one of the two activity blocks. |
| `CheckVisibility` | Check visibility | Property | `bool` | `false` |  | When enabled, the activity also checks whether the UI element is visible or not. |
| `HealingAgentBehavior` | Healing Agent mode | InArgument | `NChildHealingAgentBehavior` |  |  | Configures the Healing Agent actions if they are allowed by Governance or Orchestrator process/job/trigger level settings |
| `BranchVisibility` | Toggle branches | Property | `object` |  |  | Configure the visibility of the 'Target appears' and 'Target does not appear' containers. You can work with both containers, either one of them, or none. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Exists` | Result | `bool` | A true or false value indicating the detected state of the target. |
| `OutUiElement` | Output element | `UiElement` | Output a UI Element to use in other activities as an Input UI Element. |

### Common

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `DelayBefore` | Delay before | InArgument | `double` |  |  | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## XAML Example

```xml
<ua:NCheckState
    xmlns:ua="clr-namespace:UiPath.UIAutomationNext.Activities;assembly=UiPath.UIAutomationNext.Activities"
    DisplayName="Check App State"
    Mode="WaitAppear"
    Timeout="[5]"
    Exists="[elementExists]"
    Version="V5">
  <ua:NCheckState.Target>
    <ua:TargetAnchorable
        FullSelectorArgument="[&quot;&lt;webctrl tag='DIV' id='login-form' /&gt;&quot;]"
        SearchSteps="Selector"
        Version="V6" />
  </ua:NCheckState.Target>
</ua:NCheckState>
```

## Notes

- This activity does not require a mandatory parent scope and can be used standalone or inside a **Use Application/Browser** (`NApplicationCard`) scope.
- Contains two execution branches: "Target appears" and "Target does not appear". Activities placed in each branch are executed based on the detected state.
- The default timeout is 5 seconds (different from most other activities which default to 30 seconds).
- Use `CheckVisibility` to also verify that the element is visually visible on screen, not just present in the DOM.
- The `ContinueOnError` and `DelayAfter` properties are hidden in this activity.
