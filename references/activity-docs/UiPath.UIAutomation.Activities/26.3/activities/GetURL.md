# Get URL

`UiPath.UIAutomationNext.Activities.NGetUrl`

Returns the URL from the current browser.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Browser
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Configuration

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `WaitForReady` | Wait for page load | InArgument | `NWaitForReady` |  |  | Before performing the action, wait for the application to become ready to accept input. The options are: None -- does not wait for the target to be ready; Interactive -- waits until only a part of the app is loaded; Complete -- waits for the entire app to be loaded. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `CurrentUrl` | Current URL | `string` | Where to save the current url. |

### Common

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` |  |  | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `Timeout` | Timeout | InArgument | `double` |  |  | The amount of time (in seconds) to wait for the operation to be performed before generating an error. The default value is 30 seconds. |
| `DelayAfter` | Delay after | InArgument | `double` |  |  | Delay (in seconds) after this activity is completed, before next activity starts. The default amount of time is 0.3 seconds. |
| `DelayBefore` | Delay before | InArgument | `double` |  |  | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## XAML Example

```xml
<ui:NApplicationCard Version="V2" DisplayName="Use Application/Browser">
  <ui:NApplicationCard.Body>
    <ActivityAction x:TypeArguments="ui:IUiObject">
      <ui:NGetUrl Version="V5" DisplayName="Get URL"
                  CurrentUrl="[currentUrl]" />
    </ActivityAction>
  </ui:NApplicationCard.Body>
</ui:NApplicationCard>
```

## Notes

- This activity must be placed inside a **Use Application/Browser** (`NApplicationCard`) scope.
- Returns the URL of the currently active browser tab.
- Use the `WaitForReady` option to ensure the page is fully loaded before retrieving the URL.
