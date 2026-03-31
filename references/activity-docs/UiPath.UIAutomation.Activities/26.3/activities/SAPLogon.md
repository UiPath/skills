# SAP Logon

`UiPath.UIAutomationNext.Activities.NSAPLogon`

Use the activity to directly log on to an SAP system. Provide the exact SAP connection name from the SAP Logon or the SAP Logon Pad window used to log on to your SAP system.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.SAP

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `TargetApp` | Target application | Property | `TargetApp` |  |  |  | Expand for more options. |

### Configuration

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `Retries` | Number Of Retries | InArgument | `int` |  |  | The number of times that the activity is trying to connect to SAP Scripting interface. (Default: 5) |
| `DelayBetweenRetries` | Retry Interval | InArgument | `double` |  |  | Specifies the amount of time (in seconds) between each retry. The default amount of time is 0.5 seconds. |
| `InteractionMode` | Input mode | Property | `NInteractionMode` | `Constants.DefaultInteractionMode` |  | The method used to generate keyboard and mouse input. |
| `AttachMode` | Window attach mode | Property | `NAppAttachMode` | `NAppAttachMode.ByInstance` |  | Defines where inner activities search for their target elements. |
| `OpenMode` | Open | InArgument | `NAppOpenMode` |  |  | Defines whether to open the target application before executing the activities in it. |
| `CloseMode` | Close | InArgument | `NAppCloseMode` |  |  | Defines whether to close the target application after executing the activities in it. The default value is same as 'If opened by Use App/Browser'. |
| `WindowResize` | Resize window | Property | `NWindowResize` | `NWindowResize.None` |  | Defines whether the application/browser is resized when initialized. |
| `DialogHandling` | Dialog Handling | Property | `DialogHandling` |  |  | Configure auto-dismissal of JavaScript dialogs. |
| `HealingAgentBehavior` | Healing Agent mode | InArgument | `NHealingAgentBehavior` |  |  | Configures the Healing Agent actions if they are allowed by Governance or Orchestrator process/job/trigger level settings |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `OutUiElement` | Output element | `UiElement` | Output a UI Element to use in other activities as an Input UI Element. |

### Common

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` |  |  | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `Timeout` | Timeout | InArgument | `double` |  |  | The amount of time (in seconds) to wait for the operation to be performed before generating an error. The default value is 30 seconds. |

## How to create a new SAP Logon

To generate the default XAML for this activity, run the following command:

```bash
uip rpa get-default-activity-xaml --activity-class-name UiPath.UIAutomationNext.Activities.NSAPLogon --use-studio
```
## Notes

- This activity acts as a scope (similar to `Use Application/Browser`) specifically for SAP systems.
- It extends `NApplicationCard`, so it uses `Version="V2"` instead of `V5`.
- Provide the exact SAP connection name from the SAP Logon or SAP Logon Pad window.
- The `Number Of Retries` and `Retry Interval` properties control the retry behavior when connecting to the SAP Scripting interface.
- Inner activities such as Click, Type Into, and Get Text can be placed inside this scope to interact with the SAP GUI.
