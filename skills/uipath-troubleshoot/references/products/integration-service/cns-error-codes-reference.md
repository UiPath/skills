# CNS Error Codes (Connection Service)

Connection Service — the Integration Service component that stores and resolves **connections, connectors, and triggers** — stamps a structured `CNS<code>` error code on every API failure. These are distinct from the `DAP-…` codes ([dap-error-codes-reference.md](./dap-error-codes-reference.md)): DAP codes come from the **connector activity runtime** on the robot; CNS codes come from the **Connection Service HTTP API** that the runtime, the portal UI, Maestro, and other UiPath services call. A single incident often carries both — e.g. a runtime `DAP-GE-3000` whose underlying service call failed with `CNS1006`. **When a CNS code is visible, prefer it — it is the more specific signal.**

## Wire format

Every failed Connection Service API call returns:

```json
{ "code": "CNS1045", "message": "<user-facing text>", "traceId": "<W3C trace id>" }
```

- `code` — the stable CNS error code (this catalog).
- `message` — resolved user-facing text (safe to show; technical detail stays in service logs).
- `traceId` — also returned as a response header; **always capture it** — it is the correlation key the owner team uses to find the request in telemetry.

**Where these codes surface in RPA productivity activities:** the modern Microsoft 365 / Google Workspace activity packages resolve their Integration Service connection and fetch the OAuth token through this API at runtime — so a failing activity often carries the CNS body inside a `UiPath.ConnectionClient.Contracts.ConnectionHttpException` (raw, or quoted verbatim in the wrapped `Office365Exception`/`GSuiteException` message). The runtime token fetch is the single biggest customer-facing source of `CNS1008`/`CNS1006`/`CNS1045`. Activity-side routing lives in the [O365](../../activity-packages/o365-activities/investigation_guide.md) and [Google Workspace](../../activity-packages/gsuite-activities/investigation_guide.md) investigation guides.

Code families:

- **`CNS1xxx`** — client/validation errors (4xx): resolution failures, bad input, permissions, connector lifecycle, Solutions packages.
- **`CNS2xxx`** — internal/server errors (5xx): dependency failures, plus the tenant-migration export/import family (`CNS2030`–`CNS2046`, internal tooling only).
- **`CNS3xxx`** — governance and concurrency: `CNS3001` (policy forbidden), `CNS3002` (single-flight conflict).

Status→code fallbacks: when a downstream dependency error reaches the middleware unwrapped, the status is mapped to a generic code — 503→`CNS2007`, 403→`CNS1044`, 401→`CNS1047`, 400→`CNS1048`, 404→`CNS1049`, 424→`CNS1101`, unknown→`CNS2006`, outbound timeout→`CNS2010`. These generic codes therefore say *less* than the specific ones — route on the message and failing operation too.

> **⚠ Overloaded codes — never route on the code alone.** Several codes are reused across unrelated subsystems. The ones that bite:
> - `CNS1025` "TriggerRequestInvalid" also fires from **connection** delete/rename for *"In S2S context, the folder key is required"*, and one 500-class notification branch.
> - `CNS1001` "ConnectorKeyOrIdInvalid" is also thrown for an invalid **trigger** lookup on one path.
> - `CNS1050` is **two different constants**: `EventModeNotSupported` (make-connection-call API) and `InvalidSolutionArchive` (corrupt Solutions package).
> - `CNS1048`/`CNS1026` are generic catch-alls across governance, message-bus events, Solutions, and tenant lifecycle.
> Always read the `message` and identify the failing operation before picking a playbook.

## Telemetry (owner team)

In the region's Connection Service App Insights (`cloud_RoleName` starts with `connection-service`):

- Primary signal: `traces`/`exceptions` matching `Connection Service error reported: [StatusCode: …, ErrorCode: "CNS…", ErrorReason: "…"]`, with `customDimensions.ErrorCode` where populated. Query **both** traces and exceptions — errors logged with an exception land in `exceptions`, not `traces`.
- Structured failure dimensions (rolling out behind the `EnableStructuredFailureTelemetry` flag): `FailureErrorCode`, `FailureDependency`, `FailureStatusCode`, `FailureIsTransient`, `FailureUserMessageKey` (e.g. `FolderAuth.403.CNS1045`), `FailureTechnicalMessage` — emitted on customEvents and a structured log line.
- Volume triage: `union traces, exceptions | where cloud_RoleName startswith "connection-service" | extend ec = tostring(customDimensions.ErrorCode) | where ec startswith "CNS" | summarize count() by ec, bin(timestamp, 1h)`.

30-day production baseline (one large region) for calibration — the top codes by volume: `CNS1005` (~97k, orphaned event callbacks — mostly benign background), `CNS1006` (~69k), `CNS1008` (~37k), `CNS1001` (~25k), `CNS1045` (~20k); everything else is under 1k/month. A code in the top five behaving at baseline is normal noise; a step change is an incident.

## Fault ownership

Same two-bucket discipline as the DAP codes — classify **who can fix it** first, then route:

- **👤 Bucket A — customer/admin-resolvable:** wrong or deleted references, unauthenticated connections, missing folder permissions/scopes, governance policy choices, bad request payloads, Solutions package spec issues.
- **🛠 Bucket B1 — service-side (escalate):** dependency failures (SQL, Orchestrator, Identity, message bus), event-callback processing, corrupt persisted config, connector deployment drift, stuck install pipelines.
- **🛠 Bucket B2 — third-party provider:** `CNS1042`/`CNS1101` — the provider behind the connector is erroring or rate-limiting; wait/retry, escalate only if the provider is healthy.
- **🔧 Internal ops tooling:** `CNS3002` and `CNS2030`–`CNS2046` — migration/backfill machinery; customers never trigger these directly.

## Retry semantics

Transience is derived from **status and dependency, not the code**: 408/429/502/503/504, and anything from the Db/Cache/MessageBus/Identity dependencies, is transient-classified (background flows auto-retry; interactive calls surface immediately). All other 4xx are permanent — retrying `CNS1045` or `CNS1006` will never succeed. **`CNS1075` is deliberately a non-retryable 409** so that runtime clients don't retry-loop on an unpublished connector. `CNS2010` (timeout) surfaces as 500 but is worth one retry.

## Code → playbook map

### 👤 Bucket A — customer/admin-resolvable

| Codes | Root cause | Playbook |
|-------|------------|----------|
| `CNS1006` `CNS1000` `CNS1049` `CNS1003` | Connection not found from the caller's context — deleted, cross-workspace, no connections yet, stale auth session | [cs-connection-not-found.md](./playbooks/cs-connection-not-found.md) |
| `CNS1008` `CNS1021` `CNS1061` | Connection not in authorized state — expired/revoked token, unauthenticated shell, wrong auth type | [cs-connection-not-authenticated.md](./playbooks/cs-connection-not-authenticated.md) |
| `CNS1045` `CNS1044` `CNS1046` `CNS1047` `CNS1043` `CNS3001` | Folder permission / scope / client / governance-policy denial | [cs-permission-denied.md](./playbooks/cs-permission-denied.md) |
| `CNS1001` `CNS1002` `CNS1004` | Connector reference wrong, missing, or disabled | [cs-connector-unavailable.md](./playbooks/cs-connector-unavailable.md) |
| `CNS1020` `CNS1014` `CNS1025` `CNS1039` | Trigger CRUD — bad ID, delete blocked by active processes, malformed/S2S-folder-key request, bad interval | [cs-trigger-operation-failed.md](./playbooks/cs-trigger-operation-failed.md) |
| `CNS1038` `CNS1007` `CNS1032` `CNS1033` | Duplicate name / duplicate-key create race / name validation | [cs-operation-conflict.md](./playbooks/cs-operation-conflict.md) |
| `CNS1050` `CNS1055` `CNS1058` `CNS1059` `CNS1064` `CNS1066`–`CNS1069` `CNS1071` `CNS1072` `CNS1074` | Solutions package spec, connector-version reconciliation, shell connections | [cs-solutions-install-failed.md](./playbooks/cs-solutions-install-failed.md) |

### 🛠 Bucket B1 — service-side (escalate if sustained)

| Codes | Root cause | Playbook |
|-------|------------|----------|
| `CNS2003` `CNS2005` `CNS2006` `CNS2007` `CNS2009` `CNS2010` `CNS2012` `CNS2001` `CNS2008` `CNS1036` | A UiPath-internal dependency (SQL / Orchestrator / Identity / message bus / connector platform) failed | [cs-dependency-unavailable.md](./playbooks/cs-dependency-unavailable.md) |
| `CNS1005` `CNS2000` `CNS1015`–`CNS1019` `CNS1024` `CNS1029` `CNS2011` | Inbound event-callback processing failed (machine-to-machine; customer sees "trigger didn't fire") | [cs-events-callback-failed.md](./playbooks/cs-events-callback-failed.md) |
| `CNS1075` `CNS2045` | Connector deployment state broken / event catalog drift | [cs-connector-unavailable.md](./playbooks/cs-connector-unavailable.md) |
| `CNS2004` | Persisted trigger config undeserializable | [cs-trigger-operation-failed.md](./playbooks/cs-trigger-operation-failed.md) |
| `CNS1060` `CNS1063` `CNS1065` `CNS1056` `CNS1057` `CNS1070` | Solutions install pipeline failures | [cs-solutions-install-failed.md](./playbooks/cs-solutions-install-failed.md) |

### 🛠 Bucket B2 — third-party provider

| Codes | Root cause | Playbook |
|-------|------------|----------|
| `CNS1042` `CNS1101` | The provider behind the connector returned 5xx / rate-limited / rejected | [cs-dependency-unavailable.md](./playbooks/cs-dependency-unavailable.md) |

### 🔧 Internal — no customer playbook

- `CNS3002` — single-flight lock on migration/backfill jobs; ops waits or overrides ([cs-operation-conflict.md](./playbooks/cs-operation-conflict.md)).
- `CNS2030`–`CNS2044`, `CNS2046` — tenant-migration export/import pipeline (S2S-gated internal endpoints; a customer cannot reach them). Failures here are handled by the owning ops workflow, not support triage.
- **Defined but never thrown** (ignore if "seen" — the sighting is wrong): `CNS1051`(ConnectionCreateUpdateError twin) `CNS1052` `CNS1053` `CNS1054` `CNS1062` `CNS2033`.
