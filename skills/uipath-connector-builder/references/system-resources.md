# System Resources Reference

System resources are `element.json → resources[]` entries with NO SR file and no
`standardResourceName`. They never appear as CRUD/curated activities — they exist for
connector lifecycle, auth flow, or runtime overrides.

Create them with `auth system create --type <TYPE>`; list them with `auth system list`
(command map in SKILL.md). Flag semantics specific to this verb: `--method <verb>` falls back to
the type's `defaultMethod` (`GET` for `provisionAuthValidation`), then to `POST` for other
method-requiring types — types that don't require a method (`onProvision`/`onDelete`/`onRefresh`)
get NO method unless you pass `--method`. `--next-resource <selector>` chains a follow-up (e.g.
`GET:/organization`); `--path <path>` must equal the type's override path when it declares one
(see table). Use `activity create` for a NORMAL API endpoint.

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
`validate` surfaces a WARNING (never a hard error) when it's missing and any auth type is set —
labeled `required` for non-OAuth/JWT types (any whose name doesn't start with `oauth`/`jwt`:
`basic`, `custom`, `customApiKey`, `personalAccessToken`, `awsv4`, `googleServiceAccount`,
`rsaCertificate` — they have no token exchange to catch bad creds), and `recommended` (still
surfaced) for OAuth/JWT-only connectors. `auth set` seeds it when `--validation-vendor-path` is
given (`--validation-method` defaults to GET).

**If the validation endpoint needs a constant query param** (e.g. Azure Form Recognizer's
`/info?api-version=2023-07-31`): don't bake it into `vendorPath` — add it as a `value` param
(rationale: [element-json.md](element-json.md) → "Static / constant query parameters").
`auth set --validation-vendor-path '/info?api-version=2023-07-31'` extracts it for you; the
resulting resource is:
```json
{"type": "provisionAuthValidation", "path": "/auth_validation", "vendorPath": "/info", "method": "GET", "vendorMethod": "GET",
 "parameters": [{"name": "2023-07-31", "vendorName": "api-version", "type": "value", "vendorType": "query"}]}
```

## Override-path table
`vendorPath / method` = the type's declared `requiresVendorPath` / `requiresMethod` expectation
(`RESOURCE_TYPE_INFO`) — provide both for any `yes`. NOTE: `auth system create` does NOT
hard-reject a missing one — `vendorPath` defaults to `/<name>` and `method` falls back per the
rule above; the only hard error is a `--path` that conflicts with the type's override path. All
13 system types:

| Type | Override path | vendorPath / method expected? |
|------|---------------|------------------------------|
| `onProvision` | (custom) | no / no |
| `onDelete` | (custom) | no / no |
| `onRefresh` | `/on-refresh` | no / no |
| `provisionAuthValidation` | `/auth_validation` | yes / yes (method defaults GET) |
| `oauthOnAuthroizeUrl` | `/auth/authorize` | no / yes |
| `oauthOnTokenExchange` | `/oauthOnTokenExchange` | yes / yes |
| `oauthOnTokenRefresh` | `/oauthOnTokenRefresh` | yes / yes |
| `oauthOnTokenRevoke` | (custom) | yes / yes |
| `oauth1OnTokenRequest` | (custom) | yes / yes |
| `oauth2ClientCredentials` | (custom) | yes / yes |
| `onProvisionWebhook` | (custom) | yes / yes |
| `onDeleteWebhook` | (custom) | yes / yes |
| `onProvisionCacheVendorDataAsync` | (custom) | yes / yes |

- **onProvision**: setup work at creation (fetch metadata, validate permissions, chain
  calls via `--next-resource`). **onDelete**: teardown (revoke tokens, deregister).
- **oauthOnTokenRefresh**: replaces default OAuth2 refresh for non-standard request
  shapes; `auth set` auto-creates it for refresh-token OAuth types (not client creds).
- **oauthOnTokenExchange**: replaces default code→token exchange.
  **oauthOnTokenRevoke**: custom revoke handler called on disconnect.
- **oauthOnAuthroizeUrl** (historical typo, keep it): dynamic authorize URL via a
  preRequest hook (tenant/region/verifier in the URL).
- **oauth1OnTokenRequest**: OAuth 1.0 token-request handler.
  **oauth2ClientCredentials**: custom client-credentials grant handler.
- **onProvisionWebhook / onDeleteWebhook**: register/deregister vendor webhooks.
  **onProvisionCacheVendorDataAsync**: async cache of vendor data at provisioning.

For fixed-path types the `path` MUST match exactly — that is how Udon swaps the built-in
default for your custom one. Pass it via `--path`; `auth system create` validates it
against the type's declared override path.

## See also
- [element-json.md](element-json.md), [configuration.md](configuration.md), [events.md](events.md)
