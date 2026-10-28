# Send Keys

`UiPath.Terminal.Advanced.Activities.TerminalSendKeys`

Sends a raw text string or key sequence directly to the terminal. Use this activity to type text character by character into the terminal at the current cursor position.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals.Advanced  
**Required Scope:** `TerminalSession` — place inside a `TerminalSession.Body` `Sequence`. See [child-activity skeleton](TerminalSession.md#child-activity-skeleton) for a multi-activity example.

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Keys` | Keys | `InArgument` | `string` | Yes | | The text or key sequence to send to the terminal. |

### Options

Standard `TimeoutMS` / `DelayMS` / `WaitType` (defaults `5000` / `300` / `READY`) — see [_common-options.md](TerminalSession/_common-options.md). Defaults work for typical sessions; tune only when scripted activities run faster than the host responds.

## Notes

To send sensitive data such as passwords, use **Send Keys Secure** instead to avoid exposing the value as plain text in the workflow.

## XAML Example

```xml
<uit:TerminalSendKeys DisplayName="Send Keys"
                      Keys="[username]"
                      WaitType="READY"
                      DelayMS="300" />
```
