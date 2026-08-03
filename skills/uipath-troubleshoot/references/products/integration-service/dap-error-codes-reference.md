# DAP Runtime Error Codes (Integration Service)

Integration Service emits a structured error code on every failure: `DAP-<LAYER>-<CODE>`, appended to the user message as _"Error code: DAP-RT-1101."_. Layers:

- **RT** — runtime (execution failures; the agent's primary focus)
- **GE** — general (connection / auth / migration)
- **DT** — design time (Studio canvas; **out of scope** for runtime triage — surfaced directly to the user in Studio, never in execution telemetry)

This reference maps each runtime/general DAP code to its **fault bucket** and its playbook. Classify the bucket first (who can fix it), then route to the playbook (how).

## Telemetry customEvent fields

At runtime the failure is also emitted as a telemetry `customEvent`. Read these fields before classifying — they are the primary evidence:

| Field | Use for root-cause |
|-------|--------------------|
| `ErrorCode` | Numeric IS code — the primary classifier (maps to a playbook below). |
| `ProviderErrorCode` / `ProviderErrorMessage` | The connector / 3rd-party API's own status + message (e.g. the underlying 401/403/429/5xx). **Decisive for `DAP-RT-1101`.** Its presence is also the main signal that the failure is a downstream provider response rather than an IS-side exception. |
| `Error` | Exception type (`RuntimeException`, `GeneralException`). |
| `ErrorMessage` | Human-readable IS message. |
| `RequestId` | Correlation ID — trace the call to the connector. |
| `ConnectionId` | Which connection failed (for auth / connection issues). |

> **"Service error" is a classification you make, not a field to read.** There is **no `IsServiceError` field** emitted in the telemetry. Whether a failure is an *IS-side exception* (the platform/connector itself failed) or a *downstream provider response* (the third-party API returned a status) is a judgment you derive from the `ErrorCode` and message — chiefly from whether a `ProviderErrorCode` / provider status is present. Do not look for an `IsServiceError` value; decide it yourself.

> If the failure surfaced through Maestro (BPMN service task), the same root cause also carries a Maestro IntSvc code (`102002`, `102003`, …). The DAP code is more specific — prefer it when present. The Maestro-keyed playbooks ([connection-invalid.md](./playbooks/connection-invalid.md), [connection-auth-expired.md](./playbooks/connection-auth-expired.md), [operation-failed.md](./playbooks/operation-failed.md), [trigger-not-firing.md](./playbooks/trigger-not-firing.md)) cover the same failures from the Maestro surface.

## Fault ownership — the two-bucket decision

Every IS runtime failure falls into one of two buckets. **Classify first, then explain.** Lead the user-facing answer with the bucket verdict — whether they can fix it themselves or must escalate to the owner team.

### 👤 Bucket A — Customer-resolvable

A configuration, credential, permission, or input problem on the customer's side. **The customer fixes it themselves.**

> _Lead message:_ "This is a configuration/credential issue on your side. Here's what to change…" — then the specific fix from the playbook.

### 🛠 Bucket B — Service-side (not customer-fixable → escalate)

The customer cannot resolve it from their workflow. Two sub-cases:

- **B1 — IS platform / connector defect** (an IS-side exception — no provider status returned): a bug in the activity pack or connector metadata. → _"This is a service-side issue, not something you can fix in your workflow. Contact the owner team (Integration Service)."_
- **B2 — Third-party provider outage / instability** (a downstream provider response — provider status `429` or `5xx`): the upstream connector API is failing. → _"The upstream provider is rate-limiting or down. Wait and retry; escalate if sustained."_

### Fast decision rule

The `ErrorCode` → bucket tables below are the primary classifier — for most codes the bucket follows from the code itself. The distinction between an IS-side exception and a downstream provider response is **your classification**, derived mainly from whether a `ProviderErrorCode` / provider status is present (there is no `IsServiceError` field to read):

1. **No provider status returned** (a config / connection / metadata / trigger-config / platform-token failure inside IS) → IS-side exception → take the code's bucket from the tables (**Bucket A** for the connection/input customer-config codes; **Bucket B1** for platform/connector defects).
2. **A provider status was returned** (`ProviderErrorCode` present — e.g. `DAP-RT-1101`) → downstream provider response → read the status:
   - **4xx auth/input** (`401` / `403` / `404` / `400` / `422`) → **Bucket A** (customer fixes it).
   - **`429` / `5xx`** → **Bucket B2** (provider-side — wait / escalate).

`DAP-RT-1101` is the catch-all that **always** needs the status-code split above.

## Retry semantics

IS auto-retries before surfacing a failure. Knowing this disambiguates transient vs sustained:

- **Retried (max 2):** `429`, `423`, `5xx`. Token auto-refreshed on `401`.
- **Not retried (non-transient):** `408`, `501`, `502`, `504`.
- A `retry-exception` SRE alert means **retries were exhausted** — treat as a sustained provider/network problem (Bucket B2), not a transient blip.

## Code → bucket + playbook map

### 👤 Bucket A — Customer-resolvable

| Code | Name | Root cause | Playbook |
|------|------|------------|----------|
| `DAP-GE-3000` | FailedToGetConnection | Connection deleted, inaccessible, or wrong one selected | [connection-not-resolved.md](./playbooks/connection-not-resolved.md) |
| `DAP-GE-3005` | ConnectionDisabled | Connection is disabled | [connection-not-resolved.md](./playbooks/connection-not-resolved.md) |
| `DAP-RT-1002` | ConnectionIdNull | No connection bound to the activity | [connection-not-resolved.md](./playbooks/connection-not-resolved.md) |
| `DAP-RT-1003` | ArgumentIsRequired | A required input argument is missing | [missing-required-input.md](./playbooks/missing-required-input.md) |
| `DAP-RT-1007` | PropertyIsRequired | A required property is empty | [missing-required-input.md](./playbooks/missing-required-input.md) |
| `DAP-RT-1101` _(4xx)_ | RequestFailed — auth/input subset | Provider `401`/`403` (creds/scope), `404` (not found), `400`/`422` (bad payload) | [request-failed.md](./playbooks/request-failed.md) |

### 🛠 Bucket B1 — IS platform / connector defect (escalate to owner team)

Bugs in the activity pack or connector metadata; the customer cannot work around them. Typically an IS-side exception — no provider status is returned.

| Code | Name | Root cause | Playbook |
|------|------|------------|----------|
| `DAP-RT-1000` | ActivityConfigurationNull | Corrupt/failed-to-deserialize config blob | [activity-configuration-corrupt.md](./playbooks/activity-configuration-corrupt.md) |
| `DAP-RT-1004` | InvalidConfigurationVersion | Config schema version not understood by runtime | [activity-configuration-corrupt.md](./playbooks/activity-configuration-corrupt.md) |
| `DAP-RT-1008` | InvalidActivityConfiguration | Activity configuration is malformed | [activity-configuration-corrupt.md](./playbooks/activity-configuration-corrupt.md) |
| `DAP-RT-1100` | HttpMethodMissing | Generated activity has no HTTP method — incomplete connector metadata | [activity-configuration-corrupt.md](./playbooks/activity-configuration-corrupt.md) |
| `DAP-RT-1053` | TriggerInvalidConfiguration | Trigger object name or operation null/empty — set by connector configuration, not customer-settable | [trigger-execution-failed.md](./playbooks/trigger-execution-failed.md) |
| `DAP-RT-1001` | ServiceProviderNull | Runtime DI/service provider unavailable — internal error | [activity-configuration-corrupt.md](./playbooks/activity-configuration-corrupt.md) |
| `DAP-GE-3004` | FailedToGetAccessToken | IS could not obtain a **first-party UiPath service** token (Orchestrator, Feature Flag service) — NOT a connection credential; often transient | [token-refresh-failed.md](./playbooks/token-refresh-failed.md) |
| `DAP-GE-3001` | InvalidMigration | Activity failed to migrate to a newer schema version | [activity-configuration-corrupt.md](./playbooks/activity-configuration-corrupt.md) |
| `DAP-RT-1005` | ApiResponseMismatch | Response shape ≠ activity output type — connector schema drift | [response-mapping-mismatch.md](./playbooks/response-mapping-mismatch.md) |
| `DAP-RT-1155` `DAP-RT-1156` | DataTableFieldTypeMismatch / TypedDataTableNotConstructedProperly | Output couldn't map into the expected TypedDataTable | [response-mapping-mismatch.md](./playbooks/response-mapping-mismatch.md) |

### 🛠 Bucket B2 — Third-party provider outage / instability (wait / escalate)

A downstream provider response with status `429` or `5xx`, or a network-level failure. Not an IS bug and not customer-fixable.

| Code | Name | Root cause | Playbook |
|------|------|------------|----------|
| `DAP-RT-1101` _(429/5xx)_ | RequestFailed — provider subset | Provider `429` (rate limited) or `5xx` (outage); `ProviderErrorCode` confirms | [request-failed.md](./playbooks/request-failed.md) |
| `DAP-RT-1103` | HttpClientException | Network-level failure — UiPath IS endpoint unreachable from the robot (DNS/connectivity/firewall) | [http-client-exception.md](./playbooks/http-client-exception.md) |
| `DAP-RT-1051` | TriggerExecutionFailed | Trigger evaluation call failed/empty — connector trigger endpoint issue | [trigger-execution-failed.md](./playbooks/trigger-execution-failed.md) |
| `DAP-RT-1050` | TriggerDataMissing | Event payload missing expected event ID — malformed webhook/poll payload | [trigger-execution-failed.md](./playbooks/trigger-execution-failed.md) |

> **Debug-only, never at runtime:** `DAP-RT-1052` (TriggerNoMatches) — emitted only when a project is executed in **debug mode** (the trigger filter matched zero events). It does **not** appear in runtime execution telemetry, so it is out of scope for runtime triage. See [trigger-execution-failed.md](./playbooks/trigger-execution-failed.md).

### Design-time (DT) — out of scope

`DAP-DT-2000`–`2349` (metadata fetch failures, unsupported activity/method, object-not-found, duplicate fields, …) fire in Studio while building a workflow and block the canvas. They do **not** appear in runtime execution telemetry. Do not author runtime playbooks for DT codes — they are surfaced to the user directly in Studio.
