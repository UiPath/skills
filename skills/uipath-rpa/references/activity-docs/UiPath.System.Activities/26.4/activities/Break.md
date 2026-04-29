# Break

`UiPath.Core.Activities.Break`

Exits the Loop activity (For Each, While, Do While) or Trigger Scope activity in which it is placed and continues the workflow execution with the activity that follows it.

**Package:** `UiPath.System.Activities`
**Category:** Workflow.Control

## Properties

No configurable properties.

## XAML Example

```xml
<ui:Break DisplayName="Break"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

Must be placed directly or indirectly inside a loop activity (`For Each`, `While`, `Do While`) or a Trigger Scope activity. A validation error is raised at design time if neither a loop nor an interruptible trigger scope is found in the parent chain.

When placed inside a Trigger Scope, `Break` signals the trigger's internal bookmark to stop the trigger loop and resume execution after the scope.
