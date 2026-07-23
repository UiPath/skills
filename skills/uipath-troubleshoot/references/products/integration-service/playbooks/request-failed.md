---
confidence: high
---

# Request Failed (DAP-RT-1101)

> **Fault bucket:** depends on `ProviderErrorCode`. 4xx auth/input (`401`/`403`/`404`/`400`/`422`) → **👤 Bucket A** (customer fixes credentials/permissions/input). `429`/`5xx` → **🛠 Bucket B2** (provider-side outage/rate-limit — wait/retry, escalate if sustained). Always split on the status code before answering. See [dap-error-codes-reference.md](../dap-error-codes-reference.md#fault-ownership--the-two-bucket-decision).

## Context

What this looks like:
- Error code `DAP-RT-1101` (RequestFailed) — the most common IS runtime failure
- A `ProviderErrorCode` / provider status is present — the connector's downstream API returned an error (a downstream provider response, not an IS-side exception; there is no `IsServiceError` field to read)
- Maps to the `http-4xx` / `retry-exception` SRE alerts

The DAP code alone does not name the root cause — **the `ProviderErrorCode` (the 3rd-party API's own status) does.** Route on it:

| Provider status | Meaning | Direction |
|---|---|---|
| 401 | Token rejected by the provider | Auth — the connection's OAuth token is expired/revoked; re-authenticate (see [connection-auth-expired.md](./connection-auth-expired.md)) |
| 403 | Authenticated but not permitted | Connection scope/permissions too narrow for the operation |
| 404 | Object/record not found | Input references a resource that does not exist in the external service |
| 429 | Rate limited | Quota exceeded — retries (max 2) already exhausted |
| 5xx | Provider outage | Transient on the provider side; retries exhausted = sustained outage |

Not this playbook: HTTP 429 with `Failed to apply` in the Maestro Autopilot designer (design-time, no `DAP-RT-1101`/`ProviderErrorCode`) is not a connector fault → [autopilot-429](../../maestro/playbooks/autopilot-429.md).

What to look for:
- `ProviderErrorCode` + `ProviderErrorMessage` in the customEvent — the decisive evidence
- `RequestId` — correlates the IS call to the connector log
- Whether the same operation worked before (regression vs misconfiguration)
- Whether a `retry-exception` alert fired — means 429/5xx retries were exhausted (sustained, not a blip)

## Investigation

1. **Read `ProviderErrorCode` / `ProviderErrorMessage` from the customEvent first.** This is the classifier — do not draw conclusions from `DAP-RT-1101` alone.
2. **Read the connection resource file** — if source code is available, find the connection JSON (see "Connection Resource File" in [overview.md](../overview.md)) to get the connector name, connection ID, and `authenticationType`.
3. `uip is connections ping <connection-id>` — confirm the connection itself is active (rules out auth-vs-operation).
4. Branch on `ProviderErrorCode`:
   - **401:** the connection's OAuth token was rejected by the provider — re-authenticate the connection (see [connection-auth-expired.md](./connection-auth-expired.md)). If ping is healthy but the provider still returns 401, the granted scope is wrong. (Note: `DAP-GE-3004` is unrelated — it is a first-party-service token failure, not a connection token; see [token-refresh-failed.md](./token-refresh-failed.md).)
   - **403:** `uip is resources describe <connector-key> <object-name>` — check the operation's required permissions/scopes against what the connection was granted.
   - **404:** verify the record/object ID in the activity input exists in the external service.
   - **429/5xx:** check `RequestId` against the provider's status; if `retry-exception` fired, retries were exhausted.

## Resolution

- **401:** re-authenticate the connection (`uip is connections edit <connection-id>`). If the granted OAuth scope is insufficient, recreate the connection requesting the scope the operation needs.
- **403:** widen the connection's scope or grant the external account the permission the operation requires, then re-authenticate.
- **404:** correct the activity input to reference an existing record/object; guard upstream steps that produce the ID.
- **429:** reduce call frequency, add backoff/batching, or request a higher provider quota. IS already retried twice — application-level pacing is required.
- **5xx:** transient provider outage — retry later. If sustained (`retry-exception`), escalate to the provider; do not treat as a workflow bug.
