# Wait Screen Ready

`UiPath.Terminal.Advanced.Activities.TerminalWaitScreenReady`

Waits until the terminal keyboard is unlocked and the screen is ready to accept input. Use this activity after sending a command or key that triggers host-side processing, to ensure subsequent activities do not execute before the host responds.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals.Advanced  
**Required Scope:** `TerminalSession` — place inside a `TerminalSession.Body` `Sequence`. See [child-activity skeleton](TerminalSession.md#child-activity-skeleton) for a multi-activity example.

## Properties

### Input

This activity has only the standard timing/synchronization options — see [_common-options.md](TerminalSession/_common-options.md). It **always waits for `READY`** regardless of the `WaitType` value, and uses `DelayMS=0` because the screen is known ready when the activity completes — there is nothing to settle.

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `TimeoutMS` | TimeoutMS | `InArgument` | `int` | | `30000` | Milliseconds to wait for the screen to become ready before throwing a timeout error. |
| `DelayMS` | DelayMS | `InArgument` | `int` | | `0` | Milliseconds to wait after the activity completes, before proceeding to the next one. |
| `WaitType` | WaitType | `Property` | `WaitMode` | | `READY` | Pre-execution synchronization mode. Ignored by this activity — it always waits for `READY`. |

## Notes

- This activity has `DelayMS = 0` by default (unlike most other activities which default to 300 ms).
- Commonly placed after a **Send Control Key** (Transmit/Enter) to wait for the host to respond before reading or writing fields.
- **Flaky in the first few seconds after a fresh TLS connect.** When placed as the very first child activity in a `TerminalSession.Body` (i.e. immediately after the session opens), this activity can intermittently throw `ErrorWaitReady` — identical XAML succeeds on one run and fails on the next. The cause appears to be a race against TN5250 protocol negotiation completing after the TLS handshake. Workarounds: rely on the parent `TerminalSession.DelayMS` (raise it to 3000–5000 ms for TLS hosts) to handle initial settling and omit the leading `WaitScreenReady`, OR retry the activity on failure. After the first interaction with the host, the activity is reliable.

## XAML Example

```xml
<uit:TerminalWaitScreenReady DisplayName="Wait Screen Ready"
                              TimeoutMS="[30000]"
                              WaitType="READY"
                              DelayMS="0" />
```
