# For Each UI Element

`UiPath.UIAutomationNext.Activities.NForEachUiElement`

Iterates over a structured set of UiElements.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Application

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Target` | Target | Property | [`TargetAnchorable`](common/Target.md#targetanchorable) |  |  |  | The UI element to perform the action on. |
| `NextLink` | Target (Next button) | Property | `TargetAnchorable` |  |  |  | The target that identifies the link/button used to navigate to the next page of the table. |

### Configuration

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `LimitExtractionTo` | Limit extraction to | Property | `LimitType` |  |  | The type of limit to apply when extracting data. |
| `MaximumResults` | Number of items | InArgument | `int` |  |  | The maximum number of results to be extracted. If the value is 0, all the identified elements are extracted. |
| `InteractionMode` | Input mode | InArgument | `NChildInteractionMode` |  |  | The method used to execute the click on the next page link if the data spans multiple pages. |
| `DelayBetweenPages` | Delay between pages | InArgument | `double` |  |  | The amount of time (in seconds) to wait until the next page is loaded if the data spans multiple pages. |

### Common

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` |  |  | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `Timeout` | Timeout | InArgument | `double` |  |  | The amount of time (in seconds) to wait for the operation to be performed before generating an error. The default value is 30 seconds. |
| `DelayAfter` | Delay after | InArgument | `double` |  |  | Delay (in seconds) after this activity is completed, before next activity starts. The default amount of time is 0.3 seconds. |
| `DelayBefore` | Delay before | InArgument | `double` |  |  | Delay (in seconds) to wait before executing this activity. The default amount of time is 0.2 seconds. |

## XAML Example

```xml
<uix:NApplicationCard
    xmlns:uix="http://schemas.uipath.com/workflow/activities/uix"
    DisplayName="Use Application/Browser"
    Version="V2">
  <uix:NForEachUiElement
      DisplayName="For Each UI Element"
      Version="V5">
    <uix:NForEachUiElement.Target>
      <uix:TargetAnchorable
          FullSelectorArgument="[&quot;&lt;webctrl tag='TR' /&gt;&quot;]"
          SearchSteps="Selector"
          Version="V6" />
    </uix:NForEachUiElement.Target>
    <uix:NForEachUiElement.NextLink>
      <uix:TargetAnchorable
          FullSelectorArgument="[&quot;&lt;webctrl tag='A' class='next-page' /&gt;&quot;]"
          SearchSteps="Selector"
          Version="V6" />
    </uix:NForEachUiElement.NextLink>
    <!-- Activities to execute for each UI element -->
  </uix:NForEachUiElement>
</uix:NApplicationCard>
```

## Notes

- This activity iterates over a structured set of UI elements found by the target selector.
- Use the `NextLink` target to specify a pagination button for navigating multi-page data.
- The `Limit extraction to` and `Number of items` options control how many elements are extracted.
- The `Delay between pages` controls wait time when navigating between pages.
