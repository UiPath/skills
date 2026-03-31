# Table Cell Scope

`UiPath.UIAutomationNext.Activities.NSAPTableCellScope`

A container that enables you to attach to an existing Table UI element and perform multiple actions within it.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.SAP
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  | The UI element to perform the action on. |
| `ColumnName` | Column Name / Filter | InArgument | `string` |  |  |  | Specifies Column name from the table. After indicating the table cell, the list with all available Column names is displayed in the activity. |
| `RowIndex` | Row index | InArgument | `uint` |  |  |  | Specifies the row index |
| `RowSelector` | Row selector | InArgument | `string` |  |  |  | Specifies the row selector/filter to use |
| `RowType` | Row input type | InArgument | `NSAPTableCellScopeRowType` |  |  |  | Specifies how the row should be searched: by index, by selector/filter or first empty row |
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `HealingAgentBehavior` | Healing Agent mode | `NChildHealingAgentBehavior` |  | Configures the Healing Agent actions if they are allowed by Governance or Orchestrator process/job/trigger level settings |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `TableRow` | Table Row Index | `uint` | The found row index in case "First Empty Row" is used. This is equal to the Row Number input otherwise. This field only supports uint variables. |
| `OutUiElement` | Output element | `UiElement` | Output a UI Element to use in other activities as an Input UI Element. |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` |  | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `Timeout` | Timeout | InArgument | `double` |  | The amount of time (in seconds) to wait for the operation to be performed before generating an error. The default value is 30 seconds. |
| `DelayAfter` | Delay after | InArgument | `double` |  | Delay (in seconds) after this activity is completed, before next activity starts. The default amount of time is 0.3 seconds. |
| `DelayBefore` | Delay before | InArgument | `double` |  | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## How to create a new Table Cell Scope

To generate the default XAML for this activity, run the following command:

```bash
uip rpa get-default-activity-xaml --activity-class-name UiPath.UIAutomationNext.Activities.NSAPTableCellScope --use-studio
```
## Notes

- This activity must be placed inside a `UiPath.UIAutomationNext.Activities.NApplicationCard` scope.
- This activity is a scope/container. Place child activities inside the body to perform actions on the specified table cell.
- The `Version` attribute is mandatory and must be set to `V5`.
- Assembly: `UiPath.UIAutomationNext.Activities`
