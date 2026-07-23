---
confidence: medium
---

# Custom Connector Authentication and Provisioning

Use when a custom connection cannot be created, OAuth authorization loops, token
exchange/refresh fails, static credentials are sent incorrectly, auth fields are
empty, or a token-derived account/base URL was not provisioned.

Never log secrets. Record auth type, failing phase, configuration **key names and
presence** (not values), connector/imported/published version, environment,
request/trace ID, UTC timestamp, and redacted provider response.

## Context

Use [connector-builder.md](./connector-builder.md) to confirm authentication or
provisioning is the earliest failing lifecycle phase.

For a deployed workflow failure, do not enter this playbook from `401`/`403` alone.
First correlate the job/run, activity, published custom connector version,
connection, operation, and provider hop. Use this file only when that evidence
points to the custom authentication/provisioning definition rather than an expired
grant, provider permission, or workflow input.

### What can cause it

- The selected authentication type or grant is unsupported by the target Connector Builder deployment.
- An authorization, token, refresh, revoke, validation, callback, or provider base URL is incorrect or untrusted.
- OAuth client authentication, PKCE, scope, consent, audience, code, or refresh-token handling is incorrect.
- A Basic, API key, PAT, or custom credential is mapped to the wrong header/query location or prefix.
- A credential field is missing, stale, not secret/private, or absent from the imported/published revision.
- Token or profile provisioning failed to persist the account, identity, regional host, or refresh state required at runtime.
- An authentication-definition change invalidated the design-time or published connection binding.

### Supported Authentication Types

The public Connector Builder UI documents these authentication types:

| Builder type | Provider contract | Common configuration mistake |
|---|---|---|
| OAuth 2.0 Authorization Code | User-delegated OAuth | Authorization and token URLs reversed; callback mismatch; missing scopes |
| OAuth 2.0 Authorization Code with PKCE | User-delegated OAuth with code verifier/challenge | Provider/app not configured for the required PKCE method |
| OAuth 2.0 Client Credentials | Machine-to-machine OAuth | Treating it as an interactive user grant; wrong client placement |
| Basic | `Authorization: Basic base64(username:password)` | Supplying an API token in the wrong username/password position |
| API key | Provider-specific header or query parameter | Wrong parameter name/location/prefix |
| Personal Access Token | Usually an Authorization header with a provider scheme | Missing or duplicated `Bearer `, `Token `, or other prefix |
| Custom | One or more custom credential headers/configuration fields | Secret not encrypted/user-supplied; header mapping incomplete |
| No authentication | Public endpoint | Provider actually requires a subscription key or network allow-list |

The on-disk `uip is connectors builder auth set` authoring surface can serialize
additional catalog auth contracts: `oauth2Password`, `oauth1`, `jwtOauth`,
`jwtOauth2`, `awsv4`, `googleServiceAccount`, and `rsaCertificate`. Do not assume
those are supported by the public custom-connector UI or the target tenant merely
because the local CLI accepts the type. Capture the target product/version and
obtain an explicit support contract before using one.

This distinction is important for Resource Owner Password Credentials (ROPC):
`oauth2Password` exists in the on-disk authoring model, but it is not in the public
Connector Builder authentication list. Diagnose it as a deployment/capability
question before treating the connector definition as valid for customers.

## Investigation

### Fast Error Router

| Evidence | Meaning | First corrective check |
|---|---|---|
| Browser never reaches provider | Authorization URL, network, or builder launch | Use the full authorization URL and inspect the redirect target |
| Provider says redirect/callback mismatch | OAuth app redirect URI differs | Compare the exact UiPath callback URI, including path and slash |
| `invalid_client` | Client ID/secret or client-auth placement | Check secret, app/environment, and Basic-header versus request-body behavior |
| `invalid_grant` during code exchange | Code/callback/PKCE/clock/reuse issue | Capture phase; do not retry a one-use authorization code |
| `invalid_scope` | Requested delimiter/name or app allow-list | Compare literal scopes and delimiter with provider docs |
| Token succeeds; validation call is `401` | Token mapping/header/prefix or wrong audience | Inspect emitted Authorization header shape without exposing token |
| Works until token expires | Refresh URL/token/mapping/rotation | Inspect refresh system resource and response persistence |
| API key/PAT is `401` | Wrong name/location/prefix | Compare actual emitted header/query with provider example |
| Connection screen omits a credential | Config field hidden/not user-editable or stale publish | Compare effective imported/published auth configuration |
| Builder connection breaks immediately after an auth edit | Expected invalidation | Create a new connection using the changed auth definition |
| Token succeeds; runtime base URL is empty/wrong | Missing provisioning from token/account lookup | Trace the on-provision/post-token mapping |
| Provider requires a flow absent from public list | Capability mismatch | Confirm supported target surface; redesign or seek platform support |

### Inspect the Effective Definition

From the connector root:

```bash
uip is connectors builder inspect --output json
uip is connectors builder auth get --output json
uip is connectors builder auth system list --output json
uip is connectors builder validate --output json
```

Compare all of:

- `element.json.authentication.type`;
- embedded `elementMetadata.authenticationTypes`;
- auth/configuration entries and whether each is required, encrypted, private, and
  user-visible;
- authorization, token, refresh, revoke, and validation resource URLs;
- global credential header/query mappings;
- lifecycle resources and hooks;
- the definition imported and published in the affected tenant.

Static validation does not prove that the provider accepts the grant. A Builder
test does not prove the same revision was imported and published.

### OAuth Diagnosis

#### Authorization and token URLs

Authentication URL fields do **not** inherit the connector base URL. Configure full
URLs. A relative `/oauth/token` can therefore fail even when normal API resources
work.

For every authorization, token, refresh, revoke, validation, and provisioning URL:

- require HTTPS except a provider-documented local development case;
- parse the URL and exact-match the hostname against the provider's trusted host
  set—never use prefix, substring, or string-contains checks;
- reject user-controlled hosts plus loopback, link-local, private-network, and
  metadata-service destinations;
- revalidate the destination after every redirect and DNS resolution;
- keep client credentials, authorization codes, and tokens out of URLs and logs.

For Authorization Code/PKCE, separate:

1. browser authorization;
2. callback receipt;
3. code-to-token exchange;
4. connection validation/on-provision;
5. first API request;
6. later refresh.

Retain the provider error for the first failing phase.

#### Callback and PKCE

Compare the callback URI as a literal value. Scheme, hostname, path, URL encoding,
environment, and trailing slash all matter.

For PKCE, confirm the provider supports the configured method (normally `S256`) and
that the same authorization transaction supplies the code verifier. A
callback-looking error can still be an invalid/missing PKCE verifier at token
exchange.

For authorization-code flows, also confirm `state` is cryptographically random,
session-bound, verified, and single-use; the authorization code is short-lived,
single-use, and bound to the client, redirect URI, and PKCE verifier. Missing or
mismatched state must fail closed.

#### Client credential placement

Some providers require Client ID/secret as a Base64 Basic header at the token
endpoint; others require request-body fields. Inspect the effective
`oauth.basic.header` behavior and emitted token request metadata. `invalid_client`
is not enough to decide which placement is correct.

#### Scopes

Check:

- exact scope spelling and case;
- separator (space, comma, or provider-specific);
- required versus optional scopes;
- whether the OAuth app was allow-listed for every requested scope;
- whether re-consent is required after a scope change.

A valid token can still be under-scoped for one activity. Route operation `403` by
the provider response rather than recreating the connection blindly.

#### Refresh

If the initial operation works and later calls fail:

1. prove expiry time;
2. inspect refresh URL and system resource;
3. confirm a refresh token was returned/persisted;
4. compare client authentication and request fields;
5. inspect refresh-token rotation/revocation;
6. verify new access/refresh/expiry/base-URL fields were persisted.

Do not classify a refresh-only failure as a callback error.
When the provider supports refresh-token rotation, persist the replacement token
atomically and treat reuse of an invalidated token as grant compromise/revocation,
not as a reason to retry indefinitely.

### Static Credential Diagnosis

#### Basic

Verify the provider wants:

```text
Authorization: Basic base64(<USERNAME>:<PASSWORD>)
```

“Password” may be an API token and “username” may be an email, account ID, or
literal provider value. Follow the provider contract; never infer from labels.

#### API key and PAT

Capture the emitted **shape**, not the secret:

```text
Header: X-API-Key: <REDACTED>
Header: Authorization: Bearer <REDACTED>
Query:  api_key=<REDACTED>
```

Check name, header versus query location, scheme/prefix, whitespace, and whether the
connector added the prefix twice. A provider calling a value an “API key” does not
determine whether Builder should model it as API key or PAT; the wire format does.

#### Custom

For multiple credential headers, prove every field is:

- declared in configuration;
- user-supplied where appropriate;
- secret/encrypted where sensitive;
- mapped to the correct vendor header;
- present in the published revision.

Never hard-code a tenant/user credential into a connector intended for reuse.

### Validation and Provisioning

Static auth types have no token exchange to reject bad credentials early. Configure
a read-only validation probe such as `/me` through the supported authentication
authoring contract.

The probe must be safe and non-mutating. Distinguish:

- authentication succeeds but validation endpoint requires an unrelated scope;
- validation endpoint succeeds but its response mapping fails;
- token response must provide a regional/instance base URL;
- an account/profile lookup must provide an account or user ID.

If a token contains a runtime base URL, persist it per connection through the
supported post-token/on-provision contract. Never bake one customer's regional URL
into the connector definition. Parse and exact-match dynamic scheme/hostname
against the provider's trusted host set before persisting it; never accept an
authentication, token, or base URL supplied by workflow/provider content without
that validation.

Changing the auth type or authentication properties invalidates the design-time
connection. Published consumers may also require a new connection and workflow
rebinding. A stale connection failure after an auth edit is expected until it is
recreated.

## Resolution

Quote one confirmed cause verbatim from **What can cause it**, then correct only
that authentication/provisioning branch. If evidence does not isolate one cause,
stop at the missing discriminator.

- Correct the smallest proven layer: auth type, full URL, callback, PKCE method,
  client placement, scopes, refresh mapping, static header/query mapping, or
  provisioning.
- Use the supported authentication authoring operation; avoid manually assembling
  only part of the authentication block.
- Validate, import, publish a higher version when required, create a fresh
  connection, and bind the consumer to it.
- For a flow outside the public supported list, document the deployment capability
  and security implications before implementing a hook or alternate contract.

Verify the complete lifecycle: connection form, authorization/token or static
validation, provisioning/identity, one authenticated operation, refresh where
applicable, and the same published connector from the intended UiPath surface.

Changing the connector definition, publishing, recreating a connection, or
rebinding a workflow requires explicit approval. A diagnosis should present the
exact field/change and verification path without exposing credentials or silently
performing the mutation.

### Escalation Bundle

Include auth type and target product/deployment, phase, redacted auth/config shape,
full auth hostnames, callback URI/error, PKCE method, scope names/delimiter, client
placement (not secret), validation/provisioning resource, provider status/body,
trace ID/timestamp, local/imported/published versions, and confirmation that the
connection was recreated after auth changes.
