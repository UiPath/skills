# element.json Reference

The core connector definition at `app/element/element.json`. Udon reads it to know how
to authenticate, call vendor APIs, map parameters, and apply hooks. `scaffold` creates
it; `auth`, `config`, `resource`, `global`, `hook` commands mutate it.

## Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `key` | string | Element key. Must match repo name minus `periodic-` prefix. |
| `name` / `description` | string | Catalog display values. |
| `hub` | string | Legacy/obsolete. Paths work with or without the hub prefix. Don't set on new connectors. |
| `authentication` | object | `{ "type": "oauth2" }` — primary auth type. Multi-auth uses an `authentication.type` COMBO config with groupControl. |
| `typeOauth` | boolean | `true` if primary auth is any OAuth/JWT variant. |
| `configuration` | array | Config entries (auth creds, base URL, pagination, events). See [configuration.md](configuration.md). |
| `resources` | array | One entry per HTTP method per endpoint. |
| `parameters` | array | Global parameters (headers, auth mappings). Same schema as resource parameters. |
| `hooks` | array | Global hooks applied to ALL requests. See [hooks.md](hooks.md). |
| `paginatorVersion` | int/string | Paginator engine: `2` standard, `"V3"` newer. |
| `publishStatus` | string | `"draft"` or `"published"`. |
| `protocolType` | string | Almost always `"http"`. |
| `cloneable` / `extended` / `transformationsEnabled` | boolean | Usually true / false / true. |
| `elementMetadata` | object | Embedded object INSIDE element.json (`key`, `name`, `authenticationTypes[]`, `discovery`, `api`, `bulk`) — distinct from the separate `element-metadata.json` file, which holds catalog flags (`hasEvents`, `hasHttpRequest`, categories). |

## resources[]

Each entry = ONE HTTP method for ONE endpoint. An "accounts" resource with
GET/GETBYID/POST/PATCH/DELETE has 5 entries.

| Field | Required | Description |
|-------|----------|-------------|
| `method` | yes | Udon method: GET, GETBYID, POST, PATCH, PUT, DELETE. |
| `path` | yes | Udon path (e.g. `/accounts`). Hub prefix is legacy/optional. |
| `vendorPath` | yes | Vendor API path. May differ from `path`. |
| `vendorMethod` | yes | Vendor HTTP method (usually same as `method`). |
| `type` | yes | Resource type — see below. |
| `standardResourceName` | no | Canonical link to the SR file. Absent on system resources. |
| `rootKey` | no | JSON path to the list array (e.g. `"value"`, `"data.items"`). |
| `nextPageKey` | no | Non-standard next-page token location. |
| `parameters` | no | Per-resource parameter mappings (see below). |
| `hooks` | no | Hook refs for this resource+method. |
| `expressions` | no | `requestBodyRoot` / `responseBodyRoot` for JSON-path wrap/unwrap. |

### Resource types
`api` (discoverable, in CRUD dropdowns), `apiNoDocumentation` (hidden but callable),
`apiElementRequest` (routes back through Udon; still appears in CRUD unless `isHidden`),
plus the **system types** (no SR file): `onProvision`, `onDelete`, `onRefresh`,
`oauthOnTokenRefresh`, `oauthOnTokenExchange`, `oauthOnTokenRevoke`,
`oauthOnAuthroizeUrl` (historical typo — keep it), `provisionAuthValidation`,
`onProvisionWebhook`, `onDeleteWebhook`.
[system-resources.md](system-resources.md) is the authoritative list with override paths.

## parameters[] (global and per-resource)

Same schema at both levels. element.json is the **source of truth** for contract fields
(`name`, `vendorName`, `type`, `vendorType`, `dataType`, `vendorDataType`, `required`,
`description`, `source`); linked SR params auto-reconcile on every write. SR-only UI
fields (`displayName`, `requestCurated`, `sortOrder`, `design`) are preserved.

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Udon-side name. For `type:"value"`, this IS the literal value. |
| `vendorName` | yes | Vendor-side name. |
| `type` | yes | WHERE the value comes from (source). |
| `vendorType` | yes | WHERE it goes in the vendor request (destination). |
| `dataType` / `source` / `required` / `design` | no | Hints, request/response, requiredness, UI. |

`type`/`vendorType` values: `configuration`, `header`, `path`, `query`, `form`,
`body`, `bodyField`, `value`, `prevBody`, `prevBodyField`, `multipart`, `bodyToken`,
`customValue`, `no-op`.

Common patterns:
```json
{"name": "application/json", "vendorName": "Accept", "type": "value", "vendorType": "header"}
{"name": "id", "vendorName": "customerId", "type": "path", "vendorType": "path"}
{"name": "oauth.user.token", "vendorName": "Authorization", "type": "configuration", "vendorType": "header"}
{"name": "pageSize", "vendorName": "limit", "type": "query", "vendorType": "query"}
```

### Value interpolation (`${...}`)
For `type:"value"` params, Udon substitutes `${<namespace>.<key>}` in the `name` field
at request time. Namespaces: `configuration`, `header`, `body`. Special tokens
(no prefix): `${webhookCallbackUrl}`, `${elementWebhookCallbackUrl}`, `${encodedId}`,
`${date}`, `${date:FORMAT}` / `${gmtDate:FORMAT}` (event-poller only — see [events.md](events.md)).
This is how prefixes like
`Bearer <token>` are applied without a hook:
```json
{"name": "Bearer ${configuration.oauth.user.token}", "vendorName": "Authorization", "type": "value", "vendorType": "header"}
```
Unresolved tokens are left verbatim (silent failure) — validate spellings against
`configuration[]`. No escape for a literal `{`. Prefer `type:"configuration"` for a 1:1
map; use `type:"value"` + interpolation when you need a prefix/suffix/composition.

## Hook execution order
Global hooks wrap resource hooks around the vendor call. Canonical order, context vars,
naming, and patterns: [hooks.md](hooks.md).

## Expressions
`requestBodyRoot` wraps the body (`"contact"` → `{"contact": ...}`); `responseBodyRoot`
unwraps the response (`"data.items"`).

## See also
- [configuration.md](configuration.md), [standard-resources.md](standard-resources.md),
  [hooks.md](hooks.md), [system-resources.md](system-resources.md), [auth.md](auth.md)
