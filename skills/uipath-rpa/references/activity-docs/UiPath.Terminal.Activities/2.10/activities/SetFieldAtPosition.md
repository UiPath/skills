# Set Field at Position

`UiPath.Terminal.Advanced.Activities.TerminalSetFieldAtPosition`

Writes text into the input field that starts at the specified row and column position on the terminal screen.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals.Advanced  
**Required Scope:** `TerminalSession` — place inside a `TerminalSession.Body` `Sequence`. See [child-activity skeleton](TerminalSession.md#child-activity-skeleton) for a multi-activity example.

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Text` | Text | `InArgument` | `string` | Yes | | The text to write into the field. |

### Position

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Row` | Row | `InArgument` | `int` | Yes | | The row of the field start (1-based). |
| `Column` | Column | `InArgument` | `int` | Yes | | The column of the field start (1-based). |

### Configuration

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `BackwardsCompatible` | Backwards Compatible | `Property` | `bool?` | `true` (existing workflows); `false` (newly added) | Controls cursor movement behavior after writing. When `true`, the cursor jumps back to the field start position after writing (legacy behavior). When `false`, the cursor stays at the end of the written text. |

### Options

Standard `TimeoutMS` / `DelayMS` / `WaitType` (defaults `5000` / `300` / `READY`) — see [_common-options.md](TerminalSession/_common-options.md). Defaults work for typical sessions; tune only when scripted activities run faster than the host responds.

## Notes

- `BackwardsCompatible` defaults to `true` for activities that were created with an older version of the package (detected via stack trace at design time). New activities added to a workflow default to `false`.
- Set `BackwardsCompatible = false` for new workflows to get consistent cursor behavior after writing.

## XAML Example

```xml
<uit:TerminalSetFieldAtPosition DisplayName="Set Field at Position"
                                Row="[7]"
                                Column="[15]"
                                Text="[inputValue]"
                                BackwardsCompatible="False"
                                WaitType="READY"
                                DelayMS="300" />
```
