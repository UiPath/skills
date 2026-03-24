# Select Dates In Calendar

`UiPath.UIAutomationNext.Activities.NSAPSelectDatesInCalendar`

Select Dates in Calendar. The activity can be used to select single dates or periods of time.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.SAP
**Required Scope:** `UiPath.UIAutomationNext.Activities.NApplicationCard`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  | The UI element to perform the action on. |
| `SelectType` | Select Type | InArgument | `NDateSelectionType` |  |  |  | Select single dates or periods of time. |
| `Date` | Date | InArgument | `DateTime` |  |  |  | Select a specific day. |
| `StartDate` | Start Date | InArgument | `DateTime` |  |  |  | Enter the date. |
| `EndDate` | End Date | InArgument | `DateTime` |  |  |  | Enter the date. |
| `Year` | Year | InArgument | `int` |  |  |  | Select the year. |
| `Week` | Week | InArgument | `int` |  |  |  | Select the week. |
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `HealingAgentBehavior` | Healing Agent mode | `NChildHealingAgentBehavior` |  | Configures the Healing Agent actions if they are allowed by Governance or Orchestrator process/job/trigger level settings |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `OutUiElement` | Output element | `UiElement` | Output a UI Element to use in other activities as an Input UI Element. |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` |  | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `Timeout` | Timeout | InArgument | `double` |  | The amount of time (in seconds) to wait for the operation to be performed before generating an error. The default value is 30 seconds. |
| `DelayAfter` | Delay after | InArgument | `double` |  | Delay (in seconds) after this activity is completed, before next activity starts. The default amount of time is 0.3 seconds. |
| `DelayBefore` | Delay before | InArgument | `double` |  | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## XAML Example

```xml
<ua:NApplicationCard
    xmlns:ua="clr-namespace:UiPath.UIAutomationNext.Activities;assembly=UiPath.UIAutomationNext.Activities"
    DisplayName="Use Application/Browser"
    Version="V2">
  <ua:NSAPSelectDatesInCalendar
      DisplayName="Select Dates In Calendar"
      SelectType="SingleDate"
      Date="[selectedDate]"
      Version="V5">
    <ua:NSAPSelectDatesInCalendar.Target>
      <ua:TargetAnchorable
          FullSelectorArgument="[&quot;&lt;sapctrl type='GuiCalendar' /&gt;&quot;]"
          SearchSteps="Selector"
          Version="V6" />
    </ua:NSAPSelectDatesInCalendar.Target>
  </ua:NSAPSelectDatesInCalendar>
</ua:NApplicationCard>
```

## Notes

- This activity must be placed inside a `UiPath.UIAutomationNext.Activities.NApplicationCard` scope.
- The `Version` attribute is mandatory and must be set to `V5`.
- Assembly: `UiPath.UIAutomationNext.Activities`
