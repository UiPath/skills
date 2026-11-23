# Inline Agent

*Exact signatures, fields, and defaults: `inlineAgent()`.*

An inline agent is defined in this Flow project and may use tenant context, callable tools, and human escalation.

Signature: `inlineAgent({ model, systemPrompt, userPrompt, inputs?, returns?, source?, temperature?, maxTokenPerResponse?, modelMaxTokens?, maxIterations?, mode?, guardrails?, context?, tools?, escalation? })`.

## At a glance

Define an autonomous agent with optional resources.

```ts
.step('triage', inlineAgent({ model: 'gpt-5.4', systemPrompt: 'Return a result conforming to the output schema. category: billing | technical | account.',
  userPrompt: 'Classify {{input.body}}', inputs: { body: input('body') },
  returns: { category: 'string' },
  guardrails: [{ id: 'no-pii', $guardrailType: 'custom', name: 'Block PII', selector: { scopes: ['Agent'] },
    enabledForEvals: true, action: { $actionType: 'block', reason: 'PII detected' },
    rules: [{ $ruleType: 'always', applyTo: 'inputAndOutput' }] }] }))
```

`tools` also accepts `mcp`, `a2a`, `clientside`, `httpRequest`, and `function` kinds ([agent-resources.md](agent-resources.md#tool-kinds)); attach memory with the CLI, not `inlineAgent` ([agent-resources.md](agent-resources.md#memory)); use `escalation` with `variant: 'quick-form'` for an inline form. Set `mode: 'advanced'` to select the Advanced harness.

## Model and answer judgment

`returns` is the typed answer contract: prompts must make the requested decision explicit and describe every field ("Return a result conforming to the output schema. `<field>`: `<how to fill it>`.") and must not request JSON text, which makes the model pack its whole answer into one string field. Select a tenant-available model; run `uip agent model list`. Static checks validate wiring and output shape, not semantic quality.

## Context grounding

Context signature: `{ name, id, folderPath?, folderKey?, query?, retrievalMode?, resultCount?, threshold?, fileExtension? }`.

Resolve the tenant index. If you know its name, use `solution resources list` below.
<!--skill-flavor:cg-discover:start-->
Discover what exists with the `uip context-grounding` bridge, which reports every index with its folder.
<!--skill-flavor:cg-discover:end-->
To resolve an index, do not use `uip maestro flow registry` (node manifests), `uip maestro registry` (connector library), or `uip or folders list`.

```bash
uip solution resources list --kind Index --source remote --search "<index-name>" --output json
```

Map `Key` → `id`, `Name` → `name`, `Folder` → `folderPath`, and `FolderKey` → `folderKey`. `id` is the index GUID (`Key`), the resource node type's tail. `check` reports `FLOW_AGENT_CONTEXT_NO_ID` for blank or non-GUID `id`, and `compile` refuses it too (SDKs older than 6.88.2 spell it `AGENT_CONTEXT_NO_ID`). Give `folderPath`: the resource file has no index id, so type plus folder locates the index. Decompile entries may include `nodeId` / `source` / `label`; see [brownfield.md](brownfield.md). Omit them in new flows.

Local execution has no semantic retrieval service: answers are ungrounded even when wiring exists. Platform evidence must establish that the intended index was used and its retrieved knowledge influenced the answer.

<!--skill-flavor:cg-bridge:start-->
Activate the existing Python environment and run setup once before list/search; setup is the command itself, not a `setup --help` probe:

```bash
source .venv/bin/activate
uip context-grounding setup
uip context-grounding list --folder-path "<folder-path>" --format json
uip context-grounding search \
  --index-name "<index-name>" --query "<one bounded evidence query>" \
  --folder-path "<folder-path>" --limit 5 --format json
```

Use `--folder-key` instead of `--folder-path` when that is the known identity. The delegated command uses `--format json`, not the outer CLI's `--output json` spelling. One search answering the grounding claim is enough; do not repeat paraphrases solely for confidence.
<!--skill-flavor:cg-bridge:end-->

## Tools

Tool signatures:

- `{ kind: 'builtin', tool: 'analyzefiles' | 'summarize' | 'batchtransform', ... }`
- `{ kind: 'connector', connector, operation, connection, folder, version?, object?, name?, description? }`
- `{ kind: 'process' | 'agent' | 'api' | 'flow' | 'maestro', key, name, folderPath, inputs?, returns? }`
- `{ kind: 'ixp', projectId, name, description?, versionTag?, attachment? }`

For a sibling project, a `process` / `agent` / `api` / `flow` / `maestro` / `function` tool uses `key` = `resource.key` from `resources/solution_folder/process/*/<Project>.json` (the tail of its `uip maestro flow registry list --local` tool type) and `folderPath: 'solution_folder'`. A `ProcessOrchestration` project (folder `processOrchestration`, tool type `…tool.processorchestration.*`) is `kind: 'maestro'`, never `'process'`; every other kind is its tool type's namespace. A tool has no `location` or `projectId`. Declare it on `inlineAgent` so compile writes its `resource.json`.

A connector tool needs `connection` and `folder`, with `bindings.json` labels resolved like `connector()`'s (see [bindings.md](bindings.md)). Missing either produces `FLOW_AGENT_TOOL_CONNECTOR_NO_CONNECTION` from `check` (`INLINE_AGENT_TOOL_CONNECTOR_NO_CONNECTION` on SDKs older than 6.88.2). Write the
labels on the tool, then run
`uip maestro registry prepare <connector-key> --action <operation>`: it reads the
tool's `connection` / `folder` from the source and writes both entries under them.

A connector tool's `description` overrides the text the model is told the tool does; otherwise the library's operation description is used.

A tool is invoked by the model, not by a control-flow edge. Local execution skips tool resources, proving wiring but not invocation. A live test needs a tool-specific side effect or returned witness.

## Human escalation

Escalation signature: `{ name, description?, app: { key, name, folderPath?, inputs?, outputs? }, recipients?, outcomes?, taskTitle?, priority?, labels? }`.

Whether and when to escalate is model judgment; completion also requires a deployed app and a human. Local execution proves only resource and contract wiring. Live evidence must show the task, reviewer outcome, and resumed-agent behavior.

## Live-evidence limit

Headless local live mode calls a real model but substitutes a reachable model and remains ungrounded: it has no tenant tool loop or human escalation. Treat it as evidence that a real prompt produced the declared shape. Product debug is evidence for the configured model and cloud resources.

Compile emits the node plus a stable `<source>/agent.json` sidecar. Prompt variables use `{{input.<name>}}`; `inputs` binds those names to flow references and `returns` declares what the agent hands back.

## Guardrails and harness mode

`guardrails` is Agent Builder's own array, carried on the node and sidecar. Each rail is `$guardrailType: 'custom'` (with `rules`) or `'builtInValidator'` (with `validatorType` + `validatorParameters`), plus `id`, `name`, `selector: { scopes: ['Agent'|'Llm'|'Tool'] }`, an `action` (`block` with a reason, `filter` over fields, or `log` with a severity), and `enabledForEvals`.

Custom rules are `$ruleType: 'word' | 'number' | 'boolean'` over a field selector, or `'always'`. A rail without scopes or with an empty rules array can never fire; `check` rejects both. File-capable built-in validators take an extra `validatorParameters` entry `{ $parameterType: 'enum', id: 'detectionScope', value: 'Text' | 'Files' | 'Both' }`, determining whether the validator reads text, run files, or both. Inline agents inherit standalone low-code behavior unchanged; the sidecar is a projected `agent.json`. Scope coverage, caps, and recipes live in the low-code guardrails files guide of [/uipath:uipath-agents](/uipath:uipath-agents).

`mode: 'standard' | 'advanced'` selects the harness; naming it selects the node's 1.3 definition (omitting it keeps 1.2 byte-identically) and sets the sidecar's `settings.mode`. Guardrail/harness behavior is runtime-side; offline rungs prove only emitted shape.
