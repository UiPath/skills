# Repeat Number of Times

`UiPath.Core.Activities.RepeatNumberOfTimesX`

Repeats a set of activities a specified number of times. Add the activities to repeat inside this activity.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `NumberOfTimes` | Number Of Times | `InArgument` | `int` | Yes | — | The total number of times to repeat the body activities. |
| `StartAt` | Start at | `InArgument` | `int` | No | `1` | The starting value of the iteration counter variable. |

## XAML Example

```xml
<ui:RepeatNumberOfTimesX
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Repeat Number of Times">
  <ui:RepeatNumberOfTimesX.NumberOfTimes>
    <InArgument x:TypeArguments="x:Int32">
      <VisualBasicValue x:TypeArguments="x:Int32" ExpressionText="5" />
    </InArgument>
  </ui:RepeatNumberOfTimesX.NumberOfTimes>
  <ui:RepeatNumberOfTimesX.StartAt>
    <InArgument x:TypeArguments="x:Int32">
      <VisualBasicValue x:TypeArguments="x:Int32" ExpressionText="1" />
    </InArgument>
  </ui:RepeatNumberOfTimesX.StartAt>
  <ActivityAction x:TypeArguments="x:Int32">
    <ActivityAction.Argument>
      <DelegateInArgument x:TypeArguments="x:Int32" Name="currentIndex" />
    </ActivityAction.Argument>
    <Sequence DisplayName="Body">
      <!-- child activities go here -->
    </Sequence>
  </ActivityAction>
</ui:RepeatNumberOfTimesX>
```

## Notes

- **Repeat Number of Times** is a container/scope activity. Child activities are placed inside the `ActivityAction` body.
- The body receives the current iteration counter as a delegate argument (e.g. `currentIndex`). The counter starts at `StartAt` (default `1`) and increments by one on each iteration.
- The activity iterates exactly `NumberOfTimes` times regardless of any conditions inside the body.
- The iterator variable name is auto-suggested from the activity and can be renamed in the designer (configured via `Item` in the view model, display name `Current Index`).
- Use a `Break` activity inside the body to exit the loop early; use `Continue` to skip to the next iteration.
