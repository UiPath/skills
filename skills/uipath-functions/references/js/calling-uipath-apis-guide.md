# Calling UiPath APIs from a Function

Calling UiPath platform APIs from inside a function handler: which token to send, where platform coordinates come from, `@uipath/uipath-typescript` patterns for Orchestrator, and the calls that reach Integration Service connectors.

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

`@uipath/uipath-typescript/integration-service` calls Integration Service from inside a handler with the function's own token. It exports two functions, and both need a connector and a connection to exist first:

| Function | Use when | Sends |
|---|---|---|
| `executeActivity(sdk, connection, objectName, method, options)` | the action exists as an activity of a catalog or custom connector | the activity's inputs; the connector builds the vendor request |
| `executeHttp(sdk, connection, url, method, options)` | everything else, on a version 3 connector | one raw HTTP request; the connection adds the authentication |

### Pick the route

Run the Integration Service discovery workflow of the `uipath-platform` skill first (connector → connection → ping → describe), then pick by what the function needs:

| The function needs | Route | Call |
|---|---|---|
| A straightforward API with no vendor auth flow | HTTP request, manual authentication, on the `uipath-uipath-http` connector | `executeHttp` |
| A vendor action no catalog or custom connector covers | HTTP request, authentication from an `uipath-uipath-http` connection | `executeHttp` |
| An action of a vendor a catalog or custom connector covers | that connector's activity; an HTTP request on its connection when the action has no activity | `executeActivity`, else `executeHttp` |
| One or many actions of an uncovered vendor whose auth is complex | build a custom connector with `uip is connectors builder` (`uipath-connector-builder` skill), publish it, create a connection | `executeActivity` |

### Set up the SDK

Construct the SDK inside the handler, once per invocation, from `ctx`. On a deployed run it reads `ctx.platform` and `ctx.robot.accessToken`; on a local run, where both are null, it reads `UIPATH_BASE_URL`, `UIPATH_ORG_NAME`, `UIPATH_TENANT_NAME` and `UIPATH_ACCESS_TOKEN`.

```typescript
import { defineFunction, defineSchema, FunctionError, type JobContext } from "@uipath/coded-functions-js-sdk";
import { UiPath } from "@uipath/uipath-typescript/core";
import { executeActivity, executeHttp } from "@uipath/uipath-typescript/integration-service";

const sdk = new UiPath(ctx);
```

Take the connection id as a function input (`connectionId: string`). It is deployment configuration: each environment has its own connection.

### executeActivity

`objectName` and `method` come from the activity's `describe` output (`operation.path` without the leading slash, `operation.method`). Query parameters go in `queryParams`, request fields in `body`.

```typescript
// Version 3 connector: the object name is the connector resource
const spoken = await executeActivity(sdk, input.connectionId, "text_to_speech", "POST", {
  queryParams: { voice_id: input.voiceId },
  body: { text: input.text },
  timeoutMs: 60_000,
});
```

A connector activity of version `4.0.0` runs on the version 4 engine. Pass the connector's version and key; `objectName` is then the activity's `scriptRef`. A `resource.connection()` handle supplies the key, so pass `connectorKey` only with a plain connection id:

```typescript
// Version 4 connector: the object name is the activity's scriptRef
const sent = await executeActivity(sdk, input.connectionId, "SendMessageToChannel", "POST", {
  connectorVersion: "4.0.0",
  connectorKey: "uipath-salesforce-slack",
  queryParams: { send_as: "bot" },
  body: { channel: input.channel, messageToSend: input.message },
  timeoutMs: 15_000,
});
```

Each engine takes its own options, and `executeActivity` throws a `ValidationError` for one passed to the other engine:

| Engine | Options it takes |
|---|---|
| Version 3 (no `connectorVersion`, or below 4) | `files`, `bodyPartName`, `urlInputFields`, `fileResponse`, `maxRecords` |
| Version 4 (`connectorVersion` 4 or later) | `scriptRef`, `headers` |

### executeHttp

`executeHttp` sends the request through the version 3 engine. `url` is a path relative to the connection's base URL, and an object `body` reaches the vendor as JSON.

```typescript
const channel = await executeHttp(sdk, input.connectionId, "/conversations.info", "GET", {
  queryParams: { channel: input.channel },
  timeoutMs: 8_000,
});
```

### Read the result

Both functions return `{ ok, status, statusText, headers, body }` and resolve on a non-2xx status. Check `ok` and throw a `FunctionError` that carries the vendor's answer:

```typescript
if (!sent.ok) {
  throw new FunctionError(`Slack did not accept the message (status ${sent.status})`, {
    errorCode: "SLACK_SEND_FAILED",
    details: sent.body,
  });
}
```

1. `executeHttp` adds `isVendorError`: `true` when the vendor answered with an error status, `false` when Integration Service itself refused the call.
2. Retrying is off unless `retry: { maxRetries }` is set, and a `POST` is retried only when listed in `retry.retryMethods`.
3. `executeActivity` on a version 3 connector returns a file or binary response as a `Uint8Array` in `body`; `fileResponse: true` forces it.
4. With `maxRecords`, `executeActivity` follows the connector's pages on a version 3 `GET`; without it the result carries `page` when more records exist.

### Dependency

`executeActivity`, `executeHttp` and the `/integration-service` import path are part of `@uipath/uipath-typescript`. Add it to the function project's `dependencies` beside `@uipath/coded-functions-js-sdk`, and add `"skipLibCheck": true` to the project's `tsconfig.json`.

## Timeout Budget

Every external call gets an `AbortSignal.timeout(...)` sized to the caller's budget — a browser-invoked function must finish under ~20 s total, so per-call timeouts of ~8 s leave room for retries and the response ([http-semantics-guide](http-semantics-guide.md)). A `403` on the function's own trigger (before the handler runs) usually means the caller's PKCE scope is missing `OR.Default` ([coded-app-wiring-guide](coded-app-wiring-guide.md)).
