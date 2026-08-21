# Start Timer

`UiPath.Core.Activities.StartTimer`

Creates a new timer or restarts an existing one received as parameter.

**Package:** `UiPath.System.Activities`
**Category:** System.Timer

## Properties

### Input

_No input arguments._

### Configuration

_No configuration properties._

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| Timer | Timer | OutArgument | `UiPathTimer` | The newly created (or restarted) timer object. Pass this variable to Stop Timer, Resume Timer, or Reset Timer. |

## XAML Example

```xml
<ui:StartTimer>
  <ui:StartTimer.Timer>
    <OutArgument x:TypeArguments="ui:UiPathTimer">[myTimer]</OutArgument>
  </ui:StartTimer.Timer>
</ui:StartTimer>
```

## Notes

- The returned `UiPathTimer` variable must be stored and passed to subsequent timer activities (Stop Timer, Resume Timer, Reset Timer).
- Calling Start Timer on an existing timer variable restarts it from zero.
- Timer precision is subject to .NET threading resolution (typically ~15 ms on Windows).
