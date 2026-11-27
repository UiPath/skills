# Get Cursor Position

`UiPath.Terminal.Activities.TerminalGetCursorPosition`

Returns the current row and column position of the terminal cursor.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals  
**Required Scope:** `TerminalSession` — place inside a `TerminalSession.Body` `Sequence`. See [child-activity skeleton](TerminalSession.md#child-activity-skeleton) for a multi-activity example.

## Properties

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Row` | Row | `OutArgument` | `int` | The current row of the cursor (1-based). |
| `Column` | Column | `OutArgument` | `int` | The current column of the cursor (1-based). |

### Options

Standard `TimeoutMS` / `DelayMS` / `WaitType` (defaults `5000` / `300` / `READY`) — see [_common-options.md](TerminalSession/_common-options.md). Defaults work for typical sessions; tune only when scripted activities run faster than the host responds.

## XAML Example

```xml
<uit:TerminalGetCursorPosition DisplayName="Get Cursor Position"
                              Row="[cursorRow]"
                              Column="[cursorCol]"
                              WaitType="READY"
                              DelayMS="300" />
```
