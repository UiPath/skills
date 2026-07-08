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

All 19 types are supported. `init --auth <type>` accepts any of them inline at create
time (handy for `none`); type-specific flags beyond init's OAuth sugar go through `auth set`.

| auth-type               | Use when                                        |
|-------------------------|-------------------------------------------------|
| oauth2                  | OAuth 2.0 Authorization Code flow.              |
| oauth2Pkce              | OAuth 2.0 Authorization Code + PKCE.            |
| oauth2ClientCredentials | OAuth 2.0 Client Credentials (no user).         |
| oauth2Password          | OAuth 2.0 Resource Owner Password.              |
| oauth2PrivateKeyJwt     | OAuth 2.0 Private Key JWT (signed client assertion, e.g. Epic FHIR). |
| oauth1                  | OAuth 1.0a / Token-Based Authentication (TBA).  |
| basic                   | HTTP Basic (username + password).               |
| jwtOauth                | OAuth 2.0 JWT Bearer (service accounts — Salesforce, Box). |
| jwtOauth2               | Same contract as jwtOauth (legacy alias — prefer jwtOauth). |
| custom                  | A custom static authorization header.           |
| customApiKey            | Vendor uses a static API key (header or query). |
| personalAccessToken     | Personal access token authorization header.     |
| awsv4                   | AWS Signature v4.                               |
| googleServiceAccount    | Google service-account JSON.                    |
| rsaCertificate          | RSA private-key certificate.                    |
| none                    | Open/unauthenticated API (webhooks, public endpoints). |
| firstPartyService       | UiPath internal service — platform-injected service identity. |
| fpsUserDelegatedAccess  | UiPath internal service — acts as the connection's user. |
| fpsRobotAccess          | UiPath internal service — robot access token.   |

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

## JWT Bearer (jwtOauth / jwtOauth2)

The connector holds the token URL and the SHAPE of the JWT assertion; the connection user
supplies the client id/secret, the signing key (`jwt.base64.encoded.key` — PKCS#8 PEM or
base64), and any user-specific claim values. The runtime builds the assertion from every
config keyed `jwt.claim.<name>` (payload) / `jwt.header.<name>` (header) — declare each with
a repeatable flag:

```bash
uip is connectors builder auth set --auth-type jwtOauth \
  --token-url https://login.salesforce.com/services/oauth2/token \
  --jwt-claim aud=https://login.salesforce.com \
  --jwt-claim iss \
  --jwt-claim sub \
  --scope 'api refresh_token'
```

- `--token-url` is REQUIRED (the assertion is exchanged there for an access token).
- `--jwt-claim name=value` pre-fills the claim (still editable at connection time);
  `--jwt-claim name` (bare) creates it required-and-empty — the connection user fills it
  (e.g. Salesforce `iss` = consumer key, `sub` = username).
- Label/hint the connection-form field inline: `--jwt-claim 'iss;label=Consumer Key;hint=The connected app consumer key'`
  — without a label the field renders as "JWT claim 'iss'".
- `--jwt-header kid=...` for assertion headers, same syntax (label/hint work too).
- The runtime ALSO requires `oauth.api.key` (client id) and `oauth.api.secret` — the bundle
  ships both as connection-form fields. For Salesforce-style flows where iss == client id,
  the user enters the same value twice; that is the platform contract, not a bug.
- jwtOauth intentionally creates NO `oauthOnTokenRefresh` resource — there is no refresh
  token; the runtime signs a fresh assertion when the access token expires. Do not add one.
- `jwt.base64.encoded.key` (the signing key) is `internal: true, configScreenType: none`
  BY DESIGN — every catalog jwt connector (Box, Salesforce, uipath-http) ships it that way
  and the IS connection UI renders the private-key field for jwt flows itself. Do NOT
  "fix" it to `pre`.
- Typical claim sets: Salesforce `iss`/`sub` + `aud=https://login.salesforce.com`;
  Box `iss`/`sub` + `aud=<token url>` + `box_sub_type=enterprise`.
- NEVER write `jwt.oauth.*` config keys (consumer.key/private.key/username) — nothing in
  the platform reads them; a connector built with them can never authenticate.

## OAuth 2.0 Private Key JWT (oauth2PrivateKeyJwt)

Client-credentials-style flow where the client authenticates with a SIGNED ASSERTION
instead of a client secret (Epic FHIR is the catalog reference):

```bash
uip is connectors builder auth set --auth-type oauth2PrivateKeyJwt \
  --token-url https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token
```

The bundle ships `oauth.api.key` (client id), `jwk.private.key`, `jwk.kid` as
connection-form fields — the user pastes the registered key + kid at connection time.

## UiPath First Party Service (firstPartyService / fpsUserDelegatedAccess / fpsRobotAccess)

INTERNAL-ONLY — connectors that call UiPath's own services (Orchestrator, Data Fabric,
Apps…). There are NO credential fields: the platform injects the caller's identity at
runtime. Choose the flavor by whose token the connector should act with: the service
(`firstPartyService`), the connection's user (`fpsUserDelegatedAccess`), or a robot
(`fpsRobotAccess`).

```bash
uip is connectors builder init --name "My Service" \
  --base-url 'https://{host}/{account}/{tenant}/myservice_'
uip is connectors builder auth set --auth-type firstPartyService \
  --scope MyServiceApiUserAccess
```

- `--scope` = the first-party scope the platform token is minted with (e.g.
  `OrchestratorApiUserAccess`, `DataService`); it lands hidden on `oauth.scope` — an
  authoring-time value, never a connection-form field.
- base.url follows `https://{host}/{account}/{tenant}/<service>_` — `auth set` binds those
  three placeholders to the platform headers (`x-forwarded-host`,
  `x-uipath-internal-accountid`, `x-uipath-internal-tenantid`) automatically, CONVERTING
  any user-fillable configs + configuration-type bindings a prior `init --base-url` seeded
  (they show up under `ConfigChanges.removed`). Either command order works.
- VERIFY with `auth get`: `FpsBindings` lists each placeholder and the header it resolves
  from (`boundToHeader: null` = broken), and `ConnectionFormFields: []` proves no
  user-facing fields. `validate` errors on any FPS connector whose placeholders are
  user-fillable or configuration-bound.
- `auth set` also seeds hidden RUNTIME bookkeeping entries (`oauth.user.token`,
  `oauth.user.refresh_time`, `oauth.user.refresh_interval`, `oauth.basic.header`; the
  delegated type adds `oauth.user.refresh_token`) — token storage the platform writes at
  runtime, never credential fields. Leave them alone.

## No authentication (none)

```bash
uip is connectors builder auth set --auth-type none
```

Records `authentication.type:"none"` with zero credential configs — for open APIs and
webhook-style connectors (catalog: http-webhook, generic-webhooks). `validate` requires SOME
auth type on every connector, so run this even when the API needs no credentials.

## AWS Signature v4 (awsv4)

```bash
uip is connectors builder init --name "Amazon Connect" \
  --base-url 'https://connect.{aws.region}.amazonaws.com'
uip is connectors builder auth set --auth-type awsv4 --aws-service-name connect
```

The bundle ships `aws.api.key` / `aws.api.secret` / `aws.region` as connection-form fields
plus hidden `aws.service.name` / `aws.host`. `--aws-service-name` sets the per-service
SigV4 constant (e.g. `polly`, `connect`) — no `state patch` needed. Put `{aws.region}` in
base.url — the CLI binds it to the region config automatically, and `auth set` silently
replaces the generic placeholder config `init` seeded with the canonical AWS one (no
`--force` required).

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
so keep it GET. Credential auth types with no token exchange (`basic`, `custom`,
`customApiKey`, `personalAccessToken`, `awsv4`, `googleServiceAccount`, `rsaCertificate`)
get a `validate` warning when it is missing. OAuth/JWT flows (token exchange catches bad
creds), `none` (no credentials), and the FPS family (platform identity) are exempt —
`validate` does not ask for a probe there. Details: [system-resources.md](system-resources.md) §provisionAuthValidation.

## System (lifecycle) resources — `auth system`

Lifecycle/auth-flow endpoints with no SR file (provisionAuthValidation, onProvision,
oauthOnTokenRefresh, …) are wired with `auth system create --type <type>` / `auth system list`.
The full type list, override-path rules, and flags: [system-resources.md](system-resources.md).

## Base URL derived from a token response

There is no service-specific base-url flag (`init --base-url` is STATIC only). When the token
response returns the API host or another per-connection value, use the generic hook pattern:
a `postRequest` hook reads + validates the value (scheme, host/id shape, allowlist where applicable), then persists it into THIS connection's config
at runtime via `done({configuration})` — NOT `state patch` (that baking-time edit would set one
org's URL as everyone's default). Full pattern: [hooks.md](hooks.md) §"Pattern: base URL …
derived from a token response".

## Verifying auth setup — `auth get`

`auth get` returns the full auth read model in one call: the type(s), every auth-related
config entry (key, label, hint, screen type, hidden/required/encrypted flags, defaults
with secrets redacted), `ConnectionFormFields` (EVERY visible config across the whole
connector — the literal connection form; `[]` = empty form), whether
`oauthOnTokenRefresh` / `provisionAuthValidation` exist, `FpsBindings` (FPS
placeholder→header map), and `TemplateBindings` (each non-FPS base.url `{placeholder}`
with whether its backing config entry + path-param binding exist). Use it instead of
stitching `state query` calls.

## Re-running auth set

Idempotent on identical inputs (returns `unchanged`). If a new input would modify an
existing entry, it fails with a `configConflict` listing every diff — re-run with `--force`
to apply. Use this to swap an existing connector's auth type.

## See also
- [configuration.md](configuration.md) — config keys per auth type, widget/screen types
- [system-resources.md](system-resources.md) — auth-validation, token-refresh overrides
- [element-json.md](element-json.md) — element.json structure and the authentication block
