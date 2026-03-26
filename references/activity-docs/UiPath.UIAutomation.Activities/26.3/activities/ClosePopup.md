# Close Popup

`UiPath.UIAutomationNext.Activities.NClosePopup`

Dismisses all popups that are on top of the application and block a target, using the configured close buttons.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Semantic

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `PopupException` | Popup detected exception | InArgument | `Exception` |  |  |  | The exception thrown when detecting a popup. |

### Configuration

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `PreferredButtons` | Popup close buttons | InArgument | `string[]` | The labels of the buttons used to close the popup. |
| `EnableAI` | AI-Enhanced mode | Property | `bool` | Leverage AI to close the popup. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `PopupHandled` | Popup handled | `NPopupHandleState` | Indicate if a popup was handled or not. |

### Common

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `PopupAppearTimeout` | Popup Appear Timeout | InArgument | `double` | The amount of time (in seconds) to wait for a popup to appear. The default amount of time is 30 seconds. |
| `DelayAfter` | Delay after | InArgument | `double` | Delay (in seconds) after this activity is completed, before next activity starts. The default amount of time is 0.3 seconds. |
| `DelayBefore` | Delay before | InArgument | `double` | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## How to create a new Close Popup

To generate the default XAML for this activity, run the following command:

```bash
uip rpa get-default-activity-xaml --activity-class-name UiPath.UIAutomationNext.Activities.NClosePopup
```
## Notes

- No mandatory parent scope is required for this activity.
- The `PreferredButtons` property accepts an array of button label strings that the activity will try to click to dismiss the popup.
- Enable `EnableAI` to leverage AI-based detection for identifying and closing popups.
- The `PopupHandled` output indicates whether a popup was successfully detected and dismissed.
- Use `PopupException` to pass in an exception from a previous activity that failed due to a popup blocking the target.
