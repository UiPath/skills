---
confidence: high
---

# API Workflow Connector Call Fails 401 / 403 / 404 in Cloud

## Context

What this looks like:
- The workflow runs clean locally with `uip api-workflow run` but a Connector/HTTP activity fails once published (or against the real IS proxy)
- Status 401 with `"Invalid Organization or User secret, or invalid Element token provided"`, or 403 `ConnectionNotEnabled`, or 404 `"Connection [<uuid>] is invalid or you do not have access to it"`

What can cause it:
- **Wrong activity kind for the endpoint.** Http kind (`call: "UiPath.Http"`, `endpoint: "/http-request"`) pointed at a vendor connection (Outlook, Gmail, …) — the vendor connector has no `/http-request` operation, so the proxy returns a generic 401. Vendor activities must use IntSvc kind (`call: "UiPath.IntSvc"`, `with.connector` = vendor key, `with.endpoint` = the curated operation).
- **Broken connection state.** The bound connection's OAuth token expired, was never fully authorized, or the running identity lacks access.
- **Stale / orphaned listing.** The filtered `uip is connections list <connectorKey>` returned a UUID whose element instance was deleted upstream; a different UUID actually works.
- **Tenant / folder mismatch.** The CLI login org+tenant (or the deploy folder) differs from where the connection lives.

What to look for:
- The endpoint in the proxy URL vs. the connector on the bound connection — a curated op (`/getNewestEmail`) on the right connector, or a `/http-request` on a vendor connection (the bug)
- Whether the connection pings at all, and in which folder

## Investigation

1. Ping the bound connection: `uip is connections ping <connection-uuid> --output json`. `Code: "ConnectionPing"` = usable; `ConnectionNotEnabled` = broken state.
2. If the filtered listing's UUID doesn't ping, search all: `uip is connections list --all-folders --output json` and ping alternates for the same `ConnectorKey`.
3. Inspect the failing cloud job for the exact proxy URL + status: `uip or jobs get <jobId> --output json`, `uip or jobs logs <jobId> --output json`.
4. Confirm CLI login org+tenant matches the connection's tenant: `uip login status --output json`.

## Resolution

- **If wrong kind:** switch a vendor call from Http kind to IntSvc kind (`call: "UiPath.IntSvc"`, vendor connector key, curated operation endpoint). Http kind is only for the `uipath-uipath-http` HTTP Request activity.
- **If broken connection:** re-authenticate — `uip is connections edit <uuid>` (opens the OAuth browser flow) — or fix in the Studio Web UI, then re-ping.
- **If stale UUID:** rebind the workflow to a UUID that pings (update `connectionId` and, in Solutions mode, the connection resource + bindings).
- **If tenant/folder mismatch:** log in to the same org+tenant, or deploy to the folder where the connection is enabled.
- **Cross-reference:** for the connection's own auth internals, see the **Integration Service** product.
