# Navigate Browser

`UiPath.UIAutomationNext.Activities.NNavigateBrowser`

Allows basic navigation of the browser, like Go back, Go forward, Close, Refresh, Home.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Browser
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Configuration

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `Action` | Action | Property | `NNavigateBrowserAction` | `GoBack` |  | The action to perform in the browser. |

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
      <ui:NNavigateBrowser Version="V5" DisplayName="Navigate Browser"
                           Action="GoBack" />
    </ActivityAction>
  </ui:NApplicationCard.Body>
</ui:NApplicationCard>
```

## Notes

- This activity must be placed inside a **Use Application/Browser** (`NApplicationCard`) scope.
- The `Action` property supports browser navigation operations such as Go Back, Go Forward, Close, Refresh, and Home.
- This activity does not require a target element since it operates at the browser level.
- All properties with `browsable: false` (Target, InUiElement, OutUiElement, HealingAgentBehavior) are hidden from the designer and excluded from this documentation.
