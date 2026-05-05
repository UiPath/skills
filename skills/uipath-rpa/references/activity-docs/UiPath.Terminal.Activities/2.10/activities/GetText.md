# Get Text

`UiPath.Terminal.Activities.TerminalGetText`

Reads the entire visible text content of the terminal screen and returns it as a string.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals  
**Required Scope:** `TerminalSession`

## Properties

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Text` | Text | `OutArgument` | `string` | The full text content of the terminal screen. |

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `TimeoutMS` | TimeoutMS | `InArgument` | `int` | `5000` | Milliseconds to wait for the operation to complete. |
| `DelayMS` | DelayMS | `InArgument` | `int` | `300` | Milliseconds to wait after executing the activity. |
| `WaitType` | WaitType | `Property` | `WaitMode` | `READY` | Determines how to wait for the terminal screen before reading. |

### Enum Reference

**`WaitMode`**: `NONE`, `READY`, `COMPLETE`

- `NONE` — Do not wait; read immediately.
- `READY` — Wait for the keyboard to be unlocked (screen ready for input).
- `COMPLETE` — Wait for all data to arrive on the screen.

## XAML Example

```xml
<uit:TerminalGetText DisplayName="Get Text"
                   Text="[screenText]"
                   WaitType="READY"
                   DelayMS="300" />
```
