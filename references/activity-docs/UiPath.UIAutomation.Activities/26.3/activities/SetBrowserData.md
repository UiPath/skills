# Set Browser Data

`UiPath.UIAutomationNext.Activities.NSetBrowserData`

Imports the session data into a specified browser instance.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Browser

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Browser` | Browser | InArgument | `Browser` |  |  |  | The target browser object |
| `SessionData` | Session Data | InArgument | `string` |  |  |  | Variable where the session data is stored. |

### Common

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` |  |  | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `DelayAfter` | Delay after | InArgument | `double` |  |  | Delay (in seconds) after this activity is completed, before next activity starts. The default amount of time is 0.3 seconds. |
| `DelayBefore` | Delay before | InArgument | `double` |  |  | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## How to create a new Set Browser Data

To generate the default XAML for this activity, run the following command:

```bash
uip rpa get-default-activity-xaml --activity-class-name UiPath.UIAutomationNext.Activities.NSetBrowserData --use-studio
```
## Notes

- This activity imports previously exported session data into a browser instance.
- Use in combination with the `Get Browser Data` activity to transfer browser session data between automation runs.
- The `Session Data` input should contain the string previously obtained from `Get Browser Data`.
