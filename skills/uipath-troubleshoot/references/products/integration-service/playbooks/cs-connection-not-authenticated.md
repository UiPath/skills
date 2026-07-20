---
confidence: high
---

# Connection Service — Connection Not in Authorized State (CNS1008, CNS1021, CNS1061)

> **Fault bucket: 👤 A — customer-resolvable.** The connection exists and the caller can see it, but it is **not in a usable authentication state**: its OAuth token expired or was revoked, it was created but never authenticated, or an operation was attempted that its auth type cannot serve. The fix is re-authenticating (or correctly configuring) the connection. This is the service-API sibling of the Maestro-surfaced [connection-auth-expired.md](./connection-auth-expired.md) — use that playbook's token-expiry investigation flow; this page adds the CNS code semantics.

## Context

What this looks like:
- HTTP `400` from Connection Service when a caller asks for the connection's access token or tries to use/enable something bound to it
- Error body `{ "code": "CNS1008", "message": "…", "traceId": "…" }` — the `CNS1008` message often embeds the raw provider auth-failure JSON
- Runtime symptom: activities that previously worked start failing at the token step; enabling a trigger fails with "State update of trigger … is not allowed"

| Code | Name | Exact meaning | HTTP |
|------|------|---------------|:---:|
| `CNS1008` | ConnectionStatusInvalid | Token acquisition failed because the connection is not in the *authorized* state — expired/revoked OAuth grant, failed refresh, or never authenticated | 400 |
| `CNS1021` | ConnectionAuthTypeUnsupported | The connection's authentication type cannot serve an access-token request (e.g. a non-OAuth connection asked for an OAuth token) | 400 |
| `CNS1061` | TriggerOnInvalidConnectionError | Attempt to enable/update a **trigger** whose underlying connection is not active — the trigger is fine; the connection is the problem | 400 |

What can cause it:
- The third-party provider expired or revoked the refresh token (password change, admin revocation, provider-side session policies)
- The connection was created via a Solutions package with "authenticate after deployment" and nobody authenticated it yet
- A bring-your-own-app OAuth configuration changed (client secret rotated) so refresh now fails
- `CNS1021`: an automation or API client requests a bearer token from a connection using PAT/basic/API-key auth — a design mismatch, not a degradation

What to look for:
- The connection's status in the Integration Service UI (Failed / needs attention vs Connected)
- Whether the failure started at a point in time after working fine (token expiry/revocation) vs never worked (unauthenticated shell / wrong auth type)
- For `CNS1061`: which connection the trigger is bound to — the error names the trigger, but the connection is what needs fixing

## Investigation

1. **Ping the connection** (`uip is connections ping <connection-id>` or the UI's check) — a failed ping with `CNS1008` confirms the auth state; no need to dig further before re-authenticating.
2. **Check the connection's state and auth type** in the tenant's Integration Service → Connections page. A "Failed" state with a re-authenticate action is the expected signature for `CNS1008`.
3. **For `CNS1061`**: resolve the trigger → connection binding first (the trigger detail page names the connection), then treat it as `CNS1008` on that connection.
4. **For `CNS1021`**: this is not transient and re-auth won't change it — identify *what is requesting a token* from a connection whose auth type doesn't issue tokens. Usually a wrong connection was selected for an activity/integration that requires OAuth.
5. **If re-auth fails immediately again**, follow [connection-auth-expired.md](./connection-auth-expired.md) — provider-side app configuration (redirect URI, rotated secret, revoked app consent) is the usual cause; for bring-your-own-app setups verify the OAuth app config matches on both authorize and token-exchange legs.

## Resolution

- **`CNS1008`:** re-authenticate the connection from the Integration Service UI (or complete first-time authentication for shell connections deployed via Solutions). Then re-run the failed job / re-enable the trigger.
- **`CNS1061`:** re-authenticate (or replace) the underlying connection, then retry the trigger state change. Enabling the trigger before fixing the connection will keep failing.
- **`CNS1021`:** switch the consumer to a connection whose auth type supports the operation (typically OAuth), or recreate the connection with the correct authentication type. There is nothing to "repair" on the existing connection.
- **Escalate only** if a freshly re-authenticated, Connected-state connection still returns `CNS1008` on token acquisition — that points at a token-persistence/refresh defect on the service side; provide the `traceId` and connection ID.
