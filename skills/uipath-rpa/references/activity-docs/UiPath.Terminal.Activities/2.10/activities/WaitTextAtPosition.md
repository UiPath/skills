# Wait Text at Position

`UiPath.Terminal.Advanced.Activities.TerminalWaitTextAtPosition`

Waits until a specific row and column position on the terminal screen contains the expected text.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals.Advanced  
**Required Scope:** `TerminalSession`

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

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `TimeoutMS` | TimeoutMS | `InArgument` | `int` | `30000` | Milliseconds to wait for the text to appear before throwing a timeout error. |
| `DelayMS` | DelayMS | `InArgument` | `int` | `300` | Milliseconds to wait after executing the activity. |
| `WaitType` | WaitType | `Property` | `WaitMode` | `READY` | Determines how to wait for the terminal screen. |

### Enum Reference

**`WaitMode`**: `NONE`, `READY`, `COMPLETE`

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
