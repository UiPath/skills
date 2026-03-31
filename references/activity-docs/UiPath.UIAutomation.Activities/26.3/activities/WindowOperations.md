# Window Operation

`UiPath.UIAutomationNext.Activities.NWindowOperation`

Perform various operations on the specified window element.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Application
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  |  |
| `Operation` | Operation | InArgument | `NWindowOperationType` |  |  |  | The operation to be performed on the given window. |
| `X` | X | InArgument | `int` |  |  |  | The new position of the window's left edge, in relation to the desktop. |
| `Y` | Y | InArgument | `int` |  |  |  | The new position of the window's top edge, in relation to the desktop. |
| `Width` | Width | InArgument | `int` |  |  |  | The new width of the window. |
| `Height` | Height | InArgument | `int` |  |  |  | The new height of the window. |
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |

### Configuration

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
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

## How to create a new Window Operation

To generate the default XAML for this activity, run the following command:

```bash
uip rpa get-default-activity-xaml --activity-class-name UiPath.UIAutomationNext.Activities.NWindowOperation --use-studio
```
## Notes

- This activity must be placed inside a **Use Application/Browser** (`NApplicationCard`) scope.
- The `Operation` property determines the window action (e.g., Maximize, Minimize, Restore, Move, Resize, Close).
- The `X`, `Y`, `Width`, and `Height` properties are only relevant for Move and Resize operations.
