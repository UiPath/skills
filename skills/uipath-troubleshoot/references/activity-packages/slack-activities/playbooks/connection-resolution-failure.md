---
confidence: medium
---

# Slack — Connection resolution failure

## Context

A Slack Integration Service activity (`SendMessage`, `GetUserByEmail`, or any other in the package) faults **at connection resolution** — `BAFAsyncCodeActivity → UiPath.IntegrationCore.Services.ConnectionService.Connect(...)` — before the Slack Web API is ever called. The configured channel, message, or email is irrelevant here: the activity never got far enough to use them. The fix is always about the Integration Service connection.

What this looks like — `System.AggregateException: One or more errors occurred. (<inner message>)` whose inner exception is a `UiPath.IntegrationCore.Utilities.ConnectionException`:

- `Unable to find a connection of type  with the specified Id '<guid>'.` — the configured connection id does not resolve for the running identity. The connection was deleted, or the activity/process is bound to a connection id that doesn't exist in the folder/tenant the robot runs in.
- `The selected connection is no longer valid. Please use another connection or create a new one.` — the connection resolves but its authorization is no longer usable (the Slack OAuth grant was revoked, the workspace token was rotated/expired, or the connection was disabled). This is the highest-volume Slack connection failure in telemetry.

A transient form surfaces the same way:

- `System.AggregateException: One or more errors occurred. (Response status code does not indicate success: 503 (Service Unavailable).) ---> UiPath.CoreIpc.RemoteException: Response status code does not indicate success: 503 (Service Unavailable).` thrown from service discovery (`ServiceDiscoveryStore.GetAccountServices`) during connection resolution. This is a temporary Integration Service / platform outage, not a connection-config problem — it clears on retry.

What can cause it:
- **Connection deleted or wrong id / out of scope** (`Unable to find a connection ...`): the bound connection no longer exists, or the process runs in a folder/tenant where that connection id isn't available to the robot account.
- **Connection revoked / invalidated** (`The selected connection is no longer valid ...`): the Slack authorization behind the connection was revoked or expired (user removed the app, token rotated, connection disabled). Needs re-authorization or a new connection.
- **Transient platform 503**: Integration Service / service discovery momentarily returned 5xx while resolving the connection. Self-recovers on retry.

What to look for:
- The exception **type is `System.AggregateException`** and the inner is a `ConnectionException` (or a `503` `RemoteException`) — this is the marker that the fault is in resolution, not in the Slack call. Compare against [slack-api-error.md](./slack-api-error.md), where the connection resolved and Slack rejected the request.

> **Different cause — do not apply this playbook:**
> - `UiPath.BAF.Infrastructure.Exceptions.BusinessActivityExecutionException` (with `Error Code` / `Message` / `ProviderMessage`) means the connection resolved and **Slack** rejected the request → use [slack-api-error.md](./slack-api-error.md). Note: the BAF form `Unauthorized - An invalid connection id, and/or Bearer token provided.` is an auth failure surfaced through the BAF layer — it is covered in the Slack-API playbook, not here.
> - This is the Integration Service `UiPath.Slack.IntegrationService.Activities` package — not the legacy `UiPath.Slack.Activities` (`SlackScope`/`SlackScopeActivity`).

## Investigation

1. **Confirm the exception type and unwrap.** Verify it is `System.AggregateException`; read `InnerExceptions[0]`. Classify: `Unable to find a connection ...` vs `The selected connection is no longer valid ...` vs a `503` `RemoteException`.
2. **Capture the connection** in evidence — the connection id and the Slack workspace it authenticates to.
3. **For `Unable to find a connection`:** confirm whether the connection still exists in Integration Service, and whether the process runs in a folder/tenant where the robot account can use that connection id.
4. **For `no longer valid`:** check whether the Slack authorization is still active (app not removed from the workspace, token not revoked) and whether the connection is enabled.
5. **For the `503`:** check whether the failure is isolated/intermittent (clears on re-run) versus persistent (then treat as a config problem and re-triage).

## Resolution

- **If `Unable to find a connection of type  with the specified Id '<guid>'`:** re-select a valid Slack connection on the activity (or fix the process's connection binding), and ensure the connection exists in — and the robot account has access to — the folder/tenant the process runs in. Recreate the connection if it was deleted.
- **If `The selected connection is no longer valid. Please use another connection or create a new one.`:** re-authorize the Slack connection in Integration Service (or create a new connection and point the activity at it). Confirm the Slack app wasn't removed from the workspace and the connection is enabled.
- **If the inner error is a transient `503 (Service Unavailable)`:** retry the job. Add a Retry Scope / Orchestrator job retry around the connector activity so transient connection-resolution 5xx self-recover. Only treat it as a configuration problem if it recurs consistently.

If the connection demonstrably exists, is enabled, authorizes cleanly, and is in scope for the robot, yet resolution still fails, the cause is outside the activity — escalate to Integration Service (connection service / identity), not the Slack workspace.
