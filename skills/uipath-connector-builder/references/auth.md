# Authentication in UiPath Integration Service connectors

A connector's authentication block tells Integration Service which auth flow to run when a
tenant creates a connection. `auth set` writes all of it in one call: the **config entries**
in `element.json → configuration[]` (one per credential/endpoint URL — these render the
connection form AND drive the OAuth dance / API-key wiring) plus the **top-level fields**
`authentication.type`, `typeOauth`, `elementMetadata.authenticationTypes` (which select the
flow). The definition holds only the auth TYPE, endpoint URLs, and scopes — never real creds.

## SECURITY — secrets are never stored in the connector

Secret config keys (client secret, API key, password, token) are written by `auth set` with
`encrypt: true` — encrypted at rest and redacted in responses. Most are `type: PASSWORD` +
`isPrivate: true` (also masked); some sensitive values use a non-PASSWORD widget but stay
encrypted — e.g. an OAuth user token (`TEXTFIELD`) or a Google service-account JSON
(`TEXTAREA`). Rules:

- NEVER echo, `cat`, log, or print a secret value. `auth get` / `inspect` return the config
  SHAPE, not the value — there is nothing to dump.
- NEVER put a real secret in an example command. Use placeholders (`<CLIENT_ID>`, the
  vendor's header name) — secret VALUES are not part of the connector at all.
- The tenant user supplies `client id`, `client secret`, `api key`, etc. at connection time.

## Auth types (`auth set --auth-type`)

All 14 types are supported. `init --auth` is sugar for the two most common (`oauth2`,
`customApiKey`) at create time; everything else (and the full flag surface) goes through
`auth set`.

| auth-type               | Use when                                        |
|-------------------------|-------------------------------------------------|
| oauth2                  | OAuth 2.0 Authorization Code flow.              |
| oauth2Pkce              | OAuth 2.0 Authorization Code + PKCE.            |
| oauth2ClientCredentials | OAuth 2.0 Client Credentials (no user).         |
| oauth2Password          | OAuth 2.0 Resource Owner Password.              |
| oauth1                  | OAuth 1.0a / Token-Based Authentication (TBA).  |
| basic                   | HTTP Basic (username + password).               |
| jwtOauth                | JWT-bearer OAuth.                               |
| jwtOauth2               | JWT-bearer OAuth 2.0.                           |
| custom                  | A custom static authorization header.           |
| customApiKey            | Vendor uses a static API key (header or query). |
| personalAccessToken     | Personal access token authorization header.     |
| awsv4                   | AWS Signature v4.                               |
| googleServiceAccount    | Google service-account JSON.                    |
| rsaCertificate          | RSA private-key certificate.                    |

Per-type config key sets (which secrets, which URLs) are in
[configuration.md](configuration.md) §"Auth as configuration".

## OAuth 2.0 (authorization_code)

```bash
uip is connectors builder auth set --auth-type oauth2 \
  --authorization-url https://acme.com/oauth/authorize \
  --token-url https://acme.com/oauth/token \
  --scope 'read write'
```
- `--authorization-url`, `--token-url`, `--scope` are the core flags.
- `--token-refresh-url` defaults to `--token-url`; `--token-revoke-url` is optional.
- **Extra authorize query params need NO script** — append them to `--authorization-url`
  directly; they are preserved verbatim. Use this for vendors that require a refresh-token opt-in
  on the consent URL: Dropbox `?token_access_type=offline`, Zoho `?access_type=offline`,
  Google `?access_type=offline&prompt=consent`.
- A per-region/instance/workspace host belongs in the URL as `{placeholder}` (e.g.
  `https://accounts.{environment}/oauth/v2/token`) — the CLI auto-seeds a backing config; see
  [configuration.md](configuration.md) §"Templated hosts". No hook needed.
- For refresh-token OAuth types (not client credentials), `auth set` also creates an
  `oauthOnTokenRefresh` system resource pointing at the refresh URL.

## OAuth / JWT scope surface (FLAGS on `auth set` — there is NO `auth scope` command)

`--scope` always sets the default scope string. To make scopes USER-SELECTABLE (the
`oauth.scope` MULTISELECT with options/required/preselected), the TRIGGER is `--scope-options`
(or `--scope-options-file`) OR `--required-scopes` — without one of those the MULTISELECT
override is NOT built. The remaining flags are modifiers that take effect ONLY once the
override exists, so `--preselected-scopes` (or `--scope-delimiter`/`--scope-hint-text`/
`--scope-screen-type`) ALONE does nothing. Pass them on the SAME `auth set` call (or re-run
with `--force`):

| Flag | Purpose |
|------|---------|
| `--scope <str>` | Space-delimited scope string (the default scope value). |
| `--scope-options <json>` | JSON array of `{description,value}` selectable options. |
| `--scope-options-file <path>` | Read `--scope-options` JSON from a file. |
| `--required-scopes <csv>` | Scopes the user cannot deselect. |
| `--preselected-scopes <csv>` | Scopes pre-checked by default. |
| `--scope-delimiter <char>` | Scope separator (default: space). |
| `--scope-hint-text <text>` | Hint shown under the scope selector. |
| `--scope-screen-type <type>` | configScreenType for the scope entry (default: pre). |

```bash
uip is connectors builder auth set --auth-type oauth2 \
  --authorization-url https://acme.com/oauth/authorize \
  --token-url https://acme.com/oauth/token \
  --scope 'read write' \
  --scope-options '[{"description":"Read","value":"read"},{"description":"Write","value":"write"}]' \
  --required-scopes read --preselected-scopes read,write
```

## customApiKey

```bash
uip is connectors builder auth set --auth-type customApiKey \
  --api-key-param-name X-API-Key --api-key-location header \
  --validation-vendor-path /me      # provisionAuthValidation (see below) — recommended for static auth
```
- `--api-key-param-name` (required): vendor header/query name (`X-API-Key`, `Authorization`,
  `subscription-key`) from vendor docs.
- `--api-key-location`: `header` (default) or `query`. `--api-key-prefix`: literal prefix
  prepended to the value (e.g. `Bearer `).
- `--key-config-name`: internal config key (default `custom.api.key`). `--key-config-display-name`:
  UI label (default `API Key`).

What it writes (the PASSWORD secret entry + the `type:"value"` parameter mapping
`${configuration.<name>}` into the vendor header/query): [configuration.md](configuration.md) §"Auth as configuration".

## Multiple credential headers (any auth type) — `--auth-header` / `--secret-auth-header`

Some vendors authenticate with SEVERAL static headers (e.g. iContact: `API-AppId`, `API-Username`,
`API-Password`, `API-Version`). `auth set` (esp. with `--auth-type custom`) takes repeatable flags —
no script, no `state patch`:

```bash
uip is connectors builder auth set --auth-type custom \
  --auth-header AppID=API-AppId \
  --auth-header api.username=API-Username \
  --secret-auth-header api.password=API-Password
```

Each `ConfigName=VendorHeader` writes a `pre`/required config entry (`--secret-auth-header` makes it a
PASSWORD/encrypted) plus a global `${configuration.<ConfigName>}` → vendor-header parameter. The tenant
user fills each on the connection form. Static (non-credential) headers like `API-Version` or
`Content-Type` go through `init --header VendorName=value` (a `type:"value"` param). Bespoke config keys
ARE accepted by the backend (the catalogue connectors use them) — just declare them through these flags
rather than hand-editing `configuration[]`.

## Auth-validation probe (any type)

`--validation-vendor-path <path>` (with optional `--validation-method`, default GET) seeds
a `provisionAuthValidation` system resource — one read-only call at connection creation that
rejects bad creds immediately. The probe must be read-only and must not change vendor data,
so keep it GET. Every non-OAuth/JWT auth type (any whose name isn't `oauth*`/`jwt*` — `basic`,
`custom`, `customApiKey`, `personalAccessToken`, `awsv4`, `googleServiceAccount`,
`rsaCertificate`) has no token exchange to catch bad creds, so `validate` flags it as missing
there. Details: [system-resources.md](system-resources.md) §provisionAuthValidation.

## System (lifecycle) resources — `auth system`

Lifecycle/auth-flow endpoints with no SR file (provisionAuthValidation, onProvision,
oauthOnTokenRefresh, …) are wired with `auth system create --type <type>` / `auth system list`.
The full type list, override-path rules, and flags: [system-resources.md](system-resources.md).

## Base URL derived from a token response (e.g. Salesforce `instance_url`)

There is NO vendor-specific base-url flag (`init --base-url` is STATIC only). When the vendor
returns the API host in its token response, it is skill-guided: a `postRequest` hook reads +
validates the host (https scheme, allowlisted), then persists it into THIS connection's config
at runtime via `done({configuration})` — NOT `state patch` (that baking-time edit would set one
org's URL as everyone's default). Full pattern: [hooks.md](hooks.md) §"Pattern: base URL …
derived from a token response".

## Re-running auth set

Idempotent on identical inputs (returns `unchanged`). If a new input would modify an
existing entry, it fails with a `configConflict` listing every diff — re-run with `--force`
to apply. Use this to swap an existing connector's auth type.

## See also
- [configuration.md](configuration.md) — config keys per auth type, widget/screen types
- [system-resources.md](system-resources.md) — auth-validation, token-refresh overrides
- [element-json.md](element-json.md) — element.json structure and the authentication block
