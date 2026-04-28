# Wait Screen Ready

`UiPath.Terminal.Advanced.Activities.TerminalWaitScreenReady`

Waits until the terminal keyboard is unlocked and the screen is ready to accept input. Use this activity after sending a command or key that triggers host-side processing, to ensure subsequent activities do not execute before the host responds.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals.Advanced  
**Required Scope:** `TerminalSession`

## Properties

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `TimeoutMS` | TimeoutMS | `InArgument` | `int` | `30000` | Milliseconds to wait for the screen to become ready before throwing a timeout error. |
| `DelayMS` | DelayMS | `InArgument` | `int` | `0` | Milliseconds to wait after executing the activity. Defaults to 0 (no delay). |
| `WaitType` | WaitType | `Property` | `WaitMode` | `READY` | The wait mode; this activity always waits for the READY state regardless of this setting. |

### Enum Reference

**`WaitMode`**: `NONE`, `READY`, `COMPLETE`

## Notes

- This activity has `DelayMS = 0` by default (unlike most other activities which default to 300 ms).
- Commonly placed after a **Send Control Key** (Transmit/Enter) to wait for the host to respond before reading or writing fields.

## XAML Example

```xml
<ta:TerminalWaitScreenReady DisplayName="Wait Screen Ready"
                              TimeoutMS="[30000]" />
```
