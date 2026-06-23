# element.json Reference

The core connector definition at `app/element/element.json`. Udon reads it to know how
to authenticate, call vendor APIs, map parameters, and apply hooks.

**How it's edited.** Use the orchestrator verbs — `init` (creates the shell; seeds the
connector-level fields and `base.url`), `auth set` (the whole authentication block +
config keys), `activity create` (`resources[]` + the SR), `auth system create` (system
`resources[]` entries). Edit a long-tail field no verb exposes (`displayOrder`,
`extended`, `typeOauth`, `cloneable`, a single param) surgically with `state patch`. The
command map and workflows live in SKILL.md — don't re-derive them here.

## Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `key` | string | Element key. For a design connector: `design-{org}-{slug}` (derived by `init` from `--name` + `--organization`). |
| `name` / `description` | string | Catalog display values (`init --name` / `--description`). |
| `hub` | string | Legacy/obsolete. Paths work with or without the hub prefix. Don't set on new connectors. |
| `authentication` | object | `{ "type": "oauth2" }` — primary auth type. Multi-auth uses an `authentication.type` COMBO config with groupControl. Owned by `auth set`. |
| `typeOauth` | boolean | `true` if primary auth is any OAuth/JWT variant. Set by `auth set`. |
| `configuration` | array | Config entries (auth creds, base URL, pagination, events). See [configuration.md](configuration.md). |
| `resources` | array | One entry per HTTP method per endpoint. |
| `parameters` | array | Global parameters (headers, auth mappings). Same schema as resource parameters. Add a header with `init --header VendorName=value`; remove with `init header delete <VendorName>`. |
| `hooks` | array | Global hooks applied to ALL requests (`activity hook create --global`). See [hooks.md](hooks.md). |
| `paginatorVersion` | int/string | Paginator engine: `2` standard, `"V3"` newer. |
| `publishStatus` | string | `"draft"` or `"published"`. |
| `protocolType` | string | Almost always `"http"`. |
| `cloneable` / `extended` / `transformationsEnabled` | boolean | Usually true / false / true. |
| `elementMetadata` | object | Embedded object INSIDE element.json (`key`, `name`, `authenticationTypes[]`, `discovery`, `api`, `bulk`, `pollingResources`) — distinct from the separate `element-metadata.json` file, which holds catalog flags (`hasEvents`, `hasHttpRequest`, categories, and `latestVersion` — `init` seeds it to `"1.0.0"`). |

## resources[]

Each entry = ONE HTTP method for ONE endpoint. An "accounts" resource created with
GET/GETBYID/POST/PATCH/DELETE has 5 entries (one `activity create` call writes them all).

| Field | Required | Description |
|-------|----------|-------------|
| `method` | yes | Udon method: GET, GETBYID, POST, PATCH, PUT, DELETE. |
| `path` | yes | Udon path / IS slug (e.g. `/accounts`). Hub prefix is legacy/optional. |
| `vendorPath` | yes | Vendor API path. May differ from `path` (`--vendor-path`, per-method `--method-vendor-path`). |
| `vendorMethod` | yes | Vendor HTTP method (usually same as `method`). |
| `type` | yes | Resource type — see below (`--resource-type`). |
| `standardResourceName` | no | Canonical link to the SR file. Absent on system resources. |
| `rootKey` | no | JSON path to the list array (`--root-key`, e.g. `"value"`, `"data.items"`). |
| `nextPageKey` | no | Non-standard next-page token location (`--next-page-key`). |
| query-param vendor names | no | On a LIST GET, the CEQL filter + pagination query params default to vendor names `where`/`pageSize`. Override to the vendor's real names with `--filter-param` (e.g. `sysparm_query`), `--page-size-param` (e.g. `sysparm_limit`, `per_page`), and `--offset-param` (e.g. `sysparm_offset`, `page`) — the offset param is ADDED only when named. These set `vendorName` while the activity-input `name` stays canonical, and never apply to by-id reads. |
| `parameters` | no | Per-resource parameter mappings (`activity param create`; see below). |
| `hooks` | no | Hook refs for this resource+method (`activity hook create`). |
| `expressions` | no | `requestBodyRoot` / `responseBodyRoot` for JSON-path wrap/unwrap. |

For by-id methods (`GETBYID`/`PATCH`/`PUT`/`DELETE`) `activity create` auto-adds the
`/{primaryKey}` path param — ALWAYS for `GETBYID`, and for the write methods only on a CRUD
activity (one that also has `GET`/`GETBYID`); a write-only activity keeps its base path.
Details in [standard-resources.md](standard-resources.md) §"by-id methods".

### Resource types
`api` (discoverable, in CRUD dropdowns), `apiNoDocumentation` (hidden but callable),
`apiElementRequest` (routes back through Udon; still appears in CRUD unless `isHidden`),
plus the 13 **system types** (no SR file) created via `auth system create`:
`onProvision`, `onDelete`, `onRefresh`, `provisionAuthValidation`, `oauthOnAuthroizeUrl`
(historical typo — keep it), `oauthOnTokenExchange`, `oauthOnTokenRefresh`,
`oauthOnTokenRevoke`, `oauth1OnTokenRequest`, `oauth2ClientCredentials`,
`onProvisionWebhook`, `onDeleteWebhook`, `onProvisionCacheVendorDataAsync`.
[system-resources.md](system-resources.md) is the authoritative list with override paths.

## parameters[] (global and per-resource)

Same schema at both levels. element.json is the **source of truth** for contract fields
(`name`, `vendorName`, `type`, `vendorType`, `dataType`, `vendorDataType`, `required`,
`description`, `source`); linked SR params auto-reconcile on every write. SR-only UI
fields (`displayName`, `requestCurated`, `sortOrder`, `design`) are preserved. Add with
`activity param create --resource <name> --method <VERB> --name <p> --type <type>` (`--type`
e.g. `path`/`query`/`header`/`body` — the full accepted enum is listed below).

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Udon-side name. For `type:"value"`, this IS the literal value. |
| `vendorName` | yes | Vendor-side name. |
| `type` | yes | WHERE the value comes from (source). |
| `vendorType` | yes | WHERE it goes in the vendor request (destination). |
| `dataType` / `source` / `required` / `design` | no | Hints, request/response, requiredness, UI. |

`type`/`vendorType` values: `configuration`, `header`, `path`, `query`, `file`, `form`,
`multipart`, `value`, `customValue`, `body`, `bodyField`, `prevBody`, `prevBodyField`,
`bodyToken`, `no-op`.

Common patterns:
```json
{"name": "application/json", "vendorName": "Accept", "type": "value", "vendorType": "header"}
{"name": "id", "vendorName": "customerId", "type": "path", "vendorType": "path"}
{"name": "oauth.user.token", "vendorName": "Authorization", "type": "configuration", "vendorType": "header"}
{"name": "pageSize", "vendorName": "limit", "type": "query", "vendorType": "query"}
```

### Static / constant query parameters — use `type:"value"`, NOT a query string

A **constant** query param the connector must always send (an API version, a fixed
`format=json`, a feature flag) MUST be modelled as a `value` param whose `name` holds the
literal value and whose `vendorType` is `query`:
```json
{"name": "2023-07-31", "vendorName": "api-version", "type": "value", "vendorType": "query"}
```
This sends `?api-version=2023-07-31` exactly as written and never prompts the connection
user. **Do NOT leave the constant in the vendor path as a query string** (e.g.
`vendorPath: "/info?api-version=2023-07-31"`): on import the server parses that `?k=v`
into a `type:"query"` param that is *required user input with no value*, so every runtime
call (and `provisionAuthValidation` / connection test) fails with "value for 'api-version'
not passed". This applies everywhere a vendor path is set — activity resources AND the
auth-validation path (`auth set --validation-vendor-path`). The CLI `activity`/`auth`
verbs now auto-extract a trailing `?k=v` into a `value` param for you, so prefer passing a
clean base path; if you ever hand-edit `element.json`, follow the rule yourself. A `value`
param is stored in **plaintext** — only for non-secret constants; a secret belongs in an
encrypted `configuration` entry referenced via `type:"configuration"`, never a literal.

### Value interpolation (`${...}`)
For `type:"value"` params, Udon substitutes `${<namespace>.<key>}` in the `name` field at
request time. Namespaces: `configuration`, `header`, `body`. Special tokens (no prefix):
`${webhookCallbackUrl}`, `${elementWebhookCallbackUrl}`, `${encodedId}`, `${date}`,
`${date:FORMAT}` / `${gmtDate:FORMAT}` / `${dateTimeZone:TZ:FORMAT}` (event-poller only — see [events.md](events.md)).
This is how a prefix like `Bearer <token>` is applied without a hook:
```json
{"name": "Bearer ${configuration.oauth.user.token}", "vendorName": "Authorization", "type": "value", "vendorType": "header"}
```
Unresolved tokens are left verbatim (silent failure) — validate spellings against
`configuration[]`. No escape for a literal `{`. Prefer `type:"configuration"` for a 1:1
map; use `type:"value"` + interpolation when you need a prefix/suffix/composition.

## Editing surgically with `state patch`
The no-merge round-trip rule (query → edit → patch the COMPLETE object back) is SKILL.md
Rule 5. element.json-specific pointer detail: resource pointers URL-encode the path
(`/contacts` → `%2Fcontacts`, e.g. `element.json/resources/GET/%2Fcontacts`);
`element-metadata.json` has no addressable sub-paths (round-trip the whole file); `--op remove`
deletes one addressed item (e.g. a parameter by index); `state query --help` prints the grammar.

## Hook execution order
Global hooks wrap resource hooks around the vendor call. Canonical order, context vars,
naming, and the token-derived base-URL pattern: [hooks.md](hooks.md).

## Expressions
`requestBodyRoot` wraps the body (`"contact"` → `{"contact": ...}`); `responseBodyRoot`
unwraps the response (`"data.items"`). Both are real element.json fields but have NO builder
flag — author them by `state patch` of the whole resource entry (`"expressions": {...}`), then
`validate`. For a plain list unwrap prefer `rootKey` (`--root-key`), which the CLI does expose.

## See also
- [configuration.md](configuration.md), [standard-resources.md](standard-resources.md),
  [hooks.md](hooks.md), [system-resources.md](system-resources.md), [auth.md](auth.md)
