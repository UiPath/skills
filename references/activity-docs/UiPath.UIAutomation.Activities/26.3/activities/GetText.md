# Get Text

`UiPath.UIAutomationNext.Activities.NGetText`

Extracts the text from a specified UI element.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Application
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  | The UI element to perform the action on. |
| `ScrapingMethod` | Scraping method | Property | `NScrapingMethod` |  | `NScrapingMethod.Default` |  | The scraping method used to get the text. |
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `HealingAgentBehavior` | Healing Agent mode | `NChildHealingAgentBehavior` |  | Configures the Healing Agent actions if they are allowed by Governance or Orchestrator process/job/trigger level settings |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Text` | Text | `OutArgument` | Where to save the copied text. |
| `TextString` | Text | `string` | Where to save the copied text. |
| `WordsInfo` | Words info | `IEnumerable<NWordInfo>` | Where to save the words info from text. |
| `OutUiElement` | Output element | `UiElement` | Output a UI Element to use in other activities as an Input UI Element. |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` |  | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `Timeout` | Timeout | InArgument | `double` |  | The amount of time (in seconds) to wait for the operation to be performed before generating an error. The default value is 30 seconds. |
| `DelayAfter` | Delay after | InArgument | `double` |  | Delay (in seconds) after this activity is completed, before next activity starts. The default amount of time is 0.3 seconds. |
| `DelayBefore` | Delay before | InArgument | `double` |  | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## XAML Example

Selector properties use plain XML-escaped attribute strings (not `CSharpValue` or `[bracket]` expressions). `ScopeSelectorArgument` (window selector) must be set on every `TargetAnchorable`.

```xml
<uix:NApplicationCard
    xmlns:uix="http://schemas.uipath.com/workflow/activities/uix"
    DisplayName="Use Application/Browser"
    Version="V2">
  <uix:NGetText
      DisplayName="Get Text 'Label'"
      Version="V5">
    <uix:NGetText.Target>
      <uix:TargetAnchorable
          FullSelectorArgument="&lt;webctrl tag='SPAN' id='labelText' /&gt;"
          ScopeSelectorArgument="&lt;wnd app='myapp.exe' title='My App' /&gt;"
          SearchSteps="Selector"
          Version="V6" />
    </uix:NGetText.Target>
  </uix:NGetText>
</uix:NApplicationCard>
```

## Notes

- This activity must be placed inside a `UiPath.UIAutomationNext.Activities.NApplicationCard` scope.
- The `Version` attribute is mandatory and must be set to `V5`.
- `ScopeSelectorArgument` must be set on the `TargetAnchorable` to match the parent `NApplicationCard`'s window selector. Without it, the Get Text activity will fail at runtime with `NodeNotFoundException`.
- Assembly: `UiPath.UIAutomationNext.Activities`
