# Extract UI Data

`UiPath.Semantic.Activities.NExtractUIData`1`

Leverages AI to facilitate the extraction of form data.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Semantic
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  | The UI element to perform the action on. |
| `Queries` | Queries | Property | `Dictionary<string, InArgument<string>>` |  | `new()` |  | Use AI to extract specific information from the current screen. For each piece of data you want, provide a descriptive query and assign it to a field name for easy access in your workflow. |
| `AgentType` | Model | InArgument | `NUITaskAgentType` |  |  |  | Indicates the underlying LLM used by Extract UI Data to perform form extraction. |
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |

### Configuration

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `IsDOMEnabled` | Use DOM when available | InArgument | `bool` |  |  | Indicates whether DOM data will be used/sent to the LLM for applications where DOM can be extracted. |
| `HealingAgentBehavior` | Healing Agent mode | InArgument | `NChildHealingAgentBehavior` |  |  | Configures the Healing Agent actions if they are allowed by Governance or Orchestrator process/job/trigger level settings |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `UIData` | Result | `T` | Output argument intended for single-value queries. If the query returns multiple values, only the first value will be stored in this result. |
| `UIDataTable` | Result (Data table) | `DataTable` | Output argument intended for queries that return multiple values. Use this when you expect more than one result for the same query, as all extracted values will be stored in the table. If the number of returned values differ between queries, the extra rows under the corresponding query columns will not hold any value. |
| `OutUiElement` | Output element | `UiElement` | Output a UI Element to use in other activities as an Input UI Element. |

### Common

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` |  |  | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `Timeout` | Timeout | InArgument | `double` |  |  | The amount of time (in seconds) to wait for the operation to be performed before generating an error. The default value is 30 seconds. |
| `DelayAfter` | Delay after | InArgument | `double` |  |  | Delay (in seconds) after this activity is completed, before next activity starts. The default amount of time is 0.3 seconds. |
| `DelayBefore` | Delay before | InArgument | `double` |  |  | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## How to create a new Extract UI Data

To generate the default XAML for this activity, run the following command:

```bash
uip rpa get-default-activity-xaml --activity-class-name UiPath.Semantic.Activities.NExtractUIData --use-studio
```
## Notes

- This activity requires a parent `Use Application/Browser` scope.
- The `Queries` property allows you to define multiple AI-powered extraction queries, each mapped to a field name.
- Use the `Result` output for single-value queries, or the `Result (Data table)` output when expecting multiple values per query.
- The `Model` property determines which LLM is used for the extraction.
