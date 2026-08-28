# Get Text at Position

`UiPath.Terminal.Advanced.Activities.TerminalGetTextAtPosition`

Reads text starting at a specific row and column position on the terminal screen. An optional `Length` parameter limits how many characters are read.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals.Advanced  
**Required Scope:** `TerminalSession` — place inside a `TerminalSession.Body` `Sequence`. See [child-activity skeleton](TerminalSession.md#child-activity-skeleton) for a multi-activity example.

## Properties

### Position

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Row` | Row | `InArgument` | `int` | Yes | | The row to start reading from (1-based). |
| `Column` | Column | `InArgument` | `int` | Yes | | The column to start reading from (1-based). |
| `Length` | Length | `InArgument` | `int` | | | Number of characters to read. If not set, reads to the end of the line. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Text` | Text | `OutArgument` | `string` | The text read from the specified position. |

### Options

Standard `TimeoutMS` / `DelayMS` / `WaitType` (defaults `5000` / `300` / `READY`) — see [_common-options.md](TerminalSession/_common-options.md). Defaults work for typical sessions; tune only when scripted activities run faster than the host responds.

## XAML Example

```xml
<uit:TerminalGetTextAtPosition DisplayName="Get Text at Position"
                               Row="[5]"
                               Column="[10]"
                               Length="[20]"
                               Text="[fieldText]"
                               WaitType="READY"
                               DelayMS="300" />
```
