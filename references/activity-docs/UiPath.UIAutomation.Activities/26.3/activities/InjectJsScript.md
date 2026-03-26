# Inject Js Script

`UiPath.UIAutomationNext.Activities.NInjectJsScript`

Executes JavaScript code in the context of the web page corresponding to a UiElement.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Browser
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  | The UI element to perform the action on. |
| `InputParameter` | Input parameter | InArgument | `string` |  |  |  | Input data for the JavaScript code. |
| `ScriptCode` | Script code | InArgument | `string` |  |  |  | The JavaScript code you want to run. You can write it here as a string, or add the full path of a .js file. |
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |

### Configuration

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `ExecutionWorld` | Execution world | InArgument | `NExecutionWorld` |  |  | The JavaScript environment for the script execution. Isolated option allows access to the HTML elements, but prevents access to page variables and code. Use this option to ensure that the script execution does not conflict with the page. Page option allows access to the HTML elements, page variables and code. Use this option if you need to access page variables (e.g. jQuery $) or to interact with page code (e.g. window.alert). |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `ScriptOutput` | Script output | `OutArgument` | String result returned from JavaScript code. |
| `OutUiElement` | Output element | `UiElement` | Output a UI Element to use in other activities as an Input UI Element. |

### Common

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` |  |  | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `Timeout` | Timeout | InArgument | `double` |  |  | The amount of time (in seconds) to wait for the operation to be performed before generating an error. The default value is 30 seconds. |
| `DelayAfter` | Delay after | InArgument | `double` |  |  | Delay (in seconds) after this activity is completed, before next activity starts. The default amount of time is 0.3 seconds. |
| `DelayBefore` | Delay before | InArgument | `double` |  |  | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## How to create a new Inject Js Script

To generate the default XAML for this activity, run the following command:

```bash
uip rpa get-default-activity-xaml --activity-class-name UiPath.UIAutomationNext.Activities.NInjectJsScript
```
## Notes

- This activity must be placed inside a **Use Application/Browser** (`NApplicationCard`) scope.
- The `ExecutionWorld` property controls the JavaScript execution environment: **Isolated** prevents conflicts with page code, while **Page** allows access to page variables and functions.
- Use `InputParameter` to pass data into the JavaScript code, accessible via the first function argument.
- The script must return a value using `return` to populate the `ScriptOutput`.
