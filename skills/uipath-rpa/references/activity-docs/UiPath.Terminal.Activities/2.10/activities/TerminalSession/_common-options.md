# Common Options

Every child activity of [`TerminalSession`](../TerminalSession.md) carries the same three timing/synchronization properties. Defaults work for typical Telnet/3270/5250 sessions over LAN — tune only when scripted activities run faster than the host responds.

## Common properties

| Name | Type | Typical default | Wait-activity default | Description |
|------|------|-----------------|------------------------|-------------|
| `TimeoutMS` | `InArgument<int>` | `5000` | `30000` (`WaitScreenReady`, `WaitScreenText`, `WaitFieldText`, `WaitTextAtPosition`) | Milliseconds to wait for the operation to complete before throwing a timeout error. |
| `DelayMS` | `InArgument<int>` | `300` | `0` (`WaitScreenReady`) | Milliseconds to wait *after* the activity completes, before proceeding to the next one. |
| `WaitType` | `WaitMode` property | `READY` | `READY` | Pre-execution synchronization mode. See [`WaitMode`](#waitmode-enum) below. `WaitScreenReady` always waits for `READY` regardless of this value. |

Each child doc states its activity-specific defaults in its own Options section, so you do not need to cross-reference this table at authoring time — only when tuning.

## `WaitMode` enum

| Value | Behavior |
|-------|----------|
| `NONE` | Do not wait for the screen state; execute immediately. |
| `READY` | Wait for the keyboard to be unlocked (screen ready for input) before executing. |
| `COMPLETE` | Wait for all screen data to arrive before executing. |

## Tuning notes

- **Raise `TimeoutMS`** for slow hosts or scripted login flows that include intentional pauses (BBS systems, satellite-linked mainframes).
- **Raise `DelayMS`** if the next activity tends to fire before the host has stopped redrawing — visible as missed keystrokes, stale screen reads, or `ErrorWaitReady`.
- **Lower `DelayMS` to `0`** when the next activity is itself a `Wait*` that already blocks until the screen settles.
- **`WaitType="NONE"`** is the right choice when reading screen state for diagnostics or polling — you do not want to block on `READY` if the keyboard is intentionally locked.
- **`WaitType="COMPLETE"`** is rarely needed; reach for it only when you observe partial-screen reads despite `READY` waits succeeding (suggests the provider reports keyboard-unlock before the host has finished its redraw).
