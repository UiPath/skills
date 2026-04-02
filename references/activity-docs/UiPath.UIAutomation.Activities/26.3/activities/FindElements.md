# Find Elements

`UiPath.UIAutomationNext.Activities.NFindElements`

Gets the child elements of the specified UI element.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Application
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
| `Mode` | Mode | InArgument | `NFindMode` | Enables you to set the find mode of the UI elements in the collection. The following options are available: elements, descendants, top level. |
| `Timeout` | Timeout (seconds) | InArgument | `double` | Default value: 5 seconds. The amount of time to wait for the element to appear or disappear, before executing one of the two activity blocks. |
| `HealingAgentBehavior` | Healing Agent mode | InArgument | `NChildHealingAgentBehavior` | Configures the Healing Agent actions if they are allowed by Governance or Orchestrator process/job/trigger level settings. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Children` | Children | `IEnumerable<UiElement>` | All UI children found according to the filter and scope set. The field supports only IEnumerable<UiElement> variables. |
| `OutUiElement` | Output element | `UiElement` | Output a UI Element to use in other activities as an Input UI Element. |

### Common

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `DelayBefore` | Delay before | InArgument | `double` | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## How to create a new Find Elements

To generate the default XAML for this activity, run the following command:

```bash
uip rpa get-default-activity-xaml --activity-class-name UiPath.UIAutomationNext.Activities.NFindElements --use-studio
```
## Notes

- This activity must be placed inside a **Use Application/Browser** (`NApplicationCard`) scope.
- The `Mode` property controls how child elements are discovered: direct children, all descendants, or top-level elements only.
- The `Children` output returns an `IEnumerable<UiElement>` collection that can be iterated with a **For Each** activity.
- The default timeout is 5 seconds (different from the standard 30-second default in other activities).
