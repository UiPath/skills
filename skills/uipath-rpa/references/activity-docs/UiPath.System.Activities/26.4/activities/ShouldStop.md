# Should Stop

`UiPath.Core.Activities.ShouldStop`

Checks if a Stop command was triggered in UiPath Orchestrator for the current job. Use this activity inside loops or long-running processes to implement a graceful stop: poll periodically and exit the workflow cleanly when the result is `True`.

**Package:** `UiPath.System.Activities`
**Category:** Process

## Properties

No configurable input properties.

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `bool` | `True` if a Stop command has been issued for the current job in Orchestrator; `False` otherwise. |

## XAML Example

```xml
<ui:ShouldStop DisplayName="Should Stop" Result="[shouldStop]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

Typical usage inside a loop:

```xml
<ui:ShouldStop DisplayName="Should Stop" Result="[shouldStop]" />
<If Condition="[shouldStop]">
  <If.Then>
    <!-- clean up and exit -->
    <ui:Return DisplayName="Return" />
  </If.Then>
</If>
```

## Notes

- Returns `False` when the robot is not connected to Orchestrator (standalone execution).
- Poll this activity at natural checkpoints in long-running loops rather than on every iteration, to avoid excess Orchestrator API calls.
- Pair with `Return` or a loop exit condition to implement a graceful stop without throwing an exception.
- A *Kill* stop (as opposed to *Soft Stop*) does not wait for `ShouldStop` to be checked — it terminates the process immediately.
