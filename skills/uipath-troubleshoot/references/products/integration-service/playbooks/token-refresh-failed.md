---
confidence: high
---

# Token Refresh Failed (DAP-GE-3004)

> **Fault bucket: 👤 A — Customer-resolvable.** Expired/revoked credentials on the customer's connection. Lead with: "This is a credential issue on your side — re-authenticate the connection." See [dap-error-codes-reference.md](../dap-error-codes-reference.md#fault-ownership--the-two-bucket-decision).

## Context

What this looks like:
- Error code `DAP-GE-3004` (FailedToGetAccessToken)
- IS could not obtain a valid OAuth access token to make the call — fails before the provider request
- Maps to the `OAuthTokenRefresh-failures` SRE alert
- May co-occur with `DAP-RT-1101` + `ProviderErrorCode: 401` (provider rejected the stale token)

What can cause it:
- OAuth access token expired and the refresh token is also expired or revoked
- The user who created the connection revoked app access in the external service
- External service rotated or invalidated credentials
- Connector auth misconfiguration (wrong client credentials, changed redirect/scope)

What to look for:
- `ConnectionId` in the customEvent — identifies the failing connection
- Connection was working previously (rules out first-time misconfiguration)
- Time gap between last successful run and first failure (typical of refresh-token expiry)

> This is the IS-native (`DAP-GE-3004`) view of the same root cause as the Maestro-surfaced [connection-auth-expired.md](./connection-auth-expired.md). Prefer this playbook when the DAP code is present.

## Investigation

1. **Read the connection resource file** — if source code is available, find the connection JSON (see "Connection Resource File" in [overview.md](../overview.md)) to get the connector name and connection ID.
2. `uip is connections ping <connection-id>` — confirm the connection returns inactive / error status.
3. Check when the connection last worked successfully (from job/instance history in triage evidence) to confirm refresh-token expiry vs config error.

## Resolution

- Re-authenticate the connection via `uip is connections edit <connection-id>` or the Integration Service UI.
- If the external service revoked app access, re-authorize the app in the external service settings **before** re-authenticating.
- If the connector's client credentials/scope changed, fix the connector auth configuration, then re-authenticate.
- For production connections, set up health monitoring so token expiry is caught before a run fails.
