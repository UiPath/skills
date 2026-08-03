---
confidence: medium
---

# Connector Activity — RemoteException (Ipc / CoreIpc)

## Context

What this looks like — robot exception `UiPath.Ipc.RemoteException` or `UiPath.CoreIpc.RemoteException` (the two are the same phenomenon across two IPC library generations). Connector activities execute **out-of-process** in the connector executor; an unhandled fault in that process crosses the IPC boundary wrapped in `RemoteException`. There is **no `DAP-` code** — the operative signal is the **unwrapped inner message** after the `RemoteException:` prefix (follow `--->` chains to the innermost text).

For connector activities (`ConnectorActivity`, `ConnectorTriggerActivity`) the inner message is typically one of:
- **Token / auth:** `Could not obtain access token. (...)`, `Could not obtain user token. ...`, `invalid_grant`, `The Client ID or Client Secret is incorrect.`, `1 or more scope requested are not robot scopes.`, `The user is no longer a member of the organization.`
- **Transport:** `An existing connection was forcibly closed by the remote host.`, `Unable to read data from the transport connection`, `The SSL connection could not be established`, `The operation has timed out.`, `The request was canceled due to the configured HttpClient.Timeout`.
- **Downstream HTTP:** `Response status code does not indicate success: 404 (Not Found).` / `502 (Bad Gateway).` / `503 (Service Unavailable).`

> **Different cause — do NOT apply this playbook.** `RemoteException` is a generic robot↔executor wrapper, not Integration-Service-specific. The same class wraps UI Automation, Computer Vision (`Cloud Vision API ... disabled`), `Could not find a process named '<x>' in folder '<workspace>'` (robot/folder assignment), assembly-load failures (`Could not load file or assembly ...`), and missing-file errors. Only treat it as a connector failure when the faulted activity is a connector activity (`*.IntegrationService.Activities.*` / `Connector*`) **and** the inner message is auth/transport/HTTP as above. If the inner message is process-not-found, assembly-load, or a non-connector activity, route to the matching Orchestrator / runtime playbook instead.

## Investigation

1. **Unwrap to the innermost message.** Strip the `RemoteException:` prefix and follow every `--->` to the deepest inner exception. Classify it: token/auth, transport, or downstream HTTP. Match on that, not on the `RemoteException` class name.
2. **Confirm the faulted activity is a connector activity** (triage's activity name). If not, this playbook does not apply — see the disambiguation note above.
3. For **auth** inner messages: `uip is connections ping <connection-id>` — confirm the connection's token state; see [connection-auth-expired.md](./connection-auth-expired.md).
4. For **transport / 5xx / 503**: check whether the failure is transient (succeeds on retry) or persistent. Transient transport/5xx is an external-service or platform availability issue, not a workflow defect.
5. For **404**: the referenced resource (record/endpoint) does not exist in the external service — verify the ID/path the operation used.

## Resolution

- **Token / auth inner message:** re-authenticate the connection (`uip is connections edit <connection-id>` or the UI). If `invalid_grant` / revoked / scope errors, re-authorize the app in the external service first. If `user is no longer a member of the organization`, the connection's owning identity must be replaced.
- **Transport / SSL / timeout / 5xx / 503:** treat as transient — retry the job. If persistent, check the external service's status and any network egress / proxy between the robot and the service; raise the activity timeout only after ruling out a real outage.
- **404 (downstream):** correct the resource identifier the operation references; confirm the record exists in the external service.
- **Inner message is non-connector** (process-not-found, assembly-load, missing file): stop — this is not an Integration Service failure; investigate under the relevant Orchestrator / runtime playbook.
