# Authentication in UiPath Integration Service connectors

A connector's authentication block tells Udon which auth flow to run
when a tenant creates a connection. Two pieces are involved:

1. **Config entries** in element.json `configuration[]`: every credential
   or endpoint URL gets one entry. Udon uses these to render the
   connection form AND to drive the OAuth dance / API-key wiring at runtime.
2. **Top-level fields**: `authentication.type`, `typeOauth`,
   `elementMetadata.authenticationTypes`. Together they select the flow.

`auth set` writes all of these in one shot.

## Supported auth types

All 14 auth types periodic recognises are supported:

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

OAuth/JWT types additionally accept a rich scope surface (--scope-options,
--required-scopes, --preselected-scopes, --scope-delimiter, --scope-hint-text,
--scope-screen-type) that builds an `oauth.scope` MULTISELECT. The scope
option list can also be managed standalone with `auth scope set|add|delete`.

OAuth2 and customApiKey are detailed below as the two most common flows. For the other
types, the required flags are discoverable with `auth set --help` (or `describe auth set`);
[configuration.md](configuration.md) §"Auth as configuration" lists the config key set for
the common ones (basic, jwtOauth, awsv4, PKCE, client credentials).

## OAuth 2.0 (authorization_code)

Required CLI arguments:
- --authorization-url    Login/consent page (where the user grants access)
- --token-url            Token exchange endpoint
- --scope                Space-delimited scope string

Optional:
- --token-refresh-url    Defaults to --token-url
- --token-revoke-url

What gets written to element.json:
- 16 OAuth2 config entries — full key list in [configuration.md](configuration.md) §"Auth as configuration".
- `authentication = { "type": "oauth2" }`, `typeOauth = true`,
  `elementMetadata.authenticationTypes` appends "oauth2".
- A resources[] entry of type "oauthOnTokenRefresh" pointing at the refresh URL —
  periodic calls this when the access token expires.

## customApiKey

Required:
- --api-key-param-name   Vendor's header or query parameter name
                         (e.g. 'X-API-Key', 'Authorization',
                         'subscription-key'). Decided from vendor docs.

Optional:
- --api-key-location     'header' (default) or 'query'
- --api-key-prefix       Literal prefix prepended to the key value (e.g.
                         'Bearer '). Empty = no prefix.
- --key-config-name      Internal config key. Defaults to 'custom.api.key'.
                         Override with a vendor-meaningful name if your
                         docs/parameter mappings reference a different
                         name (e.g. 'subscription.key').
- --key-config-display-name  UI label. Defaults to 'API Key'.

Copy-paste (key sent in an `X-API-Key` header):
```bash
uip is connectors builder auth set --auth-type customApiKey \
  --api-key-param-name X-API-Key --api-key-location header \
  --validation-vendor-path /me        # provisionAuthValidation is REQUIRED for static auth (no token exchange)
```
What `auth set` writes (the secret config entry, the `type:"value"` mapping parameter, and
`authentication.type`/`typeOauth`) is documented once in [configuration.md](configuration.md)
§customApiKey — this section owns only the CLI flow and flags.

## Re-running auth set

`auth set` is idempotent on identical inputs — re-running with the
same arguments returns `unchanged`. If any existing entry would be
modified by the new inputs, it fails with a `configConflict` error
listing every diff. Use `--force` to apply.

## See also

- [configuration.md](configuration.md) — config keys per auth type
- [system-resources.md](system-resources.md) — auth-validation, token-refresh overrides
- [element-json.md](element-json.md) — what scaffold produces
