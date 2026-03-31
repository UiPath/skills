# Get Browser Data

`UiPath.UIAutomationNext.Activities.NGetBrowserData`

Exports the session data from the specified browser instance.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Browser

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Browser` | Browser | InArgument | `Browser` |  |  |  | The source browser object |
| `BrowserType` | Browser type | InArgument | `NBrowserType` |  |  |  | Choose the type of browser you want to use. The following options are available: Chrome, Edge. |

### Configuration

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `SourceUserDataFolder` | Source User Data Folder | InArgument | `string` |  |  | The source user data folder used by the running browser instance, from where the cookies will be exported. Defaults to browser's data folder setting, if not set. |
| `UserProfile` | User Profile | InArgument | `string` |  |  | All the browser profiles defined within the selected source user data folder. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `SessionData` | Session Data | `string` | Variable containing the session data. |

### Common

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` |  |  | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `DelayAfter` | Delay after | InArgument | `double` |  |  | Delay (in seconds) after this activity is completed, before next activity starts. The default amount of time is 0.3 seconds. |
| `DelayBefore` | Delay before | InArgument | `double` |  |  | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## How to create a new Get Browser Data

To generate the default XAML for this activity, run the following command:

```bash
uip rpa get-default-activity-xaml --activity-class-name UiPath.UIAutomationNext.Activities.NGetBrowserData --use-studio
```
## Notes

- This activity exports session data (cookies, local storage, etc.) from a browser instance.
- The exported data can be stored in a variable and later restored using the `Set Browser Data` activity.
- Specify the `Browser type` to target a specific browser (Chrome or Edge).
- The `Source User Data Folder` and `User Profile` options allow fine-grained control over which profile's data is exported.
