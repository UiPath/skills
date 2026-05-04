# Reset Timer

`UiPath.Core.Activities.ResetTimer`

Resets the input timer provided as argument.

**Package:** `UiPath.System.Activities`
**Category:** System.Timer

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| Timer | Timer | InArgument | `UiPathTimer` | Yes | — | The timer object to reset. Must be a variable previously populated by a Start Timer activity. |

### Configuration

_No configuration properties._

### Output

_No output properties._

## XAML Example

```xml
<ui:ResetTimer>
  <ui:ResetTimer.Timer>
    <InArgument x:TypeArguments="ui:UiPathTimer">[myTimer]</InArgument>
  </ui:ResetTimer.Timer>
</ui:ResetTimer>
```

## Notes

- Resets the elapsed time on the timer back to zero.
- The timer's running/stopped state is preserved; a running timer continues running from zero after reset.
- To stop the timer before resetting, use Stop Timer first.
