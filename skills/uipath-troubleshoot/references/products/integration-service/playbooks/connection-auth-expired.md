---
confidence: high
---

# Connection Authentication Expired

## Context

What this looks like:
- Connection was previously working but now fails
- Ping returns inactive/error status
- OAuth-related errors (401 Unauthorized, token expired, refresh failed)
- Maestro error code 102002 (IntSvcOperationFailed) with auth-related details

What can cause it:
- OAuth access token expired and refresh token is also expired or revoked
- User who created the connection revoked app access in the external service
- External service rotated or invalidated credentials
- Connection was created with short-lived credentials that were not renewed

What to look for:
- Connection was working at some point (rules out misconfiguration)
- Time gap between last successful use and first failure

## Investigation

1. **Read the connection resource file** — if source code is available, find and read the connection JSON (see "Connection Resource File" in [overview.md](../overview.md)) to get the connector name and connection ID
2. `uip is connections ping <connection-id>` — confirm the connection is inactive
3. Check when the connection last worked successfully (from job/instance history in triage evidence)

## Resolution

- Re-authenticate the connection via `uip is connections edit <connection-id>` or through the Integration Service UI
<!--skill-flavor:headless-sign-in-1:start-->
- If the connector uses basic, API key, personal access token or custom auth and `uip is connections edit --help` lists `--field`, re-authenticate with no browser: `uip is connections edit <connection-id> --auth-type <auth-type> --field <key>=env.NAME --output json`. Never write the secret in a command. Never ask the person to paste a secret into chat. The uipath-platform skill has the full steps. If the playbook says the element token cannot be refreshed in place, keep delete and recreate.
<!--skill-flavor:headless-sign-in-1:end-->
- If the external service revoked access, re-authorize the app in the external service settings before re-authenticating
- For connections used in production, consider setting up monitoring or alerts for connection health
