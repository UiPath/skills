# System Resources Reference

System resources are `element.json → resources[]` entries with NO SR file and no
`standardResourceName`. They never appear as CRUD/curated activities — they exist for
connector lifecycle, auth flow, or runtime overrides.

Create them with `auth system create --type <TYPE>` (the old `resource system` is gone).
Flags: `--vendor-path <path>`, `--method <verb>` (defaults to POST when the type requires
one), `--next-resource <selector>` (chain, e.g. `GET:/organization`), and `--path <path>`
(explicit resource path — must match the type's override path when it declares one). List
the system entries on a connector with `auth system list`. Use `activity create` for a
NORMAL API endpoint, never this.

```bash
uip is connectors builder auth system create --type provisionAuthValidation --vendor-path /me
```

## provisionAuthValidation — verify creds at connection time
Runs one test API call at connection creation; a failure rejects the connection
immediately. Override path `/auth_validation`, `vendorPath` a cheap authenticated
read-only endpoint (`/me`, `/users/me`, `/account`, smallest list endpoint), `method`
GET (the probe must be read-only and must not change vendor data).
```json
{"type": "provisionAuthValidation", "path": "/auth_validation", "vendorPath": "/me", "method": "GET", "vendorMethod": "GET"}
```
Required for `customApiKey`, `personalAccessToken`, `basic`, `awsv4` (no token exchange to
catch bad creds); recommended for OAuth/JWT types. `auth set` seeds it directly when
`--validation-vendor-path` is given (`--validation-method` defaults to GET); `validate`
warns when missing.

**If the validation endpoint needs a constant query param** (e.g. Azure Form Recognizer's
`/info?api-version=2023-07-31`), do NOT bake it into `vendorPath` — the server parses the
`?k=v` into a required, value-less input and the connection test fails at runtime. Keep
`vendorPath` the bare path and add the constant as a `value` param (see
[element-json.md](element-json.md) → "Static / constant query parameters"):
```json
{"type": "provisionAuthValidation", "path": "/auth_validation", "vendorPath": "/info", "method": "GET", "vendorMethod": "GET",
 "parameters": [{"name": "2023-07-31", "vendorName": "api-version", "type": "value", "vendorType": "query"}]}
```
`auth set --validation-vendor-path '/info?api-version=2023-07-31'` now does this extraction
for you (strips the query, emits the `value` param).

## Override-path table
| Type | Override path | vendorPath/method required? |
|------|---------------|------------------------------|
| `onProvision` | (custom) | yes / yes |
| `onDelete` | (custom) | optional / optional |
| `onRefresh` | `/on-refresh` | optional / optional |
| `provisionAuthValidation` | `/auth_validation` | yes / yes |
| `oauthOnAuthroizeUrl` | `/auth/authorize` | optional / yes |
| `oauthOnTokenExchange` | `/oauthOnTokenExchange` | yes / yes |
| `oauthOnTokenRefresh` | `/oauthOnTokenRefresh` | yes / yes |
| `oauthOnTokenRevoke` | (custom) | optional / optional |
| `onProvisionWebhook` | (custom) | yes / yes |
| `onDeleteWebhook` | (custom) | optional / optional |

- **onProvision**: setup work at creation (fetch metadata, validate permissions, chain
  calls via `--next-resource`). **onDelete**: teardown (revoke tokens, deregister).
- **oauthOnTokenRefresh**: replaces default OAuth2 refresh for non-standard request
  shapes; `auth set` auto-creates it for refresh-token OAuth types (not client creds).
- **oauthOnTokenExchange**: replaces default code→token exchange.
- **oauthOnAuthroizeUrl** (historical typo, keep it): dynamic authorize URL via a
  preRequest hook (tenant/region/verifier in the URL).
- **onProvisionWebhook / onDeleteWebhook**: register/deregister vendor webhooks.

For fixed-path types the `path` MUST match exactly — that is how Udon swaps the built-in
default for your custom one. Pass it via `--path`; `auth system create` validates it
against the type's declared override path.

## See also
- [element-json.md](element-json.md), [configuration.md](configuration.md), [events.md](events.md)
