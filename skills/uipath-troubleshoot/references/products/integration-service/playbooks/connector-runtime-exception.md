---
confidence: high
---

# Connector Activity — RuntimeException (DAP-RT)

## Context

What this looks like — robot exception `UiPath.IntegrationService.Activities.Runtime.Exceptions.RuntimeException` with a `DAP-RT-` error code. Unlike GeneralException (connection-resolution), these fault during activity setup or the connector operation itself. The code maps to an exact cause:

| Code | Verbatim message | Cause |
|------|------------------|-------|
| `DAP-RT-1002` | `Connection ID is empty.` | No connection bound to the activity — the `ConnectionId` was never set (or its binding/asset resolved to empty at runtime). |
| `DAP-RT-1003` | `<field> field is required.` | A required input field of the connector operation is empty/null at runtime. |
| `DAP-RT-1052` | `Trigger activity could not find any matches.` | `ConnectorTriggerActivity` sample/debug lookup returned zero events — the trigger object has no matching records to pull. |
| `DAP-RT-1101` | `Status code: BadRequest.` / `Status code: NotFound.` (and other HTTP statuses) — accompanied by a `ProviderMessage` / `ProviderErrorCode` block with the downstream provider's own error | The connector operation reached the external service, which rejected the request (bad input, missing/renamed resource, unsupported operation). |

Which activities produce this:
- **ConnectorActivity** — DAP-RT-1002, DAP-RT-1003, DAP-RT-1101.
- **ConnectorTriggerActivity** — DAP-RT-1052 (and DAP-RT-1002 if the trigger has no connection).

> Same `RuntimeException` class, different failure: a **`Response content too large`** message (the provider call succeeded but the response exceeded the 8 MB JSON limit — no provider status) is NOT one of these codes → [response-content-too-large.md](./response-content-too-large.md).

What can cause it:
- **1002:** activity dropped its connection binding (common after copy/paste between projects, or a deleted asset feeding `ConnectionId`).
- **1003:** an input argument is empty because an upstream variable was null, or a mandatory field was left unmapped.
- **1052:** the configured trigger object genuinely has no events in the sampled window — usually expected during setup/debug, not a defect.
- **1101:** input doesn't match the operation's schema; referenced record doesn't exist in the external service; the external API changed/deprecated the endpoint.

## Investigation

1. **Read the exact `DAP-RT` code from the job log / Info** — it routes the rest. For 1002/1003/1052 the cause is known from the code alone; for 1101 read the full inner detail (status + body).
2. For **1002**: if source is available, inspect the activity's `ConnectionId` binding in the workflow (XAML/code) and check whether it points at an asset/variable that resolved empty.
3. For **1003**: identify which field — the message names it. Trace the upstream value.
4. For **1101**: read the `ProviderMessage` / `ProviderErrorCode` block in the error first — it carries the external provider's own error (e.g. `providerErrorCode - 404`, `reason=notFound`, `location=fileId`), which names the exact failing parameter and HTTP status. Then `uip is resources describe <connector-key> <object>` to confirm required fields and supported operations; compare against what the activity sent. Check whether the referenced record/file exists.

## Resolution

- **DAP-RT-1002:** set/repair the activity's connection binding so a valid connection ID resolves at runtime; verify any asset feeding `ConnectionId` exists in the runner's folder.
- **DAP-RT-1003:** populate the named required field, or guard the upstream value so it is never null.
- **DAP-RT-1052:** for `ConnectorTriggerActivity`, this is usually benign — confirm the trigger object actually has events; if events are expected but absent, see [trigger-not-firing.md](./trigger-not-firing.md).
- **DAP-RT-1101:** this is the activity-package form of an operation error — follow [operation-failed.md](./operation-failed.md) (fix input to match the schema, verify the resource exists, or update for an API change).
