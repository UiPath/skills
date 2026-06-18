# System Resources Reference

System resources are `element.json → resources[]` entries with NO SR file and no
`standardResourceName`. They never appear as CRUD/curated activities — they exist for
connector lifecycle, auth flow, or runtime overrides. Add via
`resource system create --type <TYPE>` (skips SR creation). For types with a built-in
default, the `path` is fixed and MUST match exactly; `(custom)` types let you choose.

## provisionAuthValidation — verify creds at connection time
Runs one test API call at connection creation; a failure rejects the connection
immediately. Override path `/auth_validation`, `vendorPath` a cheap authenticated
read-only endpoint (`/me`, `/users/me`, `/account`, smallest list endpoint),
`method` usually GET.
```json
{"type": "provisionAuthValidation", "path": "/auth_validation", "vendorPath": "/me", "method": "GET", "vendorMethod": "GET"}
```
Required for `customApiKey`, `personalAccessToken`, `basic`, `awsv4` (no token
exchange to catch bad creds); recommended for OAuth/JWT types. `auth set` seeds it
when `--validation-vendor-path` is given; `validate` warns when missing.

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

- **onProvision**: setup work at creation (fetch metadata, validate permissions,
  chain calls via `nextResource`). **onDelete**: teardown (revoke tokens, deregister).
- **oauthOnTokenRefresh**: replaces default OAuth2 refresh for non-standard request
  shapes; `auth set` auto-creates it for refresh-token OAuth types (not client creds).
- **oauthOnTokenExchange**: replaces default code→token exchange.
- **oauthOnAuthroizeUrl** (historical typo, keep it): dynamic authorize URL via a
  preRequest hook (tenant/region/verifier in the URL).
- **onProvisionWebhook / onDeleteWebhook**: register/deregister vendor webhooks.

For fixed-path types the `path` MUST match exactly — that is how Udon swaps the
built-in default for your custom one.

## See also
- [element-json.md](element-json.md), [configuration.md](configuration.md), [events.md](events.md)
