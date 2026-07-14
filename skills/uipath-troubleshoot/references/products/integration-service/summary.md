# Integration Service Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and testing prerequisites for Integration Service investigations

**DAP runtime error codes:** [dap-error-codes-reference.md](./dap-error-codes-reference.md) — `DAP-<LAYER>-<CODE>` catalog, telemetry customEvent fields, the two-bucket fault-ownership decision, retry semantics, and code → playbook map. **Start here when the error carries a `DAP-…` code.**

**CNS (Connection Service) error codes:** [cns-error-codes-reference.md](./cns-error-codes-reference.md) — `CNS<code>` catalog for the Connection Service HTTP API (connections/connectors/triggers CRUD, portal UI, Maestro and runtime service calls), wire format (`{code, message, traceId}`), telemetry dimensions, overloaded-code traps, retry semantics, and code → playbook map. **Start here when the error carries a `CNS…` code** — when both a DAP and a CNS code are present, the CNS code is the more specific signal.

## Fault ownership — classify before routing

Lead every DAP runtime answer with the bucket. The code → bucket tables are the primary classifier; "service error" is your judgment (there is no `IsServiceError` field), derived from whether a provider status is present. Decision rule: no provider status returned (IS-side exception) → take the code's bucket (**B1** for platform/connector defects, **A** for connection/input customer-config codes); a provider status returned (`ProviderErrorCode` present, e.g. `DAP-RT-1101`) → 4xx auth/input → **Bucket A** (customer fixes it); `429`/`5xx` → **Bucket B2** (provider-side, wait/escalate). Full rule in [dap-error-codes-reference.md](./dap-error-codes-reference.md#fault-ownership--the-two-bucket-decision).

## By DAP runtime error code

Keyed on the IS-native `DAP-RT`/`DAP-GE` code emitted in execution telemetry (and `ProviderErrorCode` for `DAP-RT-1101`). **Bucket** column: 👤 A = customer-resolvable · 🛠 B1 = IS platform/connector defect (escalate) · 🛠 B2 = provider outage (wait/escalate).

| Codes | Bucket | Confidence | Description | Playbook |
|-------|:---:|:---:|-------------|----------|
| `DAP-RT-1101` | 👤 A / 🛠 B2 | High | RequestFailed — route by `ProviderErrorCode`: 4xx auth/input → A; 429/5xx → B2 | [request-failed.md](./playbooks/request-failed.md) |
| `DAP-GE-3004` | 🛠 B1 | High | FailedToGetAccessToken — IS could not get a **first-party UiPath service** token (Orchestrator, Feature Flag service), NOT a connection credential; retry, escalate if sustained | [token-refresh-failed.md](./playbooks/token-refresh-failed.md) |
| `DAP-GE-3000` `DAP-GE-3005` `DAP-RT-1002` | 👤 A | High | Connection not resolved — deleted/cross-workspace, disabled, or no connection bound | [connection-not-resolved.md](./playbooks/connection-not-resolved.md) |
| `DAP-RT-1003` `DAP-RT-1007` | 👤 A | High | Missing required input argument or property | [missing-required-input.md](./playbooks/missing-required-input.md) |
| `DAP-RT-1103` | 🛠 B2 | High | HttpClientException — network-level failure, target host unreachable (DNS/firewall/TLS) | [http-client-exception.md](./playbooks/http-client-exception.md) |
| `DAP-RT-1050` `DAP-RT-1051` `DAP-RT-1053` | 🛠 B2 / 🛠 B1 | Medium | Trigger eval failed or payload missing → B2; `1053` null/empty object/operation (connector config) → B1 escalate. (`DAP-RT-1052` is debug-only — never at runtime) | [trigger-execution-failed.md](./playbooks/trigger-execution-failed.md) |
| `DAP-RT-1005` `DAP-RT-1155` `DAP-RT-1156` | 🛠 B1 | Medium | Response could not be mapped to the activity output type — connector schema drift | [response-mapping-mismatch.md](./playbooks/response-mapping-mismatch.md) |
| `DAP-RT-1000` `DAP-RT-1001` `DAP-RT-1004` `DAP-RT-1008` `DAP-RT-1100` `DAP-GE-3001` | 🛠 B1 | Medium | Activity config null/malformed/unversioned or failed migration — corrupt config blob | [activity-configuration-corrupt.md](./playbooks/activity-configuration-corrupt.md) |

## By CNS (Connection Service) error code

Keyed on the `code` field of the Connection Service API error body (`{ "code": "CNS…", "message": "…", "traceId": "…" }`). ⚠ Several codes are overloaded across subsystems (`CNS1025`, `CNS1001`, `CNS1050`, `CNS1048`/`CNS1026`) — read the message and failing operation before routing; full trap list in [cns-error-codes-reference.md](./cns-error-codes-reference.md).

| Codes | Bucket | Confidence | Description | Playbook |
|-------|:---:|:---:|-------------|----------|
| `CNS1006` `CNS1000` `CNS1049` `CNS1003` | 👤 A | High | Connection not found from the caller's context — deleted, cross-workspace, no connections for connector, stale auth session | [cs-connection-not-found.md](./playbooks/cs-connection-not-found.md) |
| `CNS1008` `CNS1021` `CNS1061` | 👤 A | High | Connection not in authorized state — expired/revoked token, unauthenticated shell, wrong auth type; re-authenticate | [cs-connection-not-authenticated.md](./playbooks/cs-connection-not-authenticated.md) |
| `CNS1045` `CNS1044` `CNS1046` `CNS1047` `CNS1043` `CNS3001` | 👤 A | High | Permission/authorization denied — folder permission (`Connections.View`), OAuth scope, client allow-list, Automation Ops policy | [cs-permission-denied.md](./playbooks/cs-permission-denied.md) |
| `CNS1001` `CNS1002` `CNS1004` → A · `CNS1075` `CNS2045` → B1 | 👤 A / 🛠 B1 | High | Connector unavailable — wrong/missing/disabled connector reference (A); connector deployment/catalog drift (B1, `CNS1075` is a deliberate non-retryable 409) | [cs-connector-unavailable.md](./playbooks/cs-connector-unavailable.md) |
| `CNS1020` `CNS1014` `CNS1025` `CNS1039` → A · `CNS2004` → B1 | 👤 A / 🛠 B1 | High | Trigger CRUD failed — bad ID, delete blocked by active processes, malformed/S2S request (A); persisted config undeserializable (B1) | [cs-trigger-operation-failed.md](./playbooks/cs-trigger-operation-failed.md) |
| `CNS1005` `CNS2000` `CNS1015`–`CNS1019` `CNS1024` `CNS1029` `CNS2011` | 🛠 B1 | Medium | Inbound event-callback processing failed (machine-to-machine) — customer symptom is a trigger that doesn't fire; `CNS1005` has a large benign baseline | [cs-events-callback-failed.md](./playbooks/cs-events-callback-failed.md) |
| `CNS2003` `CNS2005` `CNS2006` `CNS2007` `CNS2009` `CNS2010` `CNS2012` `CNS2001` `CNS2008` `CNS1036` → B1 · `CNS1042` `CNS1101` → B2 | 🛠 B1 / 🛠 B2 | High | Internal dependency failed (SQL/Orchestrator/Identity/message bus → B1) or the third-party provider is erroring/rate-limiting (B2) — retry, then escalate | [cs-dependency-unavailable.md](./playbooks/cs-dependency-unavailable.md) |
| `CNS3002` `CNS1007` `CNS1038` | 🔧 / 👤 A | High | Conflict/duplicate — in-progress migration/backfill lock (ops), duplicate-key create race, duplicate name | [cs-operation-conflict.md](./playbooks/cs-operation-conflict.md) |
| `CNS1050` `CNS1055`–`CNS1074` (Solutions subset) | 👤 A / 🛠 B1 | Medium | Solutions package install/validation — spec errors, connector-version reconciliation, shell connections, stuck publish | [cs-solutions-install-failed.md](./playbooks/cs-solutions-install-failed.md) |

## By symptom (Maestro/Orchestrator-surfaced)

Keyed on the Maestro IntSvc code (`102002`…) or the user-facing message. Same underlying failures from the Maestro/Orchestrator surface.

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Connection Invalid or No Access | High | "connection is invalid or you do not have access" — connection missing, disabled, or caller lacks permissions | [connection-invalid.md](./playbooks/connection-invalid.md) |
| Connection Authentication Expired | High | Connection was working but now fails — OAuth token expired or revoked | [connection-auth-expired.md](./playbooks/connection-auth-expired.md) |
| Trigger Not Firing | Medium | IS trigger configured but events not starting jobs/instances — subscription, permissions, or event mismatch | [trigger-not-firing.md](./playbooks/trigger-not-firing.md) |
| Operation Failed | Medium | IS activity returns error during execution — bad request, unsupported method, or input validation | [operation-failed.md](./playbooks/operation-failed.md) |
| Connector Activity — GeneralException (DAP-GE) | High | `UiPath.IntegrationService.Activities.Runtime.Exceptions.GeneralException` with `DAP-GE-3000` (`Failed to retrieve connection …` — invalid/no-access, `Connections.View` permission, or Bad Gateway) or `DAP-GE-3005` (`Connection is disabled. Please enable the connection to continue.`). Connection-resolution failure in ConnectorActivity / ConnectorHttpActivity / ConnectorTriggerActivity. | [connector-general-exception.md](./playbooks/connector-general-exception.md) |
| Connector Activity — RuntimeException (DAP-RT) | High | `UiPath.IntegrationService.Activities.Runtime.Exceptions.RuntimeException` with `DAP-RT-1002` (`Connection ID is empty.`), `DAP-RT-1003` (`<field> field is required.`), `DAP-RT-1052` (`Trigger activity could not find any matches.`), or `DAP-RT-1101` (`Status code: BadRequest./NotFound.`). Binding/input/trigger/operation failure in ConnectorActivity / ConnectorTriggerActivity. | [connector-runtime-exception.md](./playbooks/connector-runtime-exception.md) |
| Connector Activity — RemoteException (IPC) | Medium | `UiPath.Ipc.RemoteException` / `UiPath.CoreIpc.RemoteException` — out-of-process connector executor fault crossing the IPC boundary (no DAP code). Match on the **unwrapped inner message**: token/auth, transport, or downstream HTTP (404/502/503). Disambiguate from non-connector RemoteExceptions. | [connector-remote-exception.md](./playbooks/connector-remote-exception.md) |
| Connector Activity — NullReferenceException | Medium | `System.NullReferenceException` on/after a connector activity — typically enumerating a null connector output (`ForEach` over `SWEntities.*_List`), an unmapped output, or a null required input. | [connector-null-reference.md](./playbooks/connector-null-reference.md) |
| Connector Activity — AggregateException | Low | `System.AggregateException` on a connector activity — async connector fault(s). The real cause is `InnerExceptions[0]`; unwrap and re-classify. | [connector-aggregate-exception.md](./playbooks/connector-aggregate-exception.md) |
