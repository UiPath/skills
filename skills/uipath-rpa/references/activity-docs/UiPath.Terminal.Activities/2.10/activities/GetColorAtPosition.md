# Get Color at Position

`UiPath.Terminal.Advanced.Activities.TerminalGetColorAtPosition`

Returns the foreground color of the character at the specified row and column on the terminal screen. Useful for detecting highlighted fields, error indicators, or status colors.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals.Advanced  
**Required Scope:** `TerminalSession` — place inside a `TerminalSession.Body` `Sequence`. See [child-activity skeleton](TerminalSession.md#child-activity-skeleton) for a multi-activity example.

## Properties

### Position

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Row` | Row | `InArgument` | `int` | Yes | | The row of the character (1-based). |
| `Column` | Column | `InArgument` | `int` | Yes | | The column of the character (1-based). |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `TerminalColor` | Color | `OutArgument` | `System.Drawing.Color` | The foreground color of the character at the specified position. |

### Options

Standard `TimeoutMS` / `DelayMS` / `WaitType` (defaults `5000` / `300` / `READY`) — see [_common-options.md](TerminalSession/_common-options.md). Defaults work for typical sessions; tune only when scripted activities run faster than the host responds.

## Notes

Color availability depends on the terminal provider and emulation type. Not all providers support color information (see BlueZone's `colorsAvailable` flag).

## XAML Example

```xml
<uit:TerminalGetColorAtPosition DisplayName="Get Color at Position"
                                Row="[3]"
                                Column="[5]"
                                TerminalColor="[charColor]"
                                WaitType="READY"
                                DelayMS="300" />
```
