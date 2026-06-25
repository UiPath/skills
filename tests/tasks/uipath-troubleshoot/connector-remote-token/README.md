# Connector Activity — RemoteException token failure (invalid_grant)

Faithful-replay scenario for the `uipath-troubleshoot` skill. Covers TROUB-140
(`ConnectorTriggerActivity`) and the `UiPath.Ipc.RemoteException` case.

## What this exercises

A `ConnectorTriggerActivity` ("Workday: New Invoice (sample)") faults with
`UiPath.Ipc.RemoteException` wrapping `Could not obtain access token.
(invalid_grant)`. `RemoteException` is the generic out-of-process IPC wrapper, so
the agent must **unwrap to the inner message** to find the real cause: the
connection's OAuth token can't refresh (`invalid_grant`). The fix is to
re-authenticate the connection — NOT to treat it as a generic IPC/network crash.

This is the disambiguation test: the agent must not stop at "RemoteException" and
must not misclassify it as a transport/platform failure or a disabled connection.

Signatures (and the `ConnectorTriggerActivity` stack frames) were mined verbatim
from the failed-job telemetry CSV.

## Mock surface

| Command | Fixture |
|---|---|
| `or folders list` | `or-folders-list.json` |
| `or jobs get <key>` | `or-jobs-get.json` (Faulted, Info = Ipc.RemoteException / invalid_grant) |
| `or jobs logs <key> --level Error` | `or-jobs-logs.json` |
| `is connections ping <id>` | `is-connections-ping.json` (AuthenticationFailed, exit 1) |
| `docsai ask` | passthrough |

No project source is staged — the conclusion is reachable from the job evidence
(the unwrapped inner message names the cause).

## Success criteria

`skill_triggered` + `llm_judge` (graded against `RESOLUTION.md`, final response only).
