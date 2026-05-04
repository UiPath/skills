# Continue

`UiPath.Core.Activities.Continue`

Skips the current iteration in a Loop activity (For Each, While, Do While) and continues the execution with the next iteration.

**Package:** `UiPath.System.Activities`
**Category:** Workflow.Control

## Properties

No configurable properties.

## XAML Example

```xml
<ui:Continue DisplayName="Continue"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

Must be placed directly or indirectly inside a loop activity (`For Each`, `While`, `Do While`). A validation error is raised at design time if no enclosing loop is found in the parent chain.

Execution resumes at the top of the next iteration. Any activities after `Continue` within the same iteration body are skipped.
