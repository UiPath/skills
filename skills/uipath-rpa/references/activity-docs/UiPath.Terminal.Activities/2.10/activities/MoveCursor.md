# Move Cursor

`UiPath.Terminal.Advanced.Activities.TerminalMoveCursor`

Moves the terminal cursor to an exact row and column position on the screen.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals.Advanced  
**Required Scope:** `TerminalSession` — place inside a `TerminalSession.Body` `Sequence`. See [child-activity skeleton](TerminalSession.md#child-activity-skeleton) for a multi-activity example.

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Row` | Row | `InArgument` | `int` | Yes | | The target row (1-based). |
| `Column` | Column | `InArgument` | `int` | Yes | | The target column (1-based). |

### Options

Standard `TimeoutMS` / `DelayMS` / `WaitType` (defaults `5000` / `300` / `READY`) — see [_common-options.md](TerminalSession/_common-options.md). Defaults work for typical sessions; tune only when scripted activities run faster than the host responds.

## XAML Example

```xml
<uit:TerminalMoveCursor DisplayName="Move Cursor"
                        Row="[5]"
                        Column="[20]"
                        WaitType="READY"
                        DelayMS="300" />
```
