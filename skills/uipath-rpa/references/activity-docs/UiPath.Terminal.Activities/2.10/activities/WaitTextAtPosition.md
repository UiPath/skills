# Wait Text at Position

`UiPath.Terminal.Advanced.Activities.TerminalWaitTextAtPosition`

Waits until a specific row and column position on the terminal screen contains the expected text.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals.Advanced  
**Required Scope:** `TerminalSession` — place inside a `TerminalSession.Body` `Sequence`. See [child-activity skeleton](TerminalSession.md#child-activity-skeleton) for a multi-activity example.

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Text` | Text | `InArgument` | `string` | Yes | | The text string to wait for at the specified position. |
| `MatchCase` | MatchCase | `InArgument` | `bool` | | `false` | When `true`, the text comparison is case-sensitive. |

### Position

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Row` | Row | `InArgument` | `int` | Yes | | The row to check (1-based). |
| `Column` | Column | `InArgument` | `int` | Yes | | The column to check (1-based). |

### Options

Standard `TimeoutMS` / `DelayMS` / `WaitType` (defaults **`30000`** / `300` / `READY`) — see [_common-options.md](TerminalSession/_common-options.md). The higher `TimeoutMS` default is appropriate for host responses that take seconds; raise further for slow scripted flows.

## XAML Example

```xml
<uit:TerminalWaitTextAtPosition DisplayName="Wait Text at Position"
                                Row="[24]"
                                Column="[1]"
                                Text="[&quot;READY&quot;]"
                                TimeoutMS="[30000]"
                                WaitType="READY"
                                DelayMS="300" />
```
