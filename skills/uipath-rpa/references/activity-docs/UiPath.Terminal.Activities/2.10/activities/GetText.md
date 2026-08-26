# Get Text

`UiPath.Terminal.Activities.TerminalGetText`

Reads the entire visible text content of the terminal screen and returns it as a string.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals  
**Required Scope:** `TerminalSession` — place inside a `TerminalSession.Body` `Sequence`. See [child-activity skeleton](TerminalSession.md#child-activity-skeleton) for a multi-activity example.

## Properties

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Text` | Text | `OutArgument` | `string` | The full text content of the terminal screen. |

### Options

Standard `TimeoutMS` / `DelayMS` / `WaitType` (defaults `5000` / `300` / `READY`) — see [_common-options.md](TerminalSession/_common-options.md). Defaults work for typical sessions; tune only when scripted activities run faster than the host responds.

## XAML Example

```xml
<uit:TerminalGetText DisplayName="Get Text"
                   Text="[screenText]"
                   WaitType="READY"
                   DelayMS="300" />
```
