# Extract Table Data

`UiPath.UIAutomationNext.Activities.NExtractDataGeneric`

Extracts tabular data from a specified web page or application.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Application
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  |  |
| `ExtractMetadata` | Extract metadata | InArgument | `string` |  |  |  | An XML string that defines what data to extract from the target application. |
| `ExtractDataSettings` | Table settings | InArgument | `string` |  |  |  | Table settings used when extracting data. |
| `NextLink` | Target (Next button) | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  | The target that identifies the link/button used to navigate to the next page of the table. |

### Configuration

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `InputDataTable` | Input DataTable | InArgument | `DataTable` | Data to append to the extracted data. |
| `LimitExtractionTo` | Limit extraction to | Property | `LimitType` | The type of limit to apply when extracting data. |
| `MaximumResults` | Number of items | InArgument | `int` | The maximum number of results to be extracted. If the value is 0, all the identified elements are extracted. |
| `InteractionMode` | Input mode | InArgument | `NChildInteractionMode` | The method used to execute the click on the next page link if the data spans multiple pages. |
| `DelayBetweenPages` | Delay between pages | InArgument | `double` | The amount of time (in seconds) to wait until the next page is loaded if the data spans multiple pages. |
| `HealingAgentBehavior` | Healing Agent mode | InArgument | `NChildHealingAgentBehavior` | Configures the Healing Agent actions if they are allowed by Governance or Orchestrator process/job/trigger level settings. |

### Input/Output

These properties are bidirectional: the activity reads the incoming value **and** writes an updated value back. In XAML, they must be bound to a **variable** — a literal expression is not valid here.

| Name | Display Name | Type | Required | Description |
|------|-------------|------|----------|-------------|
| `DataTable` | Destination data table | `DataTable` |  | Where to save the extracted data. If provided, extracted rows are appended to this table. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `ExtractedData` | DataTable | `T` | Where to save the extracted data. |

### Common

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `Timeout` | Timeout | InArgument | `double` | The amount of time (in seconds) to wait for the operation to be performed before generating an error. The default value is 30 seconds. |
| `DelayAfter` | Delay after | InArgument | `double` | Delay (in seconds) after this activity is completed, before next activity starts. The default amount of time is 0.3 seconds. |
| `DelayBefore` | Delay before | InArgument | `double` | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## How to create a new Extract Table Data

To generate the default XAML for this activity, run the following command:

```bash
uip rpa get-default-activity-xaml --activity-class-name UiPath.UIAutomationNext.Activities.NExtractDataGeneric --use-studio
```
## Notes

- This activity must be placed inside a **Use Application/Browser** (`NApplicationCard`) scope.
- The `ExtractMetadata` property is required and contains an XML string that defines the data extraction configuration (columns, selectors, etc.).
- For multi-page extraction, configure the `NextLink` target to point to the pagination button and adjust `DelayBetweenPages` as needed.
- Use `LimitExtractionTo` and `MaximumResults` to control the volume of extracted data.
