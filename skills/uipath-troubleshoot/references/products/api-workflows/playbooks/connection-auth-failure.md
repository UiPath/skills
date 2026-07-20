---
confidence: medium
---

# API Workflow Connector Call Fails 401/403 in Cloud

## Context

What this looks like:
- The workflow runs clean locally with `uip api-workflow run` but a Connector/HTTP activity fails once published (or against the real IS proxy)
- The Integration Service proxy returns an auth-shaped **4xx**, surfaced in the failing activity's result. (The executor normalizes any 4xx from the proxy to a 400 client-error status on its own error envelope, so triage on the **status code in the result payload**, not the envelope status.)
- A connection binding that is missing entirely fails earlier, locally, as a 400 validation error (`CONNECTION_REQUIRED`) before any proxy call — not a cloud auth failure

The status code in the result payload discriminates the cause family:

| Code | Signature | Cause family |
|------|-----------|--------------|
| **401** | `Invalid Organization or User secret, or invalid Element token provided` | The request never reaches a usable element: wrong activity kind, stale/orphaned connection UUID, tenant/folder mismatch |
| **403** | `Forbidden` | The bound connection exists but is unusable or under-authorized: disabled/expired, or missing OAuth scopes for the operation |

What can cause it:
- **Wrong activity kind for the endpoint (401).** Http kind (`call: "UiPath.Http"`, `endpoint: "/http-request"`) with `with.connector` set to a vendor key (Outlook, Gmail, …) — the vendor connector has no `/http-request` operation, so the proxy returns a generic 401. Vendor operations must use IntSvc kind (`call: "UiPath.IntSvc"`, `with.connector` = vendor key, `with.endpoint` = the curated operation). Do not confuse with the legitimate connector-based-authentication shape: an HTTP Request whose `with.connector` stays `uipath-uipath-http` may carry a vendor connection UUID in `connectionId` when `bodyParameters` has `authentication: "connector"` + `targetConnector` — that is valid, not this bug.
- **Stale / orphaned listing (401).** The filtered `uip is connections list <connectorKey>` returned a UUID whose element instance was deleted upstream; a different UUID actually works.
- **Tenant / folder mismatch (401).** The CLI login org+tenant (or the deploy folder) differs from where the connection lives.
- **Broken connection state (403).** The bound connection is disabled or expired — repeated OAuth token-refresh failures (IS auto-disables the connection), credentials rotated on the external system, or an admin disabled it. The connection fails its ping.
- **Missing scopes (403).** The connection is Enabled and pings clean, but was authorized without the OAuth scopes this operation needs.

What to look for:
- The status code in the failing activity's result payload — 401 routes to kind/UUID/tenant, 403 to connection state/scopes
- The endpoint in the proxy URL vs. the connector on the bound connection — a curated op (`/getNewestEmail`) on the right connector, or a `/http-request` on a vendor connection (the bug)
- Whether the connection pings at all, and in which folder. The ping verdict is a CLI diagnostic surface — its strings (`not enabled (status: <Status>)`) do not appear in the runtime error

## Investigation

1. Read the status code and exact proxy URL from the failing activity's result payload: `uip or jobs get <job-key> --output json`, `uip or jobs logs <job-key> --output json`.
2. Ping the bound connection — decisive for connection state regardless of status code: `uip is connections ping <connection-uuid> --output json`. `Code: "ConnectionPing"` = usable; `Result: "Failure"` with `not enabled (status: <Status>)` = broken state.
3. **401 + clean ping:** compare the proxy URL's endpoint against the connector on the bound connection (the wrong-kind check), then confirm CLI login org+tenant matches the connection's tenant: `uip login status --output json`.
4. **401 + failed ping:** the listing's UUID may be orphaned — search all: `uip is connections list --all-folders --output json` and ping alternates for the same `ConnectorKey`.
5. **403 + failed ping:** broken/disabled connection. **403 + clean ping:** missing scopes for this operation.

## Resolution

- **If wrong kind (401):** switch a vendor call from Http kind to IntSvc kind (`call: "UiPath.IntSvc"`, vendor connector key, curated operation endpoint). Http kind is only for the `uipath-uipath-http` HTTP Request activity.
- **If stale UUID (401):** rebind the workflow to a UUID that pings (update `connectionId` and, in Solutions mode, the connection resource + bindings).
- **If tenant/folder mismatch (401):** log in to the same org+tenant, or deploy to the folder where the connection is enabled.
- **If broken connection (403):** re-authenticate — `uip is connections edit <uuid>` (opens the OAuth browser flow) — or fix in the Studio Web UI, then re-ping.
- **If missing scopes (403):** re-authorize the connection with the scopes the operation requires (grant them on the external system first if needed): `uip is connections edit <uuid>`, then re-run.
- **Cross-reference:** for the connection's own auth internals (disabled states, scope grants, lockout), see the **Integration Service** product.
