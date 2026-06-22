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
- `validate` HARD-ERRORS if a `{placeholder}` in any URL has no backing config key — so an unbacked
  host can never ship.
- To upgrade the seeded TEXTFIELD into a **picker** (Zoho's datacenter dropdown), `state patch` the
  entry to `type: COMBO` with `options: [{"value":"zoho.com","description":"zoho.com"}, …]`.
- `${configuration.x}` (dollar-brace) is a value-REFERENCE into an existing config (e.g. an API-key
  header param), NOT a host placeholder — it is not seeded.

## Auth as configuration
Authentication is config keys + `authentication.type`, all written by `auth set`. Secret
keys (client secret, API key, password, token) are PASSWORD widgets with `encrypt: true`
and `isPrivate: true` — encrypted, masked, redacted. They hold NO value in the connector;
the tenant user supplies the real secret at connection time. Key sets per type:

- **OAuth2** (16 entries — canonical list; `auth set` writes all of them):
  `oauth.api.key`, `oauth.api.secret` (PASSWORD, encrypt, isPrivate), `oauth.callback.url`
  (auto-set, do NOT hardcode), `oauth.authorization.url`, `oauth.token.url`,
  `oauth.token.refresh.url`, `oauth.token.revoke.url`, `oauth.scope`,
  `oauth.basic.header`, `oauth.user.token`, `oauth.user.refresh.token`,
  `oauth.user.refresh.interval` (sec, default 3600), plus auto-set internals
  `oauth.user.refresh.time`, `oauth.decode.authorization.code`, `authentication.time`,
  `expires_in`. Sets `authentication.type:"oauth2"`, `typeOauth:true`.
- **OAuth2 PKCE** adds `oauth.pkce.code.challenge.verifier`, `oauth.pkce.code.challenge`,
  `oauth.pkce.code.challenge.method` (`"S256"`).
- **OAuth2 Client Credentials**: subset — no auth URL, no refresh token.
- **customApiKey** (the on-disk type for any "API key" auth — the UI labels it "API key",
  but never use periodic's bare `apiKey`): one PASSWORD secret config (default
  `custom.api.key`, encrypt, isPrivate, `groupBy:"customApiKey"`) + one `type:"value"`
  parameter mapping `${configuration.<name>}` into the vendor header/query;
  `authentication.type:"customApiKey"`, `typeOauth:false`. CLI flow + flags:
  [auth.md](auth.md) §customApiKey.
- **basic**: `username`, `password` (PASSWORD, encrypt).
- **jwtOauth**: `jwt.oauth.consumer.key`, `jwt.oauth.private.key`, `jwt.oauth.username`,
  `jwt.oauth.token.url`, `jwt.oauth.scope`. `typeOauth:true`.
- **awsv4**: `aws.api.key`, `aws.api.secret`, `aws.region`, `aws.service.name`, `aws.host`.

## Multi-auth (groupControl)
An `authentication.type` COMBO with `"groupControl": true` plus per-type config entries
tagged with `groupBy`. Fields without `groupBy` always show; comma-separated `groupBy`
shows the field for multiple groups.

## Scope entry (`oauth.scope`, MULTISELECT)
Built by the `auth set --scope*` flags (see [auth.md](auth.md)). The `design` block carries
`requiredOptions` (cannot deselect), `preSelectedOptions` (pre-checked), `delimiter`,
`enableUserOverride`; `options` is the `[{"description","value"}]` list.

## Pagination keys (`init preset apply --kind pagination`)
`pagination.type` (cursor/offset/page), `pagination.max`, `base.url` (TEXTFIELD_1000),
`filter.response.nulls`. `paginatorVersion` at top level selects the engine.

## Event keys
Polling/webhook config keys (`event.notification.*`, `event.vendor.type`, `event.poller.*`,
`event.raw.enabled`) are seeded by `trigger create --event-kind` and documented in
[events.md](events.md) §"Polling config keys" — the canonical list. They are ordinary
`configuration[]` entries.

## See also
- [auth.md](auth.md), [system-resources.md](system-resources.md), [events.md](events.md)
