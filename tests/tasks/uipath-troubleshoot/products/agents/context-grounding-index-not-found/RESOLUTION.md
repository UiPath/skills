# Final Resolution

Root Cause: The `SupportAgent` context tool is configured to use the Context
Grounding index `support-kb-prod` in folder `Shared/Agents`, but that index is
not present in the deployment folder. The trace span fails at tool-call time
with `ContextGroundingIndex not found Code: AGENT_RUNTIME.UNEXPECTED_ERROR`.

Evidence:

- `uip traces spans get aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa --output json` returns a
  `contextGroundingTool` span named `SupportKnowledge` with
  `attributes.indexName = support-kb-prod`, `attributes.folderPath =
  Shared/Agents`, and the runtime error.
- `process/SupportSolution/SupportAgent/resources/SupportKnowledge/resource.json`
  has `$resourceType: context`, `contextType: index`, `indexName:
  support-kb-prod`, and `folderPath: Shared/Agents`.
- `uip context-grounding list --folder-path Shared/Agents --output json`
  returns no `support-kb-prod` index.

Immediate fix:

1. Recreate and ingest the missing index, or relink the agent resource to an
   existing active index in the same folder:

   ```bash
   uip context-grounding create --index-name "support-kb-prod" --bucket-source "support-kb-source" --folder-path "Shared/Agents" --output json
   uip context-grounding ingest --index-name "support-kb-prod" --folder-path "Shared/Agents" --output json
   uip context-grounding retrieve --index-name "support-kb-prod" --folder-path "Shared/Agents" --output json
   ```

2. If relinking instead, edit
   `SupportAgent/resources/SupportKnowledge/resource.json` directly and set
   `indexName` and `folderPath` to the existing index. Do not use deprecated
   context-management commands.

3. Refresh and validate the agent, refresh solution resources, then upload the
   solution:

   ```bash
   uip agent refresh "process/SupportSolution/SupportAgent" --output json
   uip agent validate "process/SupportSolution/SupportAgent" --output json
   uip solution resources refresh --output json
   uip solution upload . --output json
   ```

4. For production Orchestrator deployment, promote the solution package:

   ```bash
   uip solution pack . ./dist --version "1.0.1" --output json
   uip solution publish ./dist/SupportSolution.1.0.1.zip --output json
   uip solution deploy run --name SupportAgent-prod --package-name SupportSolution --package-version "1.0.1" --folder-name Agents --parent-folder-path Shared --output json
   ```

Must NOT attribute to: LLM model failure, prompt design, or a generic platform
outage. The failing span and missing index list identify a Context Grounding
resource mismatch. Must NOT use deprecated agent context-management,
standalone publish, or run-status commands.
