---
confidence: high
---

# Connection Service — Internal / Dependency Failure (CNS2003, CNS2005, CNS2006, CNS2007, CNS2009, CNS2010, CNS2012, CNS1042, CNS1101)

> **Fault bucket: 🛠 B — service-side (not customer-fixable → retry, then escalate).** Every code on this page means Connection Service itself, or a dependency it calls (SQL, Orchestrator, Identity, the message bus, or the connector-provider layer), failed — **not** the customer's connection, credentials, or input. Lead with: "This is a service-side issue inside the platform — retry; if it persists, contact the owner team (Integration Service) with the `traceId`." The only split to make is **B1 vs B2**: `CNS1042`/`CNS1101` are the *third-party provider* failing (B2 — wait/retry), everything else is a *UiPath-internal* dependency (B1 — escalate if sustained). See [cns-error-codes-reference.md](../cns-error-codes-reference.md#fault-ownership).

## Context

What this looks like:
- HTTP `5xx` (or `502`/`424` for the provider codes) from a Connection Service API call — creating/listing/pinging connections, managing triggers, or a connector activity resolving its connection at runtime
- Error body shape: `{ "code": "CNS2007", "message": "Integration Service is currently unavailable. Please try again later.", "traceId": "…" }`
- In App Insights (owner team): traces matching `Connection Service error reported: [StatusCode: …, ErrorCode: "CNS2xxx", …]`

Code → failing dependency:

| Code | Name | What failed | HTTP |
|------|------|-------------|:---:|
| `CNS2003` | DatabaseConnectionFailed | SQL database open/query (transient by definition) | 500 |
| `CNS2005` | OrchestratorCallFailed | A Connection Service → **Orchestrator** API call (trigger CRUD, queue-definition / process lookups) returned an error | mirrors Orchestrator's status |
| `CNS2006` | UnknownInternalError | Catch-all: an unhandled exception reached the global middleware | 500 |
| `CNS2007` | ServiceUnavailableError | A downstream UiPath dependency answered **503** | 503 |
| `CNS2009` | TokenRequestFailed | S2S token request to **Identity** failed (`invalid_client` or Identity outage) | mirrors Identity's status |
| `CNS2010` | RequestTimeout | An outbound HTTP call (Orchestrator / provider layer / Identity) hit the client-side timeout | 500 |
| `CNS2012` | MessageBusDispatchFailed | Dispatcher could not publish a trigger-fired event to the **message bus** | 503 |
| `CNS1042` | CeExternalProviderError | The **third-party provider** behind the connector returned a 5xx ("Error from provider: …") | 502 |
| `CNS1101` | VendorError | Provider-layer vendor error — the third-party service rejected or rate-limited the request (dependency failures surface as 424 FailedDependency; a vendor 429 also lands here) | 424 / 429 |
| `CNS2001` | CEAccountCreationFailed | Provisioning the connector-platform shadow account for a UiPath identity failed | 503 |
| `CNS2008` | DeleteCeUserFailed | Deleting the connector-platform user during account/tenant cleanup failed | 503 |
| `CNS1036` | CEDeleteInstanceFailed | Deleting the connector-platform instance during connection delete failed | mirrors dependency status |

What can cause it:
- Transient dependency blips — SQL failovers, Orchestrator deploys, Identity token-endpoint hiccups, message-bus congestion. Most of these self-heal.
- A genuine dependency incident (sustained `CNS2005`/`CNS2007` clusters across tenants).
- For `CNS1042`/`CNS1101` — the third-party service (Salesforce, O365, …) itself is down or erroring; UiPath is only relaying it.
- `CNS2010` with no other signal usually means one slow dependency call, not an outage.

What to look for:
- **Is it one request or a cluster?** A single occurrence that succeeds on retry is a transient blip. A sustained cluster (same code, many tenants, > ~15 min) is an incident.
- **The `traceId` from the error body** — it is the correlation key the owner team needs; always capture it.
- For `CNS1042`: the provider name in the message — check that provider's status page before escalating to UiPath.

## Investigation

1. **Do NOT chase the connection.** None of these codes indicate a credential, permission, or configuration problem. Re-authenticating the connection, editing it, or recreating it will not help — skip those steps.
2. **Retry once.** All codes on this page except `CNS1101`-on-4xx are transient-classified (5xx/408/429 and the Db/Identity/MessageBus dependency family are auto-retried by background flows; interactive calls are not). A clean retry closes the case.
3. **Classify B1 vs B2:**
   - `CNS1042` / `CNS1101` → **B2** — read the provider name from the message and check the third-party service's status/health page. If the provider is degraded, wait it out.
   - Everything else → **B1** — a UiPath-internal dependency. Check the UiPath status page / trust portal for a known incident in the tenant's region.
4. **Establish blast radius (owner team):** in the Connection Service App Insights for the region, `union traces, exceptions | where customDimensions.ErrorCode == "CNS2xxx" | summarize count() by bin(timestamp, 15m)` — a flat low baseline is normal background noise; a step change marks an incident window. `CNS2005` also carries the Orchestrator status code in the message — 401/403 clusters point at S2S token/permission drift rather than an Orchestrator outage.
5. **For `CNS2012` specifically** — trigger events are queued and retried by the dispatcher; a brief message-bus blip usually means delayed (not lost) trigger firings. Sustained failures = escalate; the events may be dropped after retry exhaustion.

## Resolution

- **Transient (single occurrence, retry succeeds):** no action. Note the `traceId` in case it recurs.
- **`CNS1042` / `CNS1101` with a degraded provider:** wait for the third-party service to recover; nothing to fix on the UiPath side. If the provider is healthy and the code persists, escalate to Integration Service — the connector's provider integration may be broken.
- **Sustained B1 (any other code):** escalate to the Integration Service owner team with: the CNS code, the `traceId`(s), tenant/org IDs, timestamps, and the affected operation (e.g. "trigger create", "connection ping"). These are platform faults; the customer cannot resolve them from their side.
- **Never** advise the customer to delete/recreate connections or triggers for these codes — it does not address the dependency fault and can lose configuration.
