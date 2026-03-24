# Type Into

`UiPath.UIAutomationNext.Activities.NTypeInto`

Enters text in a specified UI element, for example a text box.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Application
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  | The UI element to perform the action on. |
| `Text` | Text | InArgument | `string` |  |  |  | The text to enter. You can add special keys from the Text Builder. |
| `SecureText` | Secure text | InArgument | `SecureString` |  |  |  | The SecureString value to enter. |
| `VerifyOptions` | Verify execution | Property | `VerifyExecutionTypeIntoOptions` |  |  |  | Define activity execution verification step. |
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `DelayBetweenKeys` | Delay between keys | `double` |  | Delay (in seconds) between consecutive keystrokes. The maximum value is 1 second. |
| `ActivateBefore` | Activate | `bool` |  | Bring the UI element to the foreground and activate it before entering the text. |
| `ClickBeforeMode` | Click before typing | `NClickMode` |  | Performs a click in the specified text-field before typing, in order to activate it. |
| `EmptyFieldMode` | Empty field | `NEmptyFieldMode` |  | Clear the existing content of the text-field before typing the text. Multiple methods available, compatible with various text-field types and applications. |
| `ClipboardMode` | Type by clipboard | `NTypeByClipboardMode` |  | Indicates whether the clipboard is used for typing the given text. |
| `DeselectAfter` | Deselect at end | `bool` |  | This option adds a Complete event after the text entry, in order to trigger certain UI responses in web browsers. |
| `AlterIfDisabled` | Alter disabled element | `bool` |  | When selected, the activity executes the action even if the target element is disabled. Property does not apply if the input mode is Hardware Events. The default value is false. |
| `InteractionMode` | Input mode | `NChildInteractionMode` |  | The method used to execute the click. |
| `HealingAgentBehavior` | Healing Agent mode | `NChildHealingAgentBehavior` |  | Configures the Healing Agent actions if they are allowed by Governance or Orchestrator process/job/trigger level settings |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `OutUiElement` | Output element | `UiElement` | Output a UI Element to use in other activities as an Input UI Element. |

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
  <ua:NTypeInto
      DisplayName="Type Into 'Text'"
      Text="[inputText]"
      ActivateBefore="True"
      ClickBeforeMode="Single"
      EmptyFieldMode="SingleLine"
      Version="V5">
    <ua:NTypeInto.Target>
      <ua:TargetAnchorable
          FullSelectorArgument="[&quot;&lt;webctrl tag='INPUT' type='text' /&gt;&quot;]"
          SearchSteps="Selector"
          Version="V6" />
    </ua:NTypeInto.Target>
  </ua:NTypeInto>
</ua:NApplicationCard>
```

## Notes

- This activity must be placed inside a `UiPath.UIAutomationNext.Activities.NApplicationCard` scope.
- The `Version` attribute is mandatory and must be set to `V5`.
- Assembly: `UiPath.UIAutomationNext.Activities`
