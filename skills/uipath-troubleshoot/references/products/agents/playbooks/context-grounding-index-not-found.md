---
confidence: high
---

# Context Grounding Index Not Found

## Context

What this looks like:
- Agent job faults during a tool call; `uip agent run status <jobId> --output json` shows `Faulted`
- `uip traces spans get <traceId> --output json` contains a span with `SPANTYPE: contextGroundingTool` or `toolCall` whose `ATTRIBUTES.error` contains:
  ```
  ContextGroundingIndex not found Code: AGENT_RUNTIME.UNEXPECTED_ERROR
  ```
- Full error prefix: `Unexpected Error Details: An unexpected error occurred during agent execution, please try again later or contact your Administrator. Error Details: ContextGroundingIndex not found`

What can cause it:
- The grounding index referenced in the agent's configuration was deleted from Data Service after the agent was published
- The agent was published pointing to an index in a different folder or tenant than where it is deployed
- The index name or ID in `agent.json` was changed manually and does not match any existing index
- The index was never created — the agent was published with a placeholder or stale reference

What to look for:
- The `contextGroundingTool` span appears before the `agentRun` fault — the index lookup happens at tool-call time, not at startup
- Whether the agent was recently re-deployed or the index was recently modified

## Investigation

1. Get the job trace ID:

   ```bash
   uip agent run status <jobId> --output json \
     --output-filter "traceId"
   ```

2. Find the `contextGroundingTool` span and extract the index reference:

   ```bash
   uip traces spans get <traceId> --output json \
     --output-filter "spans[?spanType == 'contextGroundingTool'].{name: name, error: attributes.error, attrs: attributes}"
   ```

3. Note the span `name` and any index identifier visible in `attrs` — this is the index the agent tried to resolve.

4. Open the local agent project and list configured context resources:

   ```bash
   uip agent context list --output json
   ```

   Note the index name the agent references.

5. Check whether that index exists in the deployment folder:

   ```bash
   uip context-grounding list --folder-path "<folderPath>" --output json
   ```

   If the index name is absent from the output, the index was deleted or never created. If present, check its status field — anything other than `Active` indicates it is not ready.

## Resolution

**If the index was deleted — re-create it:**

  ```bash
  uip context-grounding create --index-name "<indexName>" --bucket-source "<bucketName>" --folder-path "<folderPath>"
  uip context-grounding ingest --index-name "<indexName>" --folder-path "<folderPath>"
  ```

  No agent republish needed — the runtime resolves by name.

**If the index exists but is in a different folder — re-link the agent:**

  ```bash
  uip agent context remove --name "<oldIndexName>"
  uip agent context add --name "<correctIndexName>" --folder-key "<fk>"
  uip agent publish --output json
  ```

**If the index reference in `agent.json` is stale or wrong:**
- Correct the index name in `agent.json` → `context` block to match an existing index from `uip context-grounding list`
- Republish: `uip agent publish --output json`

**If the index was never created:**

  ```bash
  uip context-grounding create --index-name "<indexName>" --bucket-source "<bucketName>" --folder-path "<folderPath>"
  uip context-grounding ingest --index-name "<indexName>" --folder-path "<folderPath>"
  uip agent context add --name "<indexName>" --folder-key "<fk>"
  uip agent publish --output json
  ```

**If none of the above — the index exists but the runtime cannot resolve it:**
- Capture `uip traces spans get <traceId> --output json` and escalate to the Agents team with the full span output and the index name
