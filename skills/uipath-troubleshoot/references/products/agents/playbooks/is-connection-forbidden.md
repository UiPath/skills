---
confidence: medium
---

# IS Connection Forbidden (403)

## Context

What this looks like:
- Agent job faults during an IS tool call; `uip agent run status <job-id> --output json` shows `Faulted`
- `uip traces spans get <trace-id> --output json` contains a `toolCall` span whose `ATTRIBUTES.error` contains:
  ```
  Your connection has been temporarily disabled due to multiple unsuccessful attempts. To restore access, please reauthenticate
  ```
  or `Failed to execute IS Event call: HTTP Status: 403 - Forbidden`
- Error appears on first IS call in the run; no successful IS calls precede it
- Applies to OAuth2 authorization code connections only — client credentials flows are not affected by this lockout mechanism

What can cause it:
- IS locked out the connection after consecutive authentication failures (protective lockout)
- IS poller or ping infrastructure failure cascaded into a lockout — the lockout counter increments on any repeated ping failure, even when OAuth credentials are valid
- Connected app credentials (OAuth client secret, API key) were rotated on the external system after the connection was created
- An IS administrator manually disabled the connection
- Concurrent agent runs sharing the same IS connection triggered enough failures simultaneously to trip the lockout

What to look for:
- Whether the error says "temporarily disabled due to multiple unsuccessful attempts" (lockout) vs. a generic 403 (external system permissions changed)
- Whether other automations using the same IS connection started failing at the same time — shared lockout vs. single-agent issue
- The connection name or ID in the span — needed to target the re-authentication command
- The IS connection list may show the connection as "Connected" even when it is locked out — `uip is connections ping` is required to confirm the actual state

## Investigation

1. Get the job trace ID:

   ```bash
   uip agent run status <job-id> --output json \
     --output-filter "traceId"
   ```

2. Find the faulting `toolCall` span and extract IS connection details:

   ```bash
   uip traces spans get <trace-id> --output json \
     --output-filter "spans[?attributes.error != null].{name: name, spanType: spanType, error: attributes.error}"
   ```

   Note the connection name or ID from the error text or span name.

3. List IS connections to identify the connection:

   ```bash
   uip is connections list --output json \
     --output-filter "connections[?name == '<connection-name>'].{id: id, name: name, connector: connector}"
   ```

4. Ping the connection to confirm lockout:

   ```bash
   uip is connections ping <connection-id> --force-refresh --output json
   ```

   A failed ping or authentication error confirms the lockout.

## Resolution

**If locked out — re-authenticate:**

  ```bash
  uip is connections edit <connection-id>
  ```

  Completes OAuth re-authentication in the browser, lifting the lockout.

**If credentials were rotated on the external system — update credentials and re-authenticate:**

  On the external system (e.g., Salesforce > Connected Apps), regenerate the client secret. Then:

  ```bash
  uip is connections edit <connection-id>
  ```

  Complete the OAuth flow with the new credentials.

**If manually disabled by an administrator:**
- Coordinate with the admin — re-authenticate only after root cause of repeated failures is resolved
- Once approved: `uip is connections edit <connection-id>`

**If lockout recurs within hours after re-authentication — escalate:**

  Recurring lockouts indicate an underlying connector-level issue (misconfigured OAuth scopes, provider-side rate restriction, or external system instability) that re-auth temporarily masks. Capture the connection ID and the recurrence pattern, then escalate to the IS team — `uip is connections edit` alone will not resolve this.
