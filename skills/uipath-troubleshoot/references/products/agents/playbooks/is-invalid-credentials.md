---
confidence: high
---

# IS Invalid Credentials (401)

## Context

What this looks like:
- Agent job faults during an IS tool call; `uip agent run status <job-id> --output json` shows `Faulted`
- `uip traces spans get <trace-id> --output json` contains a `toolCall` span whose `ATTRIBUTES.error` contains:
  ```
  {"details":"Invalid Organization or User secret, or invalid Element token provided.","message":"Failed to execute IS call to /curated_soqlQuery: HTTP Status: 401 - Unauthorized","status":400}
  ```
- The `message` field identifies the IS endpoint and connector type — the error is connector-agnostic (Salesforce, Slack, Jira, ServiceNow, and others all produce the same 401 pattern)
- Failure is immediate (first IS call in the run); no successful IS calls precede it

What can cause it:
- IS connection is in the personal workspace or a folder different from where the agent executes — IS cannot resolve the connection at runtime (most common cause)
- OAuth client secret or API key stored in the IS connection was rotated or expired on the external system
- The user account whose delegated credentials are stored in the connection was deactivated or de-provisioned
- An Element token (connector-level auth) was manually revoked
- IS connection was created with sandbox credentials and deployed to production (or vice versa)

What to look for:
- Whether the connection is in the correct folder — `uip is connections list` and check the folder/scope
- Whether `details` says `Invalid Organization or User secret` (connection-level credentials) vs. `invalid Element token` (connector-level) — fix path differs
- Whether other IS connections to the same external system also return 401 (system-wide credential change vs. single-connection issue)

## Investigation

1. Get the job trace ID:

   ```bash
   uip agent run status <job-id> --output json \
     --output-filter "traceId"
   ```

2. Pull the IS tool call span and extract the error:

   ```bash
   uip traces spans get <trace-id> --output json \
     --output-filter "spans[?attributes.error != null].{name: name, spanType: spanType, error: attributes.error}"
   ```

3. Parse the error JSON to identify credential type:

   ```bash
   uip traces spans get <trace-id> --output json \
     --output-filter "spans[?attributes.error != null].attributes.error" \
     | jq -r '.[] | fromjson | .details'
   ```

   - `Invalid Organization or User secret` → connection-level credentials invalid (OAuth client ID/secret or API key)
   - `invalid Element token` → connector-level Element token revoked

4. List IS connections and verify scope — the connection must be in the folder where the agent runs:

   ```bash
   uip is connections list --output json \
     --output-filter "connections[?name == '<connection-name>'].{id: id, name: name, connector: connector, folders: resource.folders}"
   ```

5. Ping to confirm authentication fails:

   ```bash
   uip is connections ping <connection-id> --force-refresh --output json
   ```

## Resolution

**If the connection is in the wrong folder or personal workspace:**

  Move connection to folder where the agent executes, or create a new connection scoped to that folder:

  ```bash
  uip is connections create <connector-key> --output json
  ```

  Update the agent's tool to reference the new connection ID, then republish:

  ```bash
  uip agent publish --output json
  ```

**If `Org/User secret` invalid — re-authenticate with updated credentials:**

  On the external system, regenerate the client secret. Then:

  ```bash
  uip is connections edit <connection-id>
  ```

  Complete OAuth flow with the new credentials.

**If `Element token` invalid — recreate the connection:**

  Element tokens cannot be refreshed in place. Delete the stale connection and create a new one:

  ```bash
  uip is connections delete <connection-id> --output json
  uip is connections create <connector-key> --output json
  ```

  Update the agent's tool to reference the new connection ID, then republish:

  ```bash
  uip agent publish --output json
  ```

**If the user account was deactivated — replace with a service account:**

  ```bash
  uip is connections delete <connection-id> --output json
  uip is connections create <connector-key> --output json
  uip agent publish --output json
  ```

**If sandbox vs. production mismatch — recreate the connection in the correct environment:**

  ```bash
  uip is connections delete <connection-id> --output json
  uip is connections create <connector-key> --output json
  uip agent publish --output json
  ```
