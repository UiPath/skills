# Read Status Bar

`UiPath.UIAutomationNext.Activities.NSAPReadStatusbar`

Reads the message displayed in the Status Bar on the bottom of the SAP GUI window.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.SAP
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `MessageType` | Message Type | `string` | Enables you to store the type of message in a variable. Variable created in this field is of String type. |
| `MessageText` | Message Text | `string` | Enables you to store the full message text in a variable. Variable created in this field is of String type. |
| `MessageId` | Message ID | `string` | Enables you to store the ID of the message in a variable. Variable created in this field is of String type. |
| `MessageNumber` | Message Number | `string` | Enables you to store the number of the message in a variable. Variable created in this field is of String type. |
| `MessageData` | Message Data | `string[]` | Enables you to store the data from the status of message in a variable. Variable created in this field is of Array type. |

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
  <ua:NSAPReadStatusbar
      DisplayName="Read Status Bar"
      MessageText="[statusMessage]"
      MessageType="[statusType]"
      Version="V5" />
</ua:NApplicationCard>
```

## Notes

- This activity must be placed inside a `UiPath.UIAutomationNext.Activities.NApplicationCard` scope.
- The `Version` attribute is mandatory and must be set to `V5`.
- Assembly: `UiPath.UIAutomationNext.Activities`
