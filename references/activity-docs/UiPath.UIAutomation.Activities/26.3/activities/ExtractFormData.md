# Extract Form Data

`UiPath.Semantic.Activities.NExtractFormDataGeneric`

Uses AI to seamlessly extract form data.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Semantic
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  |  |
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |

### Configuration

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `HealingAgentBehavior` | Healing Agent mode | InArgument | `NChildHealingAgentBehavior` | Configures the Healing Agent actions if they are allowed by Governance or Orchestrator process/job/trigger level settings. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `FormData` | Form data | `T` | Where to save the extracted form data. |
| `OutUiElement` | Output element | `UiElement` | Output a UI Element to use in other activities as an Input UI Element. |

### Common

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `Timeout` | Timeout | InArgument | `double` | The amount of time (in seconds) to wait for the operation to be performed before generating an error. The default value is 30 seconds. |
| `DelayAfter` | Delay after | InArgument | `double` | Delay (in seconds) after this activity is completed, before next activity starts. The default amount of time is 0.3 seconds. |
| `DelayBefore` | Delay before | InArgument | `double` | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## How to create a new Extract Form Data

To generate the default XAML for this activity, run the following command:

```bash
uip rpa get-default-activity-xaml --activity-class-name UiPath.Semantic.Activities.NExtractFormDataGeneric --use-studio
```
## Notes

- This activity must be placed inside a **Use Application/Browser** (`NApplicationCard`) scope.
- The generic type parameter `T` defines the shape of the extracted form data. Use a custom type or `DataTable` to match the form structure.
- This activity leverages AI to identify and extract values from form fields on the current screen.
- The `FormData` output contains the extracted form data mapped to the specified type.
