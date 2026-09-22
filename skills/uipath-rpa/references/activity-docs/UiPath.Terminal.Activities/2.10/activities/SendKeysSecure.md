# Send Keys Secure

`UiPath.Terminal.Advanced.Activities.TerminalSendKeysSecure`

Sends a `SecureString` value (such as a password) to the terminal without exposing it as plain text in the workflow. The secure string is converted to characters in memory and sent immediately, then the unmanaged memory buffer is zeroed out.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals.Advanced  
**Required Scope:** `TerminalSession` — place inside a `TerminalSession.Body` `Sequence`. See [child-activity skeleton](TerminalSession.md#child-activity-skeleton) for a multi-activity example.

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `SecureText` | SecureText | `InArgument` | `SecureString` | Yes | | The secure string value to send. Typically sourced from an Asset, credential variable, or the `SSHPassword` output of a Get Credential activity. |

### Options

Standard `TimeoutMS` / `DelayMS` / `WaitType` (defaults `5000` / `300` / `READY`) — see [_common-options.md](TerminalSession/_common-options.md). Defaults work for typical sessions; tune only when scripted activities run faster than the host responds.

## Notes

- Uses `Marshal.SecureStringToGlobalAllocUnicode` internally; the unmanaged buffer is freed immediately after sending.
- Do not use **Send Keys** for passwords — use this activity instead to prevent credential exposure in logs or workflow snapshots.

## XAML Example

```xml
<uit:TerminalSendKeysSecure DisplayName="Send Keys Secure"
                             SecureText="[passwordSecureString]"
                             WaitType="READY"
                             DelayMS="300" />
```
