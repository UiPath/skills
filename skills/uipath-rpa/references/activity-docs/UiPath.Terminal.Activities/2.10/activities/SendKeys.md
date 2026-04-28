# Send Keys

`UiPath.Terminal.Advanced.Activities.TerminalSendKeys`

Sends a raw text string or key sequence directly to the terminal. Use this activity to type text character by character into the terminal at the current cursor position.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals.Advanced  
**Required Scope:** `TerminalSession`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Keys` | Keys | `InArgument` | `string` | Yes | | The text or key sequence to send to the terminal. |

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `TimeoutMS` | TimeoutMS | `InArgument` | `int` | `5000` | Milliseconds to wait for the operation to complete. |
| `DelayMS` | DelayMS | `InArgument` | `int` | `300` | Milliseconds to wait after executing the activity. |
| `WaitType` | WaitType | `Property` | `WaitMode` | `READY` | Determines how to wait for the terminal screen before sending. |

### Enum Reference

**`WaitMode`**: `NONE`, `READY`, `COMPLETE`

## Notes

To send sensitive data such as passwords, use **Send Keys Secure** instead to avoid exposing the value as plain text in the workflow.

## XAML Example

```xml
<ta:TerminalSendKeys DisplayName="Send Keys"
                      Keys="[username]" />
```
