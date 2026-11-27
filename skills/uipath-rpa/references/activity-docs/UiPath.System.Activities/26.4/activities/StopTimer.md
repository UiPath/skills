# Stop Timer

`UiPath.Core.Activities.StopTimer`

Stops the timer previously started using the Start Timer activity.

**Package:** `UiPath.System.Activities`
**Category:** System.Timer

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| Timer | Timer | InArgument | `UiPathTimer` | Yes | — | The timer object to stop. Must be a variable previously populated by a Start Timer activity. |

### Configuration

_No configuration properties._

### Output

_No output properties._

## XAML Example

```xml
<ui:StopTimer>
  <ui:StopTimer.Timer>
    <InArgument x:TypeArguments="ui:UiPathTimer">[myTimer]</InArgument>
  </ui:StopTimer.Timer>
</ui:StopTimer>
```

## Notes

- After stopping, the timer retains its elapsed value. Use Reset Timer to clear it back to zero.
- Stopping a timer that is already stopped has no effect.
- To resume a stopped timer from where it left off, use Resume Timer.
