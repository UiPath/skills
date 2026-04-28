# Send Keys Secure

`UiPath.Terminal.Advanced.Activities.TerminalSendKeysSecure`

Sends a `SecureString` value (such as a password) to the terminal without exposing it as plain text in the workflow. The secure string is converted to characters in memory and sent immediately, then the unmanaged memory buffer is zeroed out.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals.Advanced  
**Required Scope:** `TerminalSession`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `SecureText` | SecureText | `InArgument` | `SecureString` | Yes | | The secure string value to send. Typically sourced from an Asset, credential variable, or the `SSHPassword` output of a Get Credential activity. |

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `TimeoutMS` | TimeoutMS | `InArgument` | `int` | `5000` | Milliseconds to wait for the operation to complete. |
| `DelayMS` | DelayMS | `InArgument` | `int` | `300` | Milliseconds to wait after executing the activity. |
| `WaitType` | WaitType | `Property` | `WaitMode` | `READY` | Determines how to wait for the terminal screen before sending. |

### Enum Reference

**`WaitMode`**: `NONE`, `READY`, `COMPLETE`

## Notes

- Uses `Marshal.SecureStringToGlobalAllocUnicode` internally; the unmanaged buffer is freed immediately after sending.
- Do not use **Send Keys** for passwords — use this activity instead to prevent credential exposure in logs or workflow snapshots.

## XAML Example

```xml
<ta:TerminalSendKeysSecure DisplayName="Send Keys Secure"
                             SecureText="[passwordSecureString]" />
```
