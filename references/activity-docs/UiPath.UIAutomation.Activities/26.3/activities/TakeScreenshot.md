# Take Screenshot

`UiPath.UIAutomationNext.Activities.NTakeScreenshot`

Takes a screenshot of an application or UI element.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Application
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  | The UI element to perform the action on. |
| `FileName` | File name | InArgument | `string` |  |  |  | The name of the file where the screenshot of the specified UI element will be saved. |
| `FileNameMode` | Auto increment | InArgument | `NFileNameMode` |  |  |  | Defines what to append to the filename in case of filename conflicts. |
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |

### Configuration

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `HealingAgentBehavior` | Healing Agent mode | InArgument | `NChildHealingAgentBehavior` |  |  | Configures the Healing Agent actions if they are allowed by Governance or Orchestrator process/job/trigger level settings |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `SavedTo` | Saved file path | `OutArgument` | The full path of the screenshot file including the appended suffix, if Auto-increment was used; used when Output is set to 'File' |
| `OutImage` | Saved image | `Image` | The screenshot saved as Image; used when Output is set to 'Image'. |
| `OutFile` | Saved file | `ILocalResource` | The screenshot saved as a png file. |
| `OutUiElement` | Output element | `UiElement` | Output a UI Element to use in other activities as an Input UI Element. |

### Common

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` |  |  | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `Timeout` | Timeout | InArgument | `double` |  |  | The amount of time (in seconds) to wait for the operation to be performed before generating an error. The default value is 30 seconds. |
| `DelayBeforeScreenshot` | Delay before screenshot | InArgument | `double` |  |  | Delay (in seconds) between bringing the UI element into foreground and actually taking the screenshot. The default amount of time is 0.2 seconds. |
| `DelayBefore` | Delay before | InArgument | `double` |  |  | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## XAML Example

```xml
<ua:NApplicationCard
    xmlns:ua="clr-namespace:UiPath.UIAutomationNext.Activities;assembly=UiPath.UIAutomationNext.Activities"
    DisplayName="Use Application/Browser"
    Version="V2">
  <ua:NTakeScreenshot
      DisplayName="Take Screenshot"
      FileName="[&quot;screenshot.png&quot;]"
      Version="V5">
    <ua:NTakeScreenshot.Target>
      <ua:TargetAnchorable
          FullSelectorArgument="[&quot;&lt;webctrl tag='DIV' id='content' /&gt;&quot;]"
          SearchSteps="Selector"
          Version="V6" />
    </ua:NTakeScreenshot.Target>
  </ua:NTakeScreenshot>
</ua:NApplicationCard>
```

## Notes

- This activity must be placed inside a **Use Application/Browser** (`NApplicationCard`) scope.
- Screenshots can be saved as a file (using `FileName` and `SavedTo`) or as an in-memory image (using `OutImage`).
- The `FileNameMode` property controls behavior when a file with the same name already exists.
- The `DelayAfter` property is hidden in this activity.
