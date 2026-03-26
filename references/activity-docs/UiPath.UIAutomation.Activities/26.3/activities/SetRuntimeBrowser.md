# Set Runtime Browser

`UiPath.UIAutomationNext.Activities.NSetRuntimeBrowser`

Sets the currently active runtime browser.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Browser

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `BrowserType` | Browser type | InArgument | `NBrowserType` |  |  |  | Choose the type of browser you want to use. The following options are available: Chrome, Edge, Firefox, None. When converting from a String value, you can use NBrowserTypeFactory.From(String) helper method. |

### Common

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `Timeout` | Timeout | InArgument | `double` | The amount of time (in seconds) to wait for the operation to be performed before generating an error. The default value is 30 seconds. |
| `DelayAfter` | Delay after | InArgument | `double` | Delay (in seconds) after this activity is completed, before next activity starts. The default amount of time is 0.3 seconds. |
| `DelayBefore` | Delay before | InArgument | `double` | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## How to create a new Set Runtime Browser

To generate the default XAML for this activity, run the following command:

```bash
uip rpa get-default-activity-xaml --activity-class-name UiPath.UIAutomationNext.Activities.NSetRuntimeBrowser
```
## Notes

- No mandatory parent scope is required for this activity.
- Use this activity to switch the active browser type at runtime (e.g., Chrome, Edge, Firefox).
- The `NBrowserType.None` option can be used to clear the runtime browser setting.
- When converting from a string value, use the `NBrowserTypeFactory.From(String)` helper method.
