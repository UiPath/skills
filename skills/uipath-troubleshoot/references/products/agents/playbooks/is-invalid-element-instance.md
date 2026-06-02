---
confidence: high
---

# IS Invalid Element Instance (404)

## Context

What this looks like:
- Agent job faults during an IS tool call; `uip agent run status <job-id> --output json` shows `Faulted`
- `uip traces spans get <trace-id> --output json` contains a `toolCall` span whose `ATTRIBUTES.error` contains:
  ```
  {"detail":"Invalid Element Instance Id provided.","message":"Failed to execute IS call to /search: HTTP Status: 404 - Not Found","status":400}
  ```
- The IS endpoint in `message` varies (`/search`, `/records`, `/curated_contact`, etc.) but `detail` is always `Invalid Element Instance Id provided`
- Unlike 401/403 errors, this can fire mid-run — earlier IS calls in the same run may have succeeded

What can cause it:
- The IS connection referenced by the agent tool was deleted after the agent was published
- Agent deployed to a different environment (staging → production) where the source environment's IS connection does not exist — IS does not auto-create connections
- The connection ID in the agent's tool configuration was manually edited to a non-existent value
- UiPath backend tenant migration to a new Azure environment silently invalidated element instance IDs — `uip is connections list` shows the connection as healthy but the underlying instance was invalidated; requires a support ticket

What to look for:
- Whether the agent was recently deployed to a new folder or environment
- Whether an IS administrator deleted the connection for this connector recently
- Whether the error started after a UiPath platform maintenance window — this points to backend migration rather than user action
- The tool name in the faulting span — identifies which IS connection the agent is trying to use

## Investigation

1. Get the job trace ID:

   ```bash
   uip agent run status <job-id> --output json \
     --output-filter "traceId"
   ```

2. Pull the faulting `toolCall` span and note the span name:

   ```bash
   uip traces spans get <trace-id> --output json \
     --output-filter "spans[?attributes.error != null].{name: name, spanType: spanType, error: attributes.error}"
   ```

   The span `name` identifies which tool (and IS connection type) caused the 404.

3. List current IS connections and locate the connection the agent should be using:

   ```bash
   uip is connections list --output json \
     --output-filter "connections[*].{id: id, name: name, connector: connector}"
   ```

   - If no connection matches the connector type → the connection was deleted or never existed in this environment; proceed to Resolution.
   - If a matching connection exists and shows as healthy → suspect backend migration; capture the trace ID and escalate to the Integration Service team.

4. Ping the candidate connection to confirm it is active:

   ```bash
   uip is connections ping <connection-id> --force-refresh --output json
   ```

## Resolution

**If the connection was deleted — recreate it and update the agent:**

  Create a new IS connection:

  ```bash
  uip is connections create <connector-key> --output json
  ```

  Then open the agent in Agent Builder, reselect the IS connection in the tool configuration, and republish. Alternatively, update the connection reference in `agent.json` directly and republish via CLI:

  ```bash
  uip agent validate --output json
  uip agent publish --output json
  ```

**If the connection doesn't exist in the target environment — create it first:**

  IS does not auto-create connections during agent deployment. Create the connection in the target environment:

  ```bash
  uip is connections create <connector-key> --output json
  ```

  Then open the agent in Agent Builder, reselect the IS connection, and republish.

**If the connection appears healthy but the 404 persists — backend migration:**

  Not user-fixable. Open a support ticket with UiPath and provide:
  - The trace ID from step 1
  - The connection ID from `uip is connections list`
  - Confirmation that the error started after a platform maintenance window

  The Integration Service team deploys a server-side fix to restore the element instance binding.
