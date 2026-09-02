# Calling UiPath APIs from a Function

Calling UiPath platform APIs from inside a function handler: which token to send, where platform coordinates come from, `@uipath/uipath-typescript` patterns for Orchestrator, and the working route to Integration Service connectors.

## Token Decision

[SKILL.md](../../SKILL.md) JS Rule 8 names the two identities; the decision rule:

| Token | Identity | Use for |
|---|---|---|
| `ctx.user.accessToken` | The caller — delegated OAuth token from the request's `Authorization` header; the caller's folder permissions apply | Default: anything done on the caller's behalf |
| `ctx.robot.accessToken` | The function's own serverless-robot identity — platform-issued RS256 robot JWT, ~24h TTL | Privileged/S2S reads the caller must not be able to do |

Under local serve `ctx.robot` is always null ([local-dev-guide.md](local-dev-guide.md)); `ctx.user` is null only when the request carries no decodable Bearer JWT — serve decodes the `Authorization` header locally too. Privileged paths fall back robot-first to the env token:

```typescript
const token = ctx.robot?.accessToken || process.env["UIPATH_ACCESS_TOKEN"] || "";
if (!token) throw new FunctionError("Robot token unavailable — local dev: set UIPATH_ACCESS_TOKEN", 500);
```

Delegated paths must require the caller token — never fall through to the robot identity, that silently escalates privileges:

```typescript
if (!ctx.user?.accessToken) throw new FunctionError("User access token not available", 401);
```

`ctx.robot.key` is the serverless robot's key — required by Orchestrator's per-robot endpoints, notably `GetRobotAssetByNameForRobotKey`.

## Platform Coordinates

Read `baseUrl`/`orgId`/`tenantId`/`folderKey` from `ctx.platform`, never from input — caller-forwarded `_baseUrl`/`_orgId`/`_tenantId` fields are deprecated because caller-controlled values redirect the function's platform calls. Env vars (`UIPATH_BASE_URL`/`UIPATH_ORG_ID`/`UIPATH_TENANT_ID`) are the local-only fallback that populates `ctx.platform` under serve ([local-dev-guide](local-dev-guide.md)).

```typescript
if (!ctx.platform) throw new FunctionError("Platform context unavailable — local dev: set UIPATH_BASE_URL/UIPATH_ORG_ID/UIPATH_TENANT_ID", 500);
const { baseUrl, orgId, tenantId } = ctx.platform;
```

## Using @uipath/uipath-typescript

Constructor maps ctx fields by these exact names; `initialize()` is a no-op in secret mode but call it anyway:

```typescript
import { UiPath } from "@uipath/uipath-typescript/core";
import { Assets } from "@uipath/uipath-typescript/assets";

const sdk = new UiPath({ baseUrl, orgName: orgId, tenantName: tenantId, secret: token });
await sdk.initialize();
```

- The package goes in `dependencies` (public npm) — the SDK-placement and lockfile rules in [deployment-guide](deployment-guide.md) apply to it like any runtime dep.
- The SDK auto-probes runtime-published resource overwrites — solution-managed resource names redirect transparently, no code needed ([bindings-guide](bindings-guide.md)).

### Reading assets

```typescript
const escaped = input.assetName.replace(/'/g, "''");
const res = await new Assets(sdk).getAll({ filter: `Name eq '${escaped}'`, folderId: input.folderId });
return { value: res.items[0]?.value ?? null };
```

1. **`folderId` is required.** Without it `getAll` calls `GetAssetsAcrossFolders` (metadata only) and silently returns `null` for every value field.
2. **OData string/GUID literals take single quotes**, embedded quotes escaped as `''`. An unquoted GUID → `400 Bad Request`, often surfacing as an empty list.
3. **Secret-typed asset values are released only by `GetRobotAssetByNameForRobotKey`** (per-robot endpoint, takes `ctx.robot.key`) — `getAll` never returns them.
4. `AllowDirectApiAccess` is irrelevant for OData endpoints — do not add it to the Orchestrator setup.

### Secret Vault pattern (privileged read)

For credentials/API keys the caller must never see: create a dedicated folder (e.g. `Restricted-Secrets`), grant the function's runtime service account (Orchestrator → Robots/Machines) **Assets.View** on that folder only, give callers zero access to it, and read with `ctx.robot.accessToken`. Non-sensitive assets: delegated token; the caller needs Assets.View on the folder. Folder RBAC, not the function layer, is the effective security boundary — rationale → [coded-app-wiring-guide.md](coded-app-wiring-guide.md).

### Starting jobs

```typescript
import { Processes } from "@uipath/uipath-typescript/processes";

const results = await new Processes(sdk).start(
  { processKey: releaseKey, inputArguments: JSON.stringify(args), strategy: "ModernJobsCount", jobsCount: 1 },
  folderId,   // numeric folder ID — sets X-UIPATH-OrganizationUnitId
);
return { jobId: results?.[0]?.id ?? null };
```

`processKey` takes the ReleaseKey UUID from `/odata/Releases`. When later listing jobs that may span folders (`GET /odata/Jobs`), omit `X-UIPATH-OrganizationUnitId` — without the header Orchestrator searches all accessible folders.

## Integration Service Connectors

Known sharp edge: no published SDK reaches Integration Service from inside a function. `@uipath/integrationservice-sdk` authenticates only from a `uip login` session (it cannot consume a ctx token) and `@uipath/uipath-typescript` has no Integration Service surface. The currently-working approach is the connector HTTP passthrough, called with a ctx token (same token decision as above; verified with the caller's delegated token):

```typescript
const res = await fetch(`${baseUrl}/${orgId}/${tenantId}/elements_/v3/element/instances/<CONNECTION_ID>/http-request`, {
  method: "POST",
  headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
  body: JSON.stringify({
    authentication: "connector",
    targetConnector: "<CONNECTOR_KEY>",   // e.g. "uipath-salesforce-slack"
    method: "GET",
    path: "/api/endpoint",
    url: "/api/endpoint",
    query: { param: "value" },
  }),
  signal: AbortSignal.timeout(8_000),
});
const envelope = await res.json();
const downstream = Number(envelope.code ?? envelope.statusCode ?? res.status);
if (downstream >= 400) throw new FunctionError(`Connector call failed (${downstream})`, downstream);
```

1. **Never trust the 200 wrapper.** The passthrough can answer `200` while the downstream call failed — read the downstream status from the response envelope (`code`/`statusCode`) and surface 4xx/5xx as `FunctionError` carrying that status.
2. `<CONNECTION_ID>` is the Integration Service connection instance id; `<CONNECTOR_KEY>` is the connector key. Both are deployment configuration — resolve them per environment, do not hardcode tenant-specific ids in shared code.

## Timeout Budget

Every external call gets an `AbortSignal.timeout(...)` sized to the caller's budget — a browser-invoked function must finish under ~20 s total, so per-call timeouts of ~8 s leave room for retries and the response ([http-semantics-guide](http-semantics-guide.md)). A `403` on the function's own trigger (before the handler runs) usually means the caller's PKCE scope is missing `OR.Default` ([coded-app-wiring-guide](coded-app-wiring-guide.md)).
