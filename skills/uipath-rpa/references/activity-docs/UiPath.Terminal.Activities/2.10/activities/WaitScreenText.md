# Wait Screen Text

`UiPath.Terminal.Activities.TerminalWaitScreenText`

Waits until a specified text string appears anywhere on the terminal screen. Useful for synchronizing with host-side processing that updates the screen.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals  
**Required Scope:** `TerminalSession`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Text` | Text | `InArgument` | `string` | Yes | | The text string to wait for on the screen. |
| `MatchCase` | MatchCase | `InArgument` | `bool` | | `false` | When `true`, the text comparison is case-sensitive. |

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `TimeoutMS` | TimeoutMS | `InArgument` | `int` | `30000` | Milliseconds to wait for the text to appear before throwing a timeout error. |
| `DelayMS` | DelayMS | `InArgument` | `int` | `300` | Milliseconds to wait after executing the activity. |
| `WaitType` | WaitType | `Property` | `WaitMode` | `READY` | Determines how to wait for the terminal screen. |

### Enum Reference

**`WaitMode`**: `NONE`, `READY`, `COMPLETE`

- `NONE` — Do not wait for screen ready; check for text immediately.
- `READY` — Wait for the keyboard to be unlocked first.
- `COMPLETE` — Wait for all data to arrive on the screen first.

## XAML Example

```xml
<uit:TerminalWaitScreenText DisplayName="Wait Screen Text"
                           Text="[&quot;READY&quot;]"
                           TimeoutMS="[30000]"
                           WaitType="READY"
                           DelayMS="300" />
```
