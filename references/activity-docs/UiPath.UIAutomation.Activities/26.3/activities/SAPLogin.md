# SAP Login

`UiPath.UIAutomationNext.Activities.NSAPLogin`

Use the activity to log into an SAP system.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.SAP
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Username` | Username | InArgument | `string` |  |  |  | The username that you want to use for logging in. Text must be quoted. |
| `SecurePassword` | Secure Password | InArgument | `SecureString` |  |  |  | The secure text to be written in the Password field. Note: This field supports only SecureString variables. |
| `Password` | Password | InArgument | `string` |  |  |  | The password you want to use to log in. Text must be quoted. |
| `Client` | Client | InArgument | `string` |  |  |  | The SAP client number you want to log into. Text must be quoted. |
| `Language` | Language | InArgument | `string` |  |  |  | Decide which language you want to use to display screens, menus, and fields. Text must be quoted. |
| `Option` | Multiple Logon Option | Property | `NMultiLogonOption` |  |  |  | License Information for Multiple Logon opens if a user attempts to log onto the system several times. |
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `OutUiElement` | SAP Session Window | `UiElement` |  |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` |  | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `Timeout` | Timeout | InArgument | `double` |  | The amount of time (in seconds) to wait for the operation to be performed before generating an error. The default value is 30 seconds. |
| `DelayAfter` | Delay after | InArgument | `double` |  | Delay (in seconds) after this activity is completed, before next activity starts. The default amount of time is 0.3 seconds. |
| `DelayBefore` | Delay before | InArgument | `double` |  | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## XAML Example

```xml
<ua:NApplicationCard
    xmlns:ua="clr-namespace:UiPath.UIAutomationNext.Activities;assembly=UiPath.UIAutomationNext.Activities"
    DisplayName="Use Application/Browser"
    Version="V2">
  <ua:NSAPLogin
      DisplayName="SAP Login"
      Username="[username]"
      Client="800"
      Language="EN"
      Version="V5" />
</ua:NApplicationCard>
```

## Notes

- This activity must be placed inside a `UiPath.UIAutomationNext.Activities.NApplicationCard` scope.
- The `Version` attribute is mandatory and must be set to `V5`.
- Assembly: `UiPath.UIAutomationNext.Activities`
