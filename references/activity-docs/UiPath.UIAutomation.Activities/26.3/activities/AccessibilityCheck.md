# Accessibility Check

`UiPath.UIAutomationNext.Activities.NAccessibilityCheck`

Check for the accessibility issues

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Application
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Configuration

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `WaitForReady` | Wait for page load | InArgument | `NWaitForReady` |  |  | Before performing the action, wait for the application to become ready to accept input. The options are: None -- does not wait for the target to be ready; Interactive -- waits until only a part of the app is loaded; Complete -- waits for the entire app to be loaded. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `AccessibilityResults` | Accessibility Results | `AccessibilityCheckResult` | Typed result containing accessibility violations, passes, incomplete checks, and inapplicable checks. Use RawJson property for the raw axe-core JSON output. |

### Common

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` |  |  | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `Timeout` | Timeout | InArgument | `double` |  |  | The amount of time (in seconds) to wait for the operation to be performed before generating an error. The default value is 30 seconds. |
| `DelayAfter` | Delay after | InArgument | `double` |  |  | Delay (in seconds) after this activity is completed, before next activity starts. The default amount of time is 0.3 seconds. |
| `DelayBefore` | Delay before | InArgument | `double` |  |  | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## How to create a new Accessibility Check

To generate the default XAML for this activity, run the following command:

```bash
uip rpa get-default-activity-xaml --activity-class-name UiPath.UIAutomationNext.Activities.NAccessibilityCheck --use-studio
```
## Notes

- This activity must be placed inside a **Use Application/Browser** (`NApplicationCard`) scope.
- Uses the axe-core library to check for accessibility issues on the current web page.
- The output `AccessibilityCheckResult` contains detailed information about violations, passes, incomplete checks, and inapplicable checks.
- Access the raw axe-core JSON output via the `RawJson` property of the result.
