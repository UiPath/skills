# Wait Screen Text

`UiPath.Terminal.Activities.TerminalWaitScreenText`

Waits until a specified text string appears anywhere on the terminal screen. Useful for synchronizing with host-side processing that updates the screen.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals  
**Required Scope:** `TerminalSession` — place inside a `TerminalSession.Body` `Sequence`. See [child-activity skeleton](TerminalSession.md#child-activity-skeleton) for a multi-activity example.

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Text` | Text | `InArgument` | `string` | Yes | | The text string to wait for on the screen. |
| `MatchCase` | MatchCase | `InArgument` | `bool` | | `false` | When `true`, the text comparison is case-sensitive. |

### Options

Standard `TimeoutMS` / `DelayMS` / `WaitType` (defaults **`30000`** / `300` / `READY`) — see [_common-options.md](TerminalSession/_common-options.md). The higher `TimeoutMS` default is appropriate for host responses that take seconds; raise further for slow scripted flows.

## XAML Example

```xml
<uit:TerminalWaitScreenText DisplayName="Wait Screen Text"
                           Text="[&quot;READY&quot;]"
                           TimeoutMS="[30000]"
                           WaitType="READY"
                           DelayMS="300" />
```
