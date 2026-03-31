# Drag and Drop

`UiPath.UIAutomationNext.Activities.NDragAndDrop`

Executes a drag and drop operation from the source UI element to the destination UI element.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Application
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  | The UI element to perform the action on. |
| `DestinationTarget` | Destination Target | Property | `TargetAnchorable` |  |  |  | Target information that defines the destination UI element to be found. |
| `MouseButton` | Mouse button | InArgument | `NMouseButton` |  |  |  | The mouse button to click with. |
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |

### Configuration

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `KeyModifiers` | Key modifiers | InArgument | `NKeyModifiers` |  |  | One or more key modifiers to use in combination with the click. |
| `DelayBetweenActions` | Delay between actions | InArgument | `double` |  |  | Delay (in seconds) between the actions necessary to perform the drag and drop operation. The default amount of time is 0.3 seconds. |
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

## How to create a new Drag and Drop

To generate the default XAML for this activity, run the following command:

```bash
uip rpa get-default-activity-xaml --activity-class-name UiPath.UIAutomationNext.Activities.NDragAndDrop --use-studio
```
## Notes

- This activity requires a parent `Use Application/Browser` scope.
- Specify both a source `Target` (the element to drag) and a `Destination Target` (the element to drop onto).
- Use `Key modifiers` to hold modifier keys (e.g., Ctrl, Shift) during the drag and drop operation.
- The `Delay between actions` property controls the timing between the mouse down, move, and mouse up steps.
