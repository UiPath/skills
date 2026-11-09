# Inline Agent

*Exact signatures, fields, and defaults: `inlineAgent()`.*

An inline agent is defined inside this Flow project and may connect tenant context, callable tools, and human escalation resources.

Signature: `inlineAgent({ model, systemPrompt, userPrompt, inputs?, returns?, source?, temperature?, maxTokenPerResponse?, modelMaxTokens?, maxIterations?, mode?, guardrails?, context?, tools?, escalation? })`.

```ts
.step('triage', inlineAgent({ model: 'gpt-5.4',
  systemPrompt: 'Return a result conforming to the output schema. category: billing | technical | account.',
  userPrompt: 'Classify {{input.body}}', inputs: { body: input('body') },
  returns: { category: 'string' } }))
```

`tools` also takes `mcp`, `a2a`, `clientside`, `httpRequest` and `function` kinds, each with its own identity ([agent-resources.md](agent-resources.md#tool-kinds)); attach memory with the CLI, not `inlineAgent` ([agent-resources.md](agent-resources.md#memory)); `escalation: { variant: 'quick-form' }` creates an inline form; `mode: 'advanced'` selects the Advanced harness.

## Model and answer judgment

Select a tenant-available model (`uip agent model list`) and make the decision and answer contract explicit. Static checks establish wiring and output shape, not semantic quality.

`returns` is the typed answer contract. Describe every field (for example, “Return a result conforming to the output schema. `<field>`: `<how to fill it>`”); never request JSON text, which packs the answer into one string field.

## Context grounding

Context signature: `{ name, id, folderPath?, folderKey?, query?, retrievalMode?, resultCount?, threshold?, fileExtension? }`.

Resolve the index from the tenant.
Know the name: use `solution resources list` below.
<!--skill-flavor:cg-discover:start-->
Discovering what exists: use the `uip context-grounding` bridge, which reports every index with its folder.
<!--skill-flavor:cg-discover:end-->

Do not use `uip maestro flow registry` (node manifests), `uip maestro registry` (connector library), or `uip or folders list`.

```bash
uip solution resources list --kind Index --source remote --search "<index-name>" --output json
```

Map `Key` → `id`, `Name` → `name`, `Folder` → `folderPath`, and `FolderKey` → `folderKey`. `id` is the index GUID (`Key`), the resource node type's tail. Blank or non-GUID `id` makes `check` report `FLOW_AGENT_CONTEXT_NO_ID`; `compile` also refuses it (SDK older than 6.88.2: `AGENT_CONTEXT_NO_ID`). Provide `folderPath`: the resource file has no index id, so type plus folder locate the index. Decompile entries may include `nodeId` / `source` / `label`; see [brownfield.md](brownfield.md), and omit them in new flows.

Local execution has no semantic retrieval service: answers remain ungrounded even with resource wiring. Platform evidence must establish that the intended index was used and retrieved knowledge influenced the answer.

<!--skill-flavor:cg-bridge:start-->
The `uip context-grounding` bridge runs in the project's Python environment.
Activate the existing environment and run setup once before list/search; setup
is the command itself, not a `setup --help` probe:

```bash
source .venv/bin/activate
uip context-grounding setup
uip context-grounding list --folder-path "<folder-path>" --format json
uip context-grounding search \
  --index-name "<index-name>" --query "<one bounded evidence query>" \
  --folder-path "<folder-path>" --limit 5 --format json
```

Use `--folder-key` instead of `--folder-path` when that is the known identity. The delegated command uses `--format json`, not the outer CLI's `--output json`. One search answering the grounding claim is enough; do not repeat paraphrases solely for confidence.
<!--skill-flavor:cg-bridge:end-->

## Tools

Tool signatures:

- `{ kind: 'builtin', tool: 'analyzefiles' | 'summarize' | 'batchtransform', ... }`
- `{ kind: 'connector', connector, operation, connection, folder, version?, object?, name?, description? }`
- `{ kind: 'process' | 'agent' | 'api' | 'flow' | 'maestro', key, name, folderPath, inputs?, returns? }`
- `{ kind: 'ixp', projectId, name, description?, versionTag?, attachment? }`

For a sibling project, a `process` / `agent` / `api` / `flow` / `maestro` / `function` tool takes `key` = `resource.key` from `resources/solution_folder/process/*/<Project>.json` (the tail of its `uip maestro flow registry list --local` tool type) and `folderPath: 'solution_folder'`. A `ProcessOrchestration` project (folder `processOrchestration`, tool type `…tool.processorchestration.*`) is `kind: 'maestro'`, never `'process'`; otherwise use the tool type's namespace. Tools have no `location` or `projectId`.

Declare tools on `inlineAgent` so compile writes `resource.json`; nodes created with `uip maestro flow nodes create` get none.

Connector tools require `connection` and `folder`, with `bindings.json` labels resolved like `connector()`'s (see [bindings.md](bindings.md)). Missing either produces `FLOW_AGENT_TOOL_CONNECTOR_NO_CONNECTION` from `check` (`INLINE_AGENT_TOOL_CONNECTOR_NO_CONNECTION` on an SDK older than 6.88.2). `prepare` does not read source labels, so pass them:

`uip maestro registry prepare <connector-key> --action <operation> --bind-connection <connection> --bind-folder <folder>`

This finds the connection and writes both entries under the tool's labels. `description` overrides model-facing tool text; otherwise it defaults to the library operation description.

```ts
tools: [{ kind: 'connector', connector: 'uipath-uipath-airdk', operation: 'web-search',
  connection: 'genai', folder: 'shared',   // bindings.json labels
}]
```

The model invokes tools, not a control-flow edge. Local execution skips tool resources, proving wiring but not invocation; live evidence needs a tool-specific side effect or returned witness.

## Human escalation

Escalation signature: `{ name, description?, app: { key, name, folderPath?, inputs?, outputs? }, recipients?, outcomes?, taskTitle?, priority?, labels? }`.

Whether and when to escalate is model judgment; completion also requires a deployed app and human. Local execution proves only resource and contract wiring. Live evidence must show the task, reviewer outcome, and resumed agent behavior.

## Live-evidence limit

Headless local live mode calls a real model but substitutes a reachable model and remains ungrounded; it has no tenant tool loop or human escalation. Treat it as evidence that a real prompt produced the declared shape. Product debug is evidence for the configured model and cloud resources.

Compile emits the node plus stable `<source>/agent.json`. Prompt variables use `{{input.<name>}}`; `inputs` binds those names to flow references and `returns` declares the agent output.

## Guardrails and harness mode

`guardrails` is Agent Builder's own array, carried on the node and sidecar. Each rail is `$guardrailType: 'custom'` (with `rules`) or `'builtInValidator'` (with `validatorType` + `validatorParameters`), plus `id`, `name`, `selector: { scopes: ['Agent'|'Llm'|'Tool'] }`, an `action` (`block` with a reason, `filter` over fields, or `log` with a severity), and `enabledForEvals`. Custom rules are `$ruleType: 'word' | 'number' | 'boolean'` over a field selector, or `'always'`. A rail with no scopes or an empty rules array can never fire; `check` rejects both.

```ts
guardrails: [{ id: 'no-pii', $guardrailType: 'custom', name: 'Block PII', selector: { scopes: ['Agent'] },
  enabledForEvals: true, action: { $actionType: 'block', reason: 'PII detected' },
  rules: [{ $ruleType: 'always', applyTo: 'inputAndOutput' }] }]
```

File-capable built-in validators require an extra `validatorParameters` entry `{ $parameterType: 'enum', id: 'detectionScope', value: 'Text' | 'Files' | 'Both' }`, determining whether the validator reads text, run files, or both. Inline agents inherit standalone low-code behavior unchanged; the sidecar is a projected `agent.json`. Scope coverage, caps and recipes live in the low-code guardrails files guide of [/uipath:uipath-agents](/uipath:uipath-agents).

`mode: 'standard' | 'advanced'` picks the harness; naming it selects the node's 1.3 definition (omitting it keeps 1.2 byte-identically) and sets the sidecar's `settings.mode`. Guardrail and harness behavior is runtime-side; offline rungs prove emitted shape only.