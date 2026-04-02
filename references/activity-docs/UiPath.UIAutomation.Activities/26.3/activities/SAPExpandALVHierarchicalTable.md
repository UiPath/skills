# Expand ALV Hierarchical Table

`UiPath.UIAutomationNext.Activities.NSAPExpandALVHierarchicalTable`

Use the activity to identify any cell inside SAP ALV Hierarchical Table. After the identification of the cell all typical UI activities can be performed, such as Click, Double Click, Get Text and others.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.SAP
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  | The UI element to perform the action on. |
| `FocusedColumn` | Level / Focused column | InArgument | `string` |  |  |  | Defines which element is set as the focused. |
| `ColumnNameLevel0` | Level 0 / Header column | InArgument | `string` |  |  |  | Defines which column to find in the header column. |
| `ColumnNameLevel1` | Level 1 / Position column | InArgument | `string` |  |  |  | Defines which column to find in the position column. |
| `ColumnValueLevel0` | Level 0 / Value | InArgument | `string` |  |  |  | Defines which value to find in the header column. |
| `ColumnValueLevel1` | Level 1 / Value | InArgument | `string` |  |  |  | Defines which value to find in the position column. |
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |

### Configuration

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `HealingAgentBehavior` | Healing Agent mode | InArgument | `NChildHealingAgentBehavior` |  |  | Configures the Healing Agent actions if they are allowed by Governance or Orchestrator process/job/trigger level settings |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `OutUiElement` | Output element | `UiElement` | Output a UI Element to use in other activities as an Input UI Element. |

### Common

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` |  |  | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `Timeout` | Timeout | InArgument | `double` |  |  | The amount of time (in seconds) to wait for the operation to be performed before generating an error. The default value is 30 seconds. |
| `DelayAfter` | Delay after | InArgument | `double` |  |  | Delay (in seconds) after this activity is completed, before next activity starts. The default amount of time is 0.3 seconds. |
| `DelayBefore` | Delay before | InArgument | `double` |  |  | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## How to create a new Expand ALV Hierarchical Table

To generate the default XAML for this activity, run the following command:

```bash
uip rpa get-default-activity-xaml --activity-class-name UiPath.UIAutomationNext.Activities.NSAPExpandALVHierarchicalTable --use-studio
```
## Notes

- This activity requires a parent `Use Application/Browser` scope.
- Use this activity to identify and navigate to specific cells in SAP ALV Hierarchical Tables.
- The table has two levels: Level 0 (header) and Level 1 (position), each with column name and value properties.
- The `Focused column` property defines which column element receives focus after expansion.
- After identifying a cell, standard UI activities (Click, Get Text, etc.) can be used on it.
