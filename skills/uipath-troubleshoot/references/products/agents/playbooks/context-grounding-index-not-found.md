---
confidence: high
---

# Context Grounding Index Not Found

## Context

What this looks like:
- A deployed agent job or `uip agent debug` run faults during a context tool call
- `uip traces spans get <trace-id> --output json` contains a span with `SPANTYPE: contextGroundingTool` or `toolCall` whose `ATTRIBUTES.error` contains:
  ```
  ContextGroundingIndex not found Code: AGENT_RUNTIME.UNEXPECTED_ERROR
  ```
- Full error prefix: `Unexpected Error Details: An unexpected error occurred during agent execution, please try again later or contact your Administrator. Error Details: ContextGroundingIndex not found`

What can cause it:
- The grounding index referenced in the agent's context `resource.json` was deleted from Context Grounding after the solution was uploaded or published
- The solution was uploaded or published pointing to an index in a different folder or tenant than where it is deployed
- The `indexName` or `folderPath` in `<AgentName>/resources/<ContextName>/resource.json` does not match any existing index
- The index was never created — the solution was uploaded or published with a placeholder or stale reference

What to look for:
- The `contextGroundingTool` span appears before the `agentRun` fault — the index lookup happens at tool-call time, not at startup
- Whether the agent was recently re-deployed or the index was recently modified
- Authoring reference for the agent-side resource shape: [Context Capability](../../../../../uipath-agents/references/lowcode/capabilities/context/context.md) and [Index Context](../../../../../uipath-agents/references/lowcode/capabilities/context/index.md)

## Investigation

1. Get the spans for the failing run. If you already have a trace ID, use it directly. If you only have an Orchestrator job key, resolve it through traces:

   ```bash
   uip traces spans get <trace-id> --output json

   # or
   uip traces spans get --job-key <job-key> --folder-path "<folder-path>" --output json
   ```

2. Find the `contextGroundingTool` span and extract the index reference:

   ```bash
   uip traces spans get <trace-id> --output json \
     --output-filter "spans[?spanType == 'contextGroundingTool'].{name: name, error: attributes.error, attrs: attributes}"
   ```

3. Note the span `name` and any index identifier visible in `attrs` — this is the index the agent tried to resolve.

4. Open the local agent project and inspect the matching context resource at `<AgentName>/resources/<ContextName>/resource.json`. Confirm:
   - `$resourceType` is `context`
   - `contextType` is `index`
   - `indexName` matches the index from the trace exactly
   - top-level `folderPath` is the literal folder path where the index exists

5. Check whether that index exists in the deployment folder:

   ```bash
   uip context-grounding list --folder-path "<folder-path>" --output json
   ```

   If the index name is absent from the output, the index was deleted or never created. If present, check its status field — anything other than `Active` indicates it is not ready.

## Resolution

**If the index was deleted — re-create it:**

  ```bash
  uip context-grounding create --index-name "<index-name>" --bucket-source "<bucket-name>" --folder-path "<folder-path>" --output json
  uip context-grounding ingest --index-name "<index-name>" --folder-path "<folder-path>" --output json
  uip context-grounding retrieve --index-name "<index-name>" --folder-path "<folder-path>" --output json
  ```

  Ingestion is async: after `ingest`, poll `retrieve` until `last_ingestion_status` is `Successful` before searching — the index is not queryable earlier. If the solution package contains generated index resources, refresh and upload from the solution root so the current index and bucket keys are embedded:

  ```bash
  uip solution resources refresh --output json
  uip solution upload . --output json
  ```

  For a production Orchestrator deployment, use the full solution promotion template in [Project Lifecycle](../../../../../uipath-agents/references/lowcode/project-lifecycle.md#step-5--publish-to-studio-web-or-deploy-to-orchestrator): `uip solution pack . ./dist -v "<version>" --output json`, `uip solution publish ./dist/<SOLUTION_NAME>.<version>.zip --output json`, then `uip solution deploy run --name ... --package-name ... --package-version ... --folder-name ... --parent-folder-path ... --output json`.

**If the index exists but is in a different folder — re-link the agent:**
- Edit `<AgentName>/resources/<ContextName>/resource.json`; set `indexName` to the correct index name and `folderPath` to the literal folder path returned by resource discovery.
- Refresh the agent, then refresh and upload from the solution root:

  ```bash
  uip agent refresh "<AGENT_PROJECT_DIR>" --output json
  uip agent validate "<AGENT_PROJECT_DIR>" --output json
  uip solution resources refresh --output json
  uip solution upload . --output json
  ```

  For a production Orchestrator deployment, use the full solution promotion template in [Project Lifecycle](../../../../../uipath-agents/references/lowcode/project-lifecycle.md#step-5--publish-to-studio-web-or-deploy-to-orchestrator): `uip solution pack . ./dist -v "<version>" --output json`, `uip solution publish ./dist/<SOLUTION_NAME>.<version>.zip --output json`, then `uip solution deploy run --name ... --package-name ... --package-version ... --folder-name ... --parent-folder-path ... --output json`.

**If the index reference in `resource.json` is stale or wrong:**
- Correct the matching context `resource.json` to use the existing index's `indexName` and `folderPath`; do not use the deprecated context-management commands.
- Run the same refresh/validate/resource-refresh/upload sequence above.

**If the index was never created:**

  ```bash
  uip context-grounding create --index-name "<index-name>" --bucket-source "<bucket-name>" --folder-path "<folder-path>" --output json
  uip context-grounding ingest --index-name "<index-name>" --folder-path "<folder-path>" --output json
  uip context-grounding retrieve --index-name "<index-name>" --folder-path "<folder-path>" --output json
  ```

  After ingestion is `Successful`, add `<AgentName>/resources/<ContextName>/resource.json` using the `contextType: "index"` shape from the Index Context reference, then refresh the agent and upload from the solution root:

  ```bash
  uip agent refresh "<AGENT_PROJECT_DIR>" --output json
  uip agent validate "<AGENT_PROJECT_DIR>" --output json
  uip solution resources refresh --output json
  uip solution upload . --output json
  ```

  For a production Orchestrator deployment, use the full solution promotion template in [Project Lifecycle](../../../../../uipath-agents/references/lowcode/project-lifecycle.md#step-5--publish-to-studio-web-or-deploy-to-orchestrator): `uip solution pack . ./dist -v "<version>" --output json`, `uip solution publish ./dist/<SOLUTION_NAME>.<version>.zip --output json`, then `uip solution deploy run --name ... --package-name ... --package-version ... --folder-name ... --parent-folder-path ... --output json`.

**If none of the above — the index exists but the runtime cannot resolve it:**
- Capture `uip traces spans get <trace-id> --output json` and escalate to the Agents team with the full span output and the index name
