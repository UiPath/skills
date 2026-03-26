# Set Text

`UiPath.UIAutomationNext.Activities.NSetText`

Enters text in a specified UI element, for example a text box.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Application
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  | The UI element to perform the action on. |
| `Text` | Text | InArgument | `string` |  |  |  | The string to be written in the text attribute of the target element. Note, all the strings must be quoted. |
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |

### Configuration

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `CacheTargetElement` | Cache target element | Property | `bool` | `false` |  | Cache the target element when found and reuse it in the next activity run to improve the execution performance. |
| `AlterIfDisabled` | Alter disabled element | InArgument | `bool` |  |  | When selected, the activity executes the action even if the target element is disabled. Property does not apply if the input mode is Hardware Events. The default value is false. |
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

## How to create a new Set Text

To generate the default XAML for this activity, run the following command:

```bash
uip rpa get-default-activity-xaml --activity-class-name UiPath.UIAutomationNext.Activities.NSetText
```
## Notes

- This activity requires a parent `Use Application/Browser` scope.
- Unlike `Type Into`, `Set Text` directly sets the text attribute value of the target element without simulating keyboard input.
- Use `Cache target element` to improve performance when the same element is targeted repeatedly.
- The `Alter disabled element` option allows setting text even on disabled elements (does not apply to Hardware Events input mode).
