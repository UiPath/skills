# Browser File Picker Scope

`UiPath.UIAutomationNext.Activities.NBrowserFilePickerScope`

Captures and handles a browser file picker dialog.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Browser
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  | The UI element to perform the action on. |
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |

### Configuration

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `Mode` | Mode | Property | `NBrowserFilePickerScopeMode` | `SingleFile` |  | Respond with a single file or multiple files to the file picker. |
| `SingleFilePath` | File path | InArgument | `string` |  |  | The file path to input in the file picker. |
| `MultiFilePaths` | File paths | InArgument | `List<string>` |  |  | The file paths to input in the file picker. |
| `WaitForDialogToAppearTimeout` | Wait for dialog to appear timeout | InArgument | `double` |  |  | The amount of time (in seconds) to wait for the dialog to appear after children activities finish executing. The default value is 30 seconds. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `OutUiElement` | Output element | `UiElement` | Output a UI Element to use in other activities as an Input UI Element. |

### Common

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` |  |  | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `Timeout` | Timeout | InArgument | `double` |  |  | The amount of time (in seconds) to wait for the operation to be performed before generating an error. The default value is 30 seconds. |
| `DelayBefore` | Delay before | InArgument | `double` |  |  | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## XAML Example

```xml
<ua:NApplicationCard
    xmlns:ua="clr-namespace:UiPath.UIAutomationNext.Activities;assembly=UiPath.UIAutomationNext.Activities"
    DisplayName="Use Application/Browser"
    Version="V2">
  <ua:NBrowserFilePickerScope
      DisplayName="Browser File Picker Scope"
      Mode="SingleFile"
      SingleFilePath="[&quot;C:\Documents\upload.pdf&quot;]"
      Version="V5">
    <ua:NBrowserFilePickerScope.Target>
      <ua:TargetAnchorable
          FullSelectorArgument="[&quot;&lt;webctrl tag='HTML' /&gt;&quot;]"
          SearchSteps="Selector"
          Version="V6" />
    </ua:NBrowserFilePickerScope.Target>
    <!-- Place activities that trigger the file picker here -->
  </ua:NBrowserFilePickerScope>
</ua:NApplicationCard>
```

## Notes

- This activity must be placed inside a **Use Application/Browser** (`NApplicationCard`) scope.
- Place the activities that trigger the file picker dialog (e.g., clicking an upload button) inside the scope body.
- Use `SingleFile` mode with `SingleFilePath` for single file uploads, or `MultipleFiles` mode with `MultiFilePaths` for multi-file uploads.
- The `DelayAfter` property is hidden in this activity.
