# Keyboard Shortcuts

`UiPath.UIAutomationNext.Activities.NKeyboardShortcuts`

Sends one or more keyboard shortcuts to a UI element.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Application
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  | The UI element to perform the action on. |
| `ShortcutsArgument` | Shortcuts | InArgument | `string` |  |  |  | The keyboard shortcuts to be sent. |
| `Shortcuts` | Shortcuts | Property | `string` |  |  |  | The keyboard shortcuts to be sent. |
| `VerifyOptions` | Verify execution | Property | `VerifyExecutionOptions` |  |  |  | Define activity execution verification step. |
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |

### Configuration

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `ActivateBefore` | Activate | InArgument | `bool` |  |  | Bring the target UI element to the foreground and activate it before sending the shortcut. |
| `DelayBetweenShortcuts` | Delay between shortcuts | InArgument | `double` |  |  | Delay (in seconds) between consecutive shortcuts. |
| `DelayBetweenKeys` | Delay between keys | InArgument | `double` |  |  | Delay (in seconds) between consecutive keystrokes. The maximum value is 1 second. |
| `ClickBeforeMode` | Click before typing | InArgument | `NClickMode` |  |  | The type of click to execute in the specified UI element before sending the shortcut. |
| `InteractionMode` | Input mode | InArgument | `NChildInteractionMode` |  |  | The method used to execute the click. |
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

## How to create a new Keyboard Shortcuts

To generate the default XAML for this activity, run the following command:

```bash
uip rpa get-default-activity-xaml --activity-class-name UiPath.UIAutomationNext.Activities.NKeyboardShortcuts
```
## Notes

- This activity must be placed inside a **Use Application/Browser** (`NApplicationCard`) scope.
- Supports sending multiple shortcuts in sequence, with configurable delay between them.
- Use `ActivateBefore` to ensure the target element has focus before sending shortcuts.
- The `ClickBeforeMode` property allows clicking the element before sending the shortcuts to ensure focus.
