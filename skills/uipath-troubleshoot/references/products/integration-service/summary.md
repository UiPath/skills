# Integration Service Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and testing prerequisites for Integration Service investigations

**DAP runtime error codes:** [dap-error-codes-reference.md](./dap-error-codes-reference.md) — `DAP-<LAYER>-<CODE>` catalog, telemetry customEvent fields, the two-bucket fault-ownership decision, retry semantics, and code → playbook map. **Start here when the error carries a `DAP-…` code.**

## Fault ownership — classify before routing

Lead every DAP runtime answer with the bucket. Decision rule: `IsServiceError = false` → **Bucket B1** (escalate). `IsServiceError = true` → `ProviderErrorCode` 4xx auth/input → **Bucket A** (customer fixes it); `429`/`5xx` → **Bucket B2** (provider-side, wait/escalate). Full rule in [dap-error-codes-reference.md](./dap-error-codes-reference.md#fault-ownership--the-two-bucket-decision).

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

## By symptom (Maestro/Orchestrator-surfaced)

Keyed on the Maestro IntSvc code (`102002`…) or the user-facing message. Same underlying failures from the Maestro/Orchestrator surface.

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Connection Invalid or No Access | High | "connection is invalid or you do not have access" — connection missing, disabled, or caller lacks permissions | [connection-invalid.md](./playbooks/connection-invalid.md) |
| Connection Authentication Expired | High | Connection was working but now fails — OAuth token expired or revoked | [connection-auth-expired.md](./playbooks/connection-auth-expired.md) |
| Trigger Not Firing | Medium | IS trigger configured but events not starting jobs/instances — subscription, permissions, or event mismatch | [trigger-not-firing.md](./playbooks/trigger-not-firing.md) |
| Operation Failed | Medium | IS activity returns error during execution — bad request, unsupported method, or input validation | [operation-failed.md](./playbooks/operation-failed.md) |
