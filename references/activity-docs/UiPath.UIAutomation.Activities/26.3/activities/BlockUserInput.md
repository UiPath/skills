# Block User Input

`UiPath.UIAutomationNext.Activities.NBlockUserInput`

Suppress keyboard/mouse input until the set key combination is pressed, or timeout exceeded.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Application

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  |  |
| `BlockType` | Block | InArgument | `NBlockInputType` |  |  |  | Indicates whether both keyboard and/or mouse are blocked. Default value is Both, which means that both keyboard and mouse are blocked. |
| `KeyModifiers` | Unblock using key modifiers | InArgument | `NKeyModifiers` |  |  |  | Indicates the key modifiers that are part of the unblock key sequence, alongside the key. The unblock key sequence allows unblocking the user input, while the activity is still executing. |
| `Keys` | Unblock using key | InArgument | `string` |  |  |  | Indicates the key that is part of the unblock key sequence, alongside the key modifiers. The unblock key sequence allows unblocking the user input, while the activity is still executing. |
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |

### Configuration

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `DisableUnblock` | Disable automatic unblock | InArgument | `bool` | Indicates whether to disable the automatic unblock of input after the inner activities are executed and the scope finishes execution. User input can be manually unblocked using the 'Unblock User Input' activity. Default value is false. |
| `Allow3rdPartyApps` | Allow 3rd party applications | InArgument | `bool` | Indicates whether input sent by other 3rd party applications is allowed or also blocked. Default value is false. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `OutUiElement` | Output element | `UiElement` | Output a UI Element to use in other activities as an Input UI Element. |

### Common

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` | Continue executing the activities in the automation if this activity fails. The default value is False. |

## How to create a new Block User Input

To generate the default XAML for this activity, run the following command:

```bash
uip rpa get-default-activity-xaml --activity-class-name UiPath.UIAutomationNext.Activities.NBlockUserInput --use-studio
```
## Notes

- No mandatory parent scope is required for this activity.
- Use the `BlockType` property to control whether keyboard, mouse, or both input types are blocked.
- Configure `KeyModifiers` and `Keys` to define a key combination that allows the user to manually unblock input.
- When `DisableUnblock` is set to true, input remains blocked until an explicit **Unblock User Input** activity is executed.
- The `Allow3rdPartyApps` option controls whether input from other automation tools or third-party applications is also blocked.
