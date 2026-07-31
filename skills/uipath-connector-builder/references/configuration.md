# Configuration Reference

Config entries live in `element.json → configuration[]`. Authentication, pagination,
and events are ALL config keys — their values are filled per-connection at creation time.

## How configuration gets set (no `config create` command exists)

There is no `config` command group. Configuration is authored by the verbs below — never
hand-edit raw JSON when one of these covers it:

| To set… | Use |
|---|---|
| Base URL, headers, accept/content-type, categories, lifecycle, tier | `init` (e.g. `init --base-url`, `init --header VendorName=value`, `init --accept-type`) |
| Auth config keys + the `oauth.scope` MULTISELECT | `auth set` (see [auth.md](auth.md)) |
| The base or pagination key bundle | `init preset apply --kind base \| pagination` |
| The event/polling key bundle | `trigger create --event-kind polling \| webhook \| all` (NOT a config preset) — see [events.md](events.md) |
| One bespoke entry, or a surgical edit to an existing entry | `state patch element.json/configuration/<key>` |

### Presets

```bash
uip is connectors builder init preset apply --kind pagination
uip is connectors builder init preset apply --kind base --override base.url=https://api.acme.com
```
- `--kind base` seeds the base URL + select/nulls/instance keys; `--kind pagination` seeds
  the four pagination keys. `--override key=value` (repeatable) overrides a defaultValue.
- `--force` applies diffs on entries that already exist instead of erroring.
- There is NO `event` preset kind — the event bundle is seeded by `trigger create --event-kind`.

### Surgical edits with `state patch`

To change one config field, `state patch` the entry at
`element.json/configuration/<key>` (e.g. `.../oauth.token.url`). `state patch` REPLACES the
whole node — query first and patch the COMPLETE object back (SKILL.md Rule 5).

## Config Entry Object
`key` (dot-notation, e.g. `oauth.api.key`), `name`, `description`, `type` (widget),
`defaultValue`, `required`, `internal` (system-set), `hide`, `hideFromConsole`,
`encrypt` (secrets), `active` (true), `companyConfig`/`resellerConfig` (false),
`isPrivate` (redact in responses), `displayOrder`, `configScreenType`.
Optional: `groupControl`, `groupBy`, `options` (`[{"description","value"}]`),
`design`, `hintText`.

## Config Types (widgets)
`TEXTFIELD_32|64|128|256|1000` (by max length; 128 = most fields, 1000 = URLs),
`TEXTAREA` (keys/certs/JSON), `PASSWORD` (masked, auto-encrypt), `BOOLEAN`,
`COMBO` (single-select), `MULTISELECT` (OAuth scopes), `CODE_EDITOR`.

## Config Screen Types
`"pre"` (must fill on creation), `"pre-optional"` (optional on creation), `"none"` (hidden).

## Templated (per-instance / per-region / per-workspace) hosts — NO script needed
When the API host differs per connection (Zoho's region `https://desk.{environment}/api/v1`,
Databricks `{workspace.url}`, Sugar `https://{siteUrl}/rest/v11`), put a `{placeholder}` in the
URL and back it with a configuration entry **keyed exactly the same** as the placeholder. At
connection time IS substitutes `{placeholder}` with that config's value. This is the correct,
scriptless way to handle dynamic hosts — do NOT reach for a hook.

- Just template the URL on `init`/`auth set`: `init --base-url 'https://desk.{environment}/api/v1'`,
  `auth set --token-url 'https://{workspace.url}/oidc/v1/token'`. The CLI **auto-seeds** a required
  `TEXTFIELD_1000` config keyed by each placeholder (e.g. `environment`, `workspace.url`), screen
  type `pre`, so the user fills it on the connection form.
- A `{placeholder}` in **`base.url`** also gets an auto-seeded element-level **global path parameter**
  (`{ vendorType:"path", vendorName:"<placeholder>", name:"<configKey>", type:"configuration" }` in
  the root `parameters[]`). This is what actually substitutes the token into **every resource
  request** — the backing config entry alone is NOT enough for `base.url` (it would only resolve the
  OAuth call). The CLI seeds this on `init --base-url` / `auth set`; if you instead set `base.url`
  by raw `state patch`, add the path parameter yourself.
- `validate` HARD-ERRORS if a `{placeholder}` in any URL has no backing config key, AND if a
  `base.url` placeholder has no global path parameter binding it — so an unresolvable host can never ship.
- To upgrade the seeded TEXTFIELD into a **picker** (Zoho's datacenter dropdown), `state patch` the
  entry to `type: COMBO` with `options: [{"value":"zoho.com","description":"zoho.com"}, …]`.
- `${configuration.x}` (dollar-brace) is a value-REFERENCE into an existing config (e.g. an API-key
  header param), NOT a host placeholder — it is not seeded.

## Auth as configuration
Authentication is config keys + `authentication.type`, all written by `auth set`. Secret
keys (client secret, API key, password, token) are written with `encrypt: true` — encrypted
and redacted; most are `PASSWORD` + `isPrivate` (masked), but some (OAuth tokens, a
service-account JSON) are encrypted `TEXTFIELD`/`TEXTAREA`. They hold NO value in the
connector; the tenant user supplies the real secret at connection time. Key sets per type:

- **OAuth2** (16 entries — canonical list; `auth set` writes all of them):
  `oauth.api.key`, `oauth.api.secret` (PASSWORD, encrypt, isPrivate), `oauth.callback.url`
  (auto-set, do NOT hardcode), `oauth.authorization.url`, `oauth.token.url`,
  `oauth.token.refresh_url`, `oauth.token.revoke_url`, `oauth.scope`,
  `oauth.basic.header`, `oauth.user.token`, `oauth.user.refresh_token`,
  `oauth.user.refresh_interval` (sec, default 3600), plus auto-set internals
  `oauth.user.refresh_time`, `oauth.decode.authorization.code`, `authentication.time`,
  `expires_in`. Sets `authentication.type:"oauth2"`, `typeOauth:true`.
  NOTE the underscore in the last segment of the four refresh/revoke keys
  (`refresh_url`, `refresh_token`, `refresh_time`, `refresh_interval`) — the
  all-dots spellings are dead keys the runtime never reads.
- **OAuth2 PKCE** adds `oauth.pkce.code.challenge.verifier`, `oauth.pkce.code.challenge`,
  `oauth.pkce.code.challenge.method` (`"S256"`).
- **OAuth2 Client Credentials**: subset — no auth URL, no refresh token.
- **oauth2PrivateKeyJwt** (client authenticates with a signed assertion, e.g. Epic FHIR):
  `oauth.api.key`, `oauth.token.url`, `jwk.private.key` (TEXTAREA, encrypt), `jwk.kid` —
  the connection user supplies the key + kid. `typeOauth:true`.
- **customApiKey** (the on-disk type for any "API key" auth — the UI labels it "API key",
  but never use periodic's bare `apiKey`): one PASSWORD secret config (default
  `custom.api.key`, encrypt, isPrivate, `groupBy:"customApiKey"`) + one `type:"value"`
  parameter mapping `${configuration.<name>}` into the vendor header/query;
  `authentication.type:"customApiKey"`, `typeOauth:false`. CLI flow + flags:
  [auth.md](auth.md) §customApiKey.
- **basic**: `username`, `password` (PASSWORD, encrypt).
- **jwtOauth / jwtOauth2** (OAuth 2.0 JWT Bearer): `oauth.api.key`, `oauth.api.secret`,
  `oauth.callback.url`, `oauth.token.url`, `jwt.base64.encoded.key` (TEXTAREA — the signing
  key, PKCS#8 PEM or base64), plus one `jwt.claim.<name>` config per assertion claim and
  `jwt.header.<name>` per assertion header (the runtime builds the JWT from every config
  with those prefixes — Salesforce ships `jwt.claim.iss/sub/aud`). Wire claims with
  `auth set --jwt-claim` / `--jwt-header` ([auth.md](auth.md) §"JWT Bearer"). `typeOauth:true`.
  (The old `jwt.oauth.*` keys are read by NOTHING — never write them.)
- **awsv4**: `aws.api.key`, `aws.api.secret`, `aws.region` (user-filled), `aws.service.name`
  (hidden, per-service constant like `connect`), `aws.host` (hidden). Put the region in the
  base URL as `https://<service>.{aws.region}.amazonaws.com` — the CLI binds `{aws.region}`
  to the config automatically.
- **none**: no auth configs at all — `authentication.type:"none"` only (open APIs, webhooks).
- **firstPartyService / fpsUserDelegatedAccess / fpsRobotAccess** (UiPath internal services
  ONLY): no user credentials — the platform injects the caller's identity. `oauth.scope`
  (hidden) carries the service scope (set via `auth set --scope`). base.url uses
  `https://{host}/{account}/{tenant}/<service>_` and the CLI binds those three placeholders
  to the internal headers `x-forwarded-host` / `x-uipath-internal-accountid` /
  `x-uipath-internal-tenantid` (`type:"header"` path params) — they are NOT connection-form
  fields. `fpsUserDelegatedAccess` adds `oauth.user.refresh_token`.

## Multi-auth (groupControl)
An `authentication.type` COMBO with `"groupControl": true` plus per-type config entries
tagged with `groupBy`. Fields without `groupBy` always show; comma-separated `groupBy`
shows the field for multiple groups.

## Scope entry (`oauth.scope`, MULTISELECT)
Built by the `auth set --scope*` flags — only when `--scope-options`/`--scope-options-file` or
`--required-scopes` triggers it (condition + flag list in [auth.md](auth.md)). The `design`
block carries `requiredOptions` (cannot deselect), `preSelectedOptions` (pre-checked),
`delimiter`, `enableUserOverride`; `options` is the `[{"description","value"}]` list.

## Pagination keys (`init preset apply --kind pagination`)
The pagination preset seeds exactly four keys: `pagination.max` (TEXTFIELD_32, default `100`),
`pagination.type` (TEXTFIELD_32 — e.g. cursor/offset/page), `pagination` (TEXTFIELD_128, a
pagination-config JSON string), and `pagination.page.startindex` (TEXTFIELD_32, default `1`).
`base.url` and `filter.response.nulls` are seeded by the `--kind base` preset, NOT this one.
`paginatorVersion` at top level selects the engine.

## Event keys
Polling/webhook config keys (`event.notification.*`, `event.vendor.type`, `event.poller.*`,
`event.raw.enabled`) are seeded by `trigger create --event-kind` and documented in
[events.md](events.md) §"Polling config keys" — the canonical list. They are ordinary
`configuration[]` entries.

## See also
- [auth.md](auth.md), [system-resources.md](system-resources.md), [events.md](events.md)
