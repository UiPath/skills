# Resume Timer

`UiPath.Core.Activities.ResumeTimer`

Resumes the input timer provided as argument.

**Package:** `UiPath.System.Activities`
**Category:** System.Timer

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| Timer | Timer | InArgument | `UiPathTimer` | Yes | — | The timer object to resume. Must be a variable previously populated by a Start Timer activity and stopped via Stop Timer. |

### Configuration

_No configuration properties._

### Output

_No output properties._

## XAML Example

```xml
<ui:ResumeTimer>
  <ui:ResumeTimer.Timer>
    <InArgument x:TypeArguments="ui:UiPathTimer">[myTimer]</InArgument>
  </ui:ResumeTimer.Timer>
</ui:ResumeTimer>
```

## Notes

- Resumes counting from the elapsed value at the point the timer was stopped.
- Resuming a timer that is already running has no effect.
- To restart the timer from zero instead, use Reset Timer followed by Start Timer.
