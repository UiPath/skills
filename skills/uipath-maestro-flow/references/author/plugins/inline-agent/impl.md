# Inline Agent Node — Implementation

This plugin covers **flow-side** authoring of an inline agent: the `uipath.agent.autonomous` node, its configuration inputs, its resource nodes, edges, and validation. For agent-design guidance (model choice, prompt quality, per-capability discovery of processes / indexes / apps), see the `uipath-agents` skill — `lowcode/capabilities/inline-in-flow/inline-in-flow.md`.

Node type: `uipath.agent.autonomous`. BPMN type and `serviceType` (`Orchestrator.StartInlineAgentJob`) come from the definition in `definitions[]`.

For coded (Python) agents, use the [`agent`](../agent/impl.md) plugin (`uipath.core.agent.{key}`) — inline agents are low-code only.

## The `.flow` Is the Source of Truth

An inline agent is authored **entirely in the `.flow`**:

- The agent node's `inputs` carry the agent: prompts, model, settings, guardrails, output fields.
- Each resource node wired to the agent carries that resource's configuration in its own `inputs`.
- `<FlowProjectDir>/<projectId>/` (`agent.json`, `resources/`, `features/`) is a **generated folder**. `uip agent refresh --inline-in-flow` regenerates it from the `.flow` — the same projection Studio Web runs on every canvas save. Packaging reads that folder, so refresh is what makes the `.flow` edits reach `pack`, `debug`, and `upload`.

### Rules

1. **Edit the `.flow`, never the `<projectId>/` folder.** Refresh overwrites `agent.json` and every `resource.json` / `feature.json` from the nodes, and deletes entries whose node is gone. A hand edit in the folder is lost on the next refresh and is never shown in Studio Web.
2. **Run refresh after every bulk of `.flow` edits, before any `flow validate`, `pack`, `debug`, or `upload`:**

   ```bash
   uip agent refresh "<FlowProjectDir>/<projectId>" --inline-in-flow --output json
   ```

   Read `Data.SyncedFromFlow` (the folder files refresh wrote) in the result. **If the result has no `SyncedFromFlow` key, or carries `FlowShellified`, the installed `uip` predates `.flow`-native inline agents.** An older CLI either packs a stale folder or strips the agent node back to a shell. Stop, upgrade (`npm install -g @uipath/cli@latest`), restore the `.flow` from before that refresh if `FlowShellified` appeared, and re-run refresh.
3. **Opening an existing flow: refresh once before the first edit.** A flow written by an older Studio Web or older CLI is a *legacy shell* — the agent node carries only `source`, `agentInputVariables`, `agentOutputVariables`. Refresh copies the folder's configuration onto the nodes and reports `Data.FlowEmbedded: true`. Re-read the `.flow` after it, then edit the nodes.
4. **Write the agent's prompts on the node as `inputs.systemPrompt` / `inputs.userPrompt`, referencing flow data as `{{ $vars.<nodeId>.output.<field> }}`.** Never write the runtime `{{input.<key>}}` form on the node, and never hand-author `inputSchema`, `contentTokens`, or flattened `<trigger>__output__<var>` keys — refresh and the converter derive all of them from the `$vars` tokens.
5. **Start every resource node's `inputs` from its definition's `inputDefaults`** (copied from `uip maestro flow registry get`), then set `source` and the documented overrides. A node whose inputs fail the agent storage schema makes refresh fail with `AgentRefreshFlowSyncFailed` naming the node — fix those inputs; never work around it in the folder.

## Scaffold the Agent Folder and `projectId`

```bash
uip agent init "<FlowProjectDir>" --inline-in-flow --output json
```

**Record the returned `ProjectId`** — the agent node's `inputs.source`. The command creates `<FlowProjectDir>/<projectId>/` with a placeholder `agent.json`; do not edit it — refresh replaces it from the node. `--model` and `--system-prompt` do not matter here: the node's `inputs.model` / `inputs.systemPrompt` win.

## Registry Validation

Even though `uipath.agent.autonomous` is OOTB, validate it against the registry during Phase 2:

```bash
uip maestro flow registry get uipath.agent.autonomous --output json
```

Confirm:

- Input port: `input`; output ports: `success`, `error`
- Artifact ports: `tool`, `context`, `escalation`, `memory`
- The definition declares `model.source: true`; flow-core hoists that identity field onto the node instance as `inputs.source`
- `model.serviceType` — `Orchestrator.StartInlineAgentJob`; `model.version` — `v2`
- `inputDefinition.required` — `systemPrompt`, `userPrompt`, `model`

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). The inline-agent cluster is not a Flow CLI carve-out: author the agent node, resource nodes, outputs, variables, layout, and edges directly in the `.flow` JSON with `Edit` / `Write`.

### Add the agent node

```json
{
  "id": "autonomousAgent1",
  "type": "uipath.agent.autonomous",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "Invoice Triage Agent" },
  "inputs": {
    "source": "<projectId-uuid>",
    "model": "<MODEL_ID>",
    "mode": "standard",
    "systemPrompt": "You triage supplier invoices. ...",
    "userPrompt": "Invoice number: {{ $vars.start.output.invoiceNumber }}\nAmount: {{ $vars.start.output.amount }}",
    "temperature": 0,
    "maxTokenPerResponse": 16384,
    "maxIterations": 25,
    "guardrails": [],
    "agentInputVariables": [],
    "agentOutputVariables": [
      { "id": "category", "type": "string", "description": "One of: standard, disputed, duplicate", "required": true },
      { "id": "rationale", "type": "string", "description": "One-paragraph justification", "required": true }
    ]
  },
  "outputs": {
    "output": { "type": "object", "description": "Agent response", "source": "=result.response", "var": "output" },
    "error": { "type": "object", "description": "Error information if the node fails", "source": "=Error", "var": "error" }
  }
}
```

Also add:

- A `definitions[]` entry copied verbatim from `uip maestro flow registry get uipath.agent.autonomous --output json`. Set `typeVersion` to the copied definition's exact `version`.
- `variables.nodes[]` entries for `autonomousAgent1.output` and `autonomousAgent1.error` with `binding.nodeId = "autonomousAgent1"` and matching `binding.outputId` values.
- A placeholder `layout.nodes.<agentNodeId>` entry; `flow format` owns the final position.

No `model` block on the node instance — see § What NOT to Do.

### Agent node inputs

Every configuration field the agent has lives on the node. Refresh projects each into the generated `agent.json`:

| Node input | Generated `agent.json` field | Rule |
| --- | --- | --- |
| `source` | `projectId`, `id`, folder name | The `ProjectId` from `uip agent init`. Never change it. |
| `display.label` | `name` | The agent's name. |
| `systemPrompt` | `messages[role=system].content` (+ `contentTokens`) | **Required, non-empty.** A real structured prompt — see the `uipath-agents` skill's `autonomous-agent-prompting-guide.md`. |
| `userPrompt` | `messages[role=user].content` (+ `contentTokens`) | **Required, non-empty.** Carries the per-run task and the flow data. |
| `model` | `settings.model` | **Required.** Discover with `uip agent model list --output json`; never ship `gpt-4o-2024-11-20`. |
| `mode` | `settings.mode` | `standard` (default) or `advanced`. |
| `temperature` | `settings.temperature` | `0` for extraction / classification / judgment. |
| `maxTokenPerResponse` | `settings.maxTokens` | ≤ the model's cap. |
| `maxIterations` | `settings.maxIterations` | Keep `25` when the agent has any tool or context; `≤5` only for a tool-less single shot. |
| `guardrails` | `guardrails` | Same objects as a standalone agent's root `guardrails` array (uipath-agents `capabilities/guardrails/guardrails.md`). |
| `agentOutputVariables` | `outputSchema` | One entry per output field — see § Wiring Agent Output. |
| `agentInputVariables` | `inputSchema` | **Leave `[]`.** Derived from the `$vars` tokens in the prompts and the resource nodes (§ Wiring Flow Data). |

**Every tool and context needs a call cap plus a decide-anyway fallback in `systemPrompt`**, or the agent re-queries until the runtime kills it (`AGENT_RUNTIME.TERMINATION_MAX_ITERATIONS`, incident `170002`). Two sentences per grounding tool:

```text
Call <toolName> at most <N> times (N ≤ 3 for a single decision). After the last call, stop retrieving and decide with the evidence you already have.
If the retrieved content does not cover a detail, say so in <rationaleField>, lower <confidenceField>, and still return every output field. Never end a run without a determination.
```

> **Source of truth.** Prompt skeleton, production-field checklist, model-selection mapping, and the worked example live in the `uipath-agents` guides linked above. The two stop-condition sentences are inlined here because a flow whose agent skips them faults at debug.

### Wire edges

```json
{ "id": "<EDGE_ID>", "sourceNodeId": "<upstreamNodeId>", "sourcePort": "output", "targetNodeId": "autonomousAgent1", "targetPort": "input" }
```

```json
{ "id": "<EDGE_ID>", "sourceNodeId": "autonomousAgent1", "sourcePort": "success", "targetNodeId": "<nextNodeId>", "targetPort": "input" }
```

Resource nodes hang off the agent's artifact ports — see § Adding Resource Nodes.

## Wiring Flow Data into the Agent

Reference flow data directly in the node prompts (and in resource-node argument values) with the canvas expression form:

```text
{{ $vars.<nodeId>.output.<field> }}
```

That token is the whole wiring. On refresh and on pack, the tooling:

1. flattens it to an agent input `<nodeId>__output__<field>` in `agent.json` `inputSchema`, typed from the source variable,
2. rewrites the prompt to the runtime form `{{input.<nodeId>__output__<field>}}` with matching `contentTokens`, and
3. emits the matching `JobArguments` in the BPMN.

Rules:

- **The referenced variable must exist.** A trigger field is read as `$vars.<triggerId>.output.<id>` and must be declared in `variables.globals[]` as a trigger-associated input:

  ```json
  { "id": "invoiceNumber", "direction": "in", "type": "string", "triggerNodeId": "start" }
  ```

  Any other node's output (`$vars.<nodeId>.output.<field>`) needs that node's `variables.nodes[]` entry. Full access rules: [../../../shared/variables-and-expressions.md](../../../shared/variables-and-expressions.md) (§ Input associated with a trigger); declaring mechanics: [../../editing-operations-json.md § Add a workflow variable](../../editing-operations-json.md#add-a-workflow-variable).
- **Declare the source variable's real type.** The derived agent input takes its type from the variable. A list declared `object` faults `AGENT_STARTUP.INPUT_VALIDATION_ERROR` before the model runs (`"Input should be a valid dictionary … input_type=list"`), and both validators pass. Data Service query-entity-records returns an array; a script's output has the shape the script returns. When the shape is unknown, bind a leaf (`{{ $vars.crmLookup1.output[0].accountTier }}`) or read it from one `flow debug` run.
- **Only referenced variables become inputs.** Refresh prunes inputs no prompt or resource node references, so remove a token and its input goes with it.
- **When a connector-trigger field name is unknown at authoring time** (email `subject` / `from` / `body`), write best-guess `$vars` paths, ask the user to confirm before upload, and correct them after the first run.

> **Encoding note.** Refresh writes the flat `__` input encoding. A folder you inherit may carry the newer nested form (`{{input.a.b.c}}`); leave it — refresh rewrites it from the `.flow`.

## Wiring Agent Output

Each `agentOutputVariables[]` entry becomes one `outputSchema` property and surfaces **flat** at `$vars.<agentNodeId>.output.<id>`:

| Where | What | Example |
| --- | --- | --- |
| Agent node `inputs.agentOutputVariables[]` | **One entry per field** — never a single `content` object. `required: true` for fields the prompt always fills; `schema` for `object` / `array`. | `{ "id": "category", "type": "string", "required": true }` |
| End node `outputs.<global>` | Maps each `out` global to the flat field path. | `"category": { "source": "=js:$vars.autonomousAgent1.output.category" }` |

Plus: declare each flow output as a `direction: "out"` global in `variables.globals[]`, and map it on **every reachable End node**.

An object or array field carries its JSON Schema in `schema`:

```json
{ "id": "lineItems", "type": "array", "schema": { "type": "array", "items": { "type": "object", "properties": { "sku": { "type": "string" } } } } }
```

- **Untyped (single string)** — only when no typed output is needed: `agentOutputVariables: [{ "id": "content", "type": "string" }]`, read as `$vars.<nodeId>.output.content`.
- `$vars.<nodeId>.error` — error details if the agent fails.

**Anti-pattern:** `agentOutputVariables: [{ "id": "content", "type": "object" }]` paired with End `=js:$vars.<node>.output.content.<field>`. Typed fields arrive at `output.<field>`; the `.content.` path resolves to undefined → `flow validate` passes, debug Completes, the flow output is **null**.

## Adding Resource Nodes

An inline agent attaches resource nodes to its artifact ports. **Every kind follows one recipe:** discover the node type, copy its definition, add the node with inputs seeded from the definition's `inputDefaults`, wire ONE artifact edge, then refresh.

| Kind | Edge source port | Node type | Needs `uip solution resources refresh`? | Discovery / design (uipath-agents) |
|------|------------------|-----------|------------------------------------------|------------------------------------|
| RPA process tool | `tool` | `uipath.agent.resource.tool.process.<release-key>` | Yes | `lowcode/capabilities/process/process.md` |
| Agent tool | `tool` | `uipath.agent.resource.tool.agent.<release-key>` | Yes | `lowcode/capabilities/process/process.md` |
| API workflow tool | `tool` | `uipath.agent.resource.tool.api.<release-key>` | Yes | `lowcode/capabilities/process/process.md` |
| Process Orchestration tool | `tool` | `uipath.agent.resource.tool.processorchestration.<release-key>` | Yes | `lowcode/capabilities/process/process.md` |
| IS connector tool | `tool` | `uipath.agent.resource.tool.connector.<connector-key>.<operation>` | Yes (connection) | [../connector/impl.md](../connector/impl.md) for `inputs.detail` |
| Built-in tool | `tool` | `uipath.agent.resource.tool.builtin.<tool>` | **No** | `lowcode/capabilities/built-in-tools/built-in-tools.md` |
| MCP server | `tool` | `uipath.agent.resource.tool.mcp.<name>.<key>` | Yes | `lowcode/capabilities/mcp/mcp.md` |
| Context (index / RAG) | `context` | `uipath.agent.resource.context.index.<index-name>.<index-id>` | Yes | `lowcode/capabilities/context/index.md` |
| Escalation (HITL) | `escalation` | `uipath.agent.resource.escalation[.<variant>]` | Yes | `lowcode/capabilities/escalation/escalation.md` |
| Memory space | `memory` | `uipath.agent.resource.memory.<...>` | Yes | `lowcode/capabilities/memory/memory.md` |

### 1. Discover the node type and generate a UUID

Suffix-bearing kinds (process-family tools, connector, MCP, context, memory) — `registry search` by the prefix, then `registry get` the matching `NodeType`. Exact-string kinds (escalation, built-ins) — `registry get` directly.

```bash
uip maestro flow registry search "uipath.agent.resource.tool.process" --output json
uip maestro flow registry get "<NodeType>" --output json

# One resource UUID — the node's inputs.source
RES=$(uuidgen)
```

`<release-key>` is the resource's release-key GUID from `uip solution resources list` (the row's `Key`).

### 2. Add the node

```json
{
  "id": "agentTool1",
  "type": "<NodeType>",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "<ToolName>" },
  "inputs": {
    "...": "every key of the definition's inputDefaults, verbatim",
    "source": "<RES_UUID>",
    "description": "<when the agent should call this tool>"
  }
}
```

Also add:

- The definition copied verbatim from `registry get` into `definitions[]`; set `typeVersion` to its `version`.
- Top-level `bindings[]` entries when the definition declares `model.bindings` — process tools use `model.bindings.resourceKey` and `model.bindings.values[]`; see [editing-operations-json.md — Resource nodes](../../editing-operations-json.md#add-a-node). Built-in tools declare none.
- A placeholder `layout.nodes.<nodeId>` entry.
- ONE artifact edge from the agent's port (per the matrix) to the node's `input` port:

```json
{ "id": "<EDGE_ID>", "sourceNodeId": "autonomousAgent1", "sourcePort": "tool", "targetNodeId": "agentTool1", "targetPort": "input" }
```

`inputs.source` is the resource's identity for its whole life: it names `resources/<RES_UUID>/` in the generated folder. **Exception:** Summarize and BatchTransform built-ins use `inputs.source` for the file-variable binding (`{{ $vars.<nodeId>.output.<file> }}`); they are keyed by node id instead.

### 3. Set the resource inputs

After seeding from `inputDefaults`, set the fields below. Value-source fields — tool arguments, context `query`, built-in `query` / `itemsDescription` — take one of three shapes:

| Mode | Shape | Meaning |
| --- | --- | --- |
| Agent decides | `{ "mode": "prompt", "textValue": "", "promptValue": "<hint for the LLM>", "argumentPath": "" }` | The LLM fills the value; `promptValue` becomes the argument description. |
| Flow data | `{ "mode": "variable", "textValue": "", "promptValue": "", "argumentPath": "$vars.<nodeId>.output.<field>" }` | Bound to a flow variable (becomes an agent input, like a prompt token). |
| Fixed | `{ "mode": "text-builder", "textValue": "<literal>", "promptValue": "", "argumentPath": "" }` | Static value; may contain `{{ $vars.… }}` tokens. |

| Kind | Inputs to set |
| --- | --- |
| Process-family tool | `name`, `description`; `referenceKey` = release key; `folderPath` and `properties: { "processName": "<Name>", "folderPath": "<Folder>" }` = the literal `Name` / `Folder` from `uip solution resources list`; one value-source object per argument (the argument's name is the input key, already seeded by `inputDefaults`); `inputSchema` / `outputSchema` as seeded (replace with `uip solution resources get` schemas when the seed is empty). |
| IS connector tool | `inputs.detail` exactly as the connector plugin's `node configure` flow writes it ([../connector/impl.md](../connector/impl.md)). Refresh generates this tool's `resource.json` from `detail` plus Integration Service metadata. |
| Built-in tool | The definition's `inputDefaults` already hold every field. Set `description`; set `query` / `itemsDescription` / `analysisTaskDescription` value sources as the capability doc directs. |
| MCP server | `name`, `description`, `slug`, `folderPath`, `referenceKey`, `discoveryMode`, `selectedTools` (the tools the agent may call). |
| Context index | Seeded `indexId`, `indexName`, `folderPath`; set `name`, `description`, `retrievalMode` (`semantic` / `deeprag` / `batchtransform`), `query` value source, `resultCount`, `threshold`. |
| Escalation | `name`, `description`, `type` (`app-task` / quick form), `app: { appName, resourceKey, folderName, appVersion, inputSchema, outputSchema }` from app discovery, `recipients`, `outcomeMapping`, `_additionalProps: { taskTitle, priority, labels }`. |
| Memory space | Seeded `memoryId`, `referenceKey`, `memorySpaceName`; set `folderPath` (literal), `name`, `description`, `dynamicFewShotLearning`, `semanticSimilarity`, `kValue`, `searchMode`, `fieldSettings` (`[{ "id": "<input>", "name": "<input>", "weight": 1 }]`; empty → every agent input at weight 1). |

**Guardrails on a tool** are not a tool input. Configure them in the agent node's `inputs.guardrails` with `selector.scopes: ["Tool"]` and `selector.matchNames: ["<tool name>"]`; refresh copies the matching policies into each tool's `resource.json`.

### 4. Refresh, validate, refresh solution resources

```bash
uip agent refresh "<FlowProjectDir>/<projectId>" --inline-in-flow \
  --bindings-target "<FlowProjectDir>/bindings_v2.json" --output json
uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow --output json
uip maestro flow validate <FlowName>.flow --output json
# All kinds EXCEPT built-in tools:
uip solution resources refresh --output json
```

- `Data.SyncedFromFlow` must list `create resources/<RES_UUID>/resource.json` (or `features/…` for memory) the first time a resource node is added.
- `--bindings-target` propagates the agent's bindings (process, connection, index, memorySpace, app) into the flow project's `bindings_v2.json`, which `uip solution resources refresh` scans. Never hand-edit `bindings_v2.json`.
- Built-in tools need no `bindings[]`, no solution-level files, and no `uip solution resources refresh`.

## Refresh and Validate

Run after every bulk of `.flow` edits — in this order:

```bash
# 1. Regenerate the agent folder from the .flow (+ bindings)
uip agent refresh "<FlowProjectDir>/<projectId>" --inline-in-flow \
  --bindings-target "<FlowProjectDir>/bindings_v2.json" --output json

# 2. Check the agent folder (read-only; fails with AgentValidationDrift when the .flow changed since step 1)
uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow --output json

# 3. Validate the flow
uip maestro flow validate <FlowName>.flow --output json
```

Refresh result fields (inline):

| Field | Meaning |
| --- | --- |
| `SyncedFromFlow` | Folder files refresh created / updated / deleted from the `.flow` (`[]` = already in sync). **Absent → CLI too old** (Rule 2). |
| `FlowEmbedded` | `true` when a legacy shell `.flow` was made self-contained from the folder (Rule 3). Re-read the `.flow` before editing. |
| `FlowFile` | The `.flow` that holds the agent node. |
| `ConnectorToolsGenerated` | IS connector tool `resource.json` files generated from `inputs.detail`. |
| `FlowShellified` | **Old CLI** — it stripped the node. Upgrade and restore (Rule 2). |

`flow validate` reads the agent configuration from the node: the registry marks `systemPrompt`, `userPrompt`, and `model` required with `minLength: 1`, so a missing or empty prompt reports `[SCHEMA_ERROR] System prompt is required` (older builds: `[REQUIRED_FIELD] "systemPrompt" is required`). Fix it on the node.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `flow validate`: `[SCHEMA_ERROR] System prompt is required` / `User prompt is required` / `Model is required` | The node's `systemPrompt` / `userPrompt` / `model` is missing or `""` | Write a real value on the node, then refresh. |
| `uip agent refresh`: `AgentRefreshFlowSyncFailed` | A node's inputs fail the agent storage schema, or a resource node has no `definitions[]` entry; `Data.Errors` names the node and field | Fix that node's inputs (re-seed from `inputDefaults`, set the § 3 fields) or add its definition; re-run refresh. Never patch the folder. |
| `uip agent validate`: `AgentValidationDrift` — `agent.json: out of sync with the .flow` | The `.flow` changed after the last refresh, or the folder was hand-edited | Run refresh. |
| Refresh result has no `SyncedFromFlow`, or has `FlowShellified: true` | Installed CLI predates `.flow`-native inline agents | Rule 2 — upgrade `uip`, restore the `.flow` if it was stripped, re-run refresh. |
| Debug faults with `JobArguments {"input":""}` / `AGENT_STARTUP.INPUT_VALIDATION_ERROR` `"Field required"` | A prompt references flow data through a path that is not a declared variable, or uses `{{input.X}}` instead of `{{ $vars.… }}` | Use `{{ $vars.<nodeId>.output.<field> }}` on the node and declare the variable (§ Wiring Flow Data); refresh. |
| Prompt shows a literal `{{input.X}}` or `$vars…` at runtime | Runtime token form written on the node, or refresh skipped before pack | Write `{{ $vars.… }}` on the node; refresh before pack. |
| `AGENT_STARTUP.INPUT_VALIDATION_ERROR` `"Input should be a valid dictionary … input_type=list"` | Source variable declared with the wrong type | Declare the variable's real type (array vs object); refresh. |
| `flow validate` passes, debug Completes, but an `out` global is null | Typed output read with a `.content.` wrapper | § Wiring Agent Output — one `agentOutputVariables[]` entry per field, End maps `output.<field>`. |
| `inputs.source` UUID does not match any subdirectory | Refresh never ran, or `source` was changed | Run refresh — it creates `<FlowProjectDir>/<source>/`. Never rename the folder by hand. |
| `Orchestrator.StartAgentJob` error at runtime | Stale instance `model` fields override the inherited inline-agent definition | Remove the node's instance `model` block; keep the registry definition in `definitions[]`. |
| Studio Web debug: "Could not find process for tool" | Flow project's `bindings_v2.json` lacks the tool's process binding | Refresh with `--bindings-target <FlowProjectDir>/bindings_v2.json`, then `uip solution resources refresh`, then re-upload. |
| Studio Web shows old prompts after upload | Refresh skipped after the last `.flow` edit, so the folder and `.flow` disagree | Refresh, validate, re-upload. |
| `inputs.agentProjectId` unrecognized | Wrong field name | Use `inputs.source`. |
| Inline agent rejected by `uip agent validate` | `entry-points.json` or `project.uiproj` present inside the agent folder | Delete those files — they belong only to standalone agent projects. |

## Repair Recipes

Use direct JSON edits for inline-agent graph repairs. The Flow CLI has no node-update command (see [editing-operations-cli.md § Operations Not Supported by CLI](../../editing-operations-cli.md#operations-not-supported-by-cli)). If a bulk scripted rewrite is explicitly approved, use the `python3` heredoc pattern from [editing-operations-json.md — Edit Tooling](../../editing-operations-json.md#edit-tooling); otherwise apply the same transformations through `Edit` / `Write`.

### Replace a definition entry

Re-fetch from the registry, splice into `definitions[]` matching on `nodeType`, keep the node instance free of a `model` block:

```bash
uip maestro flow registry get uipath.agent.autonomous --output json > /tmp/registry_response.json
python3 - <<'PY'
import json
new_def = json.load(open("/tmp/registry_response.json"))["Data"]["Node"]
flow = json.load(open("<FILE>.flow"))
for i, d in enumerate(flow["definitions"]):
    if d.get("nodeType") == "uipath.agent.autonomous":
        flow["definitions"][i] = new_def
        break
for node in flow["nodes"]:
    t = node.get("type", "")
    if t == "uipath.agent.autonomous" or t.startswith("uipath.agent.resource."):
        model = node.pop("model", None) or {}
        if isinstance(model.get("source"), str):
            node.setdefault("inputs", {})["source"] = model["source"]
json.dump(flow, open("<FILE>.flow", "w"), indent=2)
PY
uip maestro flow validate <FILE>.flow --output json
```

The `model.source` → `inputs.source` move applies to the agent node and every attached resource node — all carry identity at `inputs.source` and never on an instance `model` block.

### Recover a node that `node add` or an old CLI left wrong

- **`node add` wrote placeholder prompts** (`"You are an agentic assistant."`, `"What is the current date?"`, model `gpt-4o-2024-11-20`): replace all three on the node with real values, then refresh.
- **An old CLI shell-ified the node** (`FlowShellified: true`): upgrade `uip`, restore the `.flow` from version control, then refresh. Without a backup, refresh on the new CLI re-embeds the folder's configuration (`FlowEmbedded: true`) — check the prompts afterwards.

## What NOT to Do

- **Do not edit `<FlowProjectDir>/<projectId>/`** — not `agent.json`, not `resources/*/resource.json`, not `features/`. Author on the nodes; refresh regenerates the folder and overwrites hand edits.
- **Do not use `uip agent tool add` or `uip agent memory add` for inline agents** — they write the generated folder, and refresh deletes an entry that has no node. Add a resource node instead.
- **Do not use Flow CLI `node add`, `edge add`, or `variable` commands for inline-agent graph edits** — author with `Edit` / `Write`. On `uipath.agent.autonomous`, `node add` writes placeholder prompts and `gpt-4o-2024-11-20` from `inputDefaults`. This rule scopes to `uipath.agent.autonomous`; the inline conversational agent's recipe uses `node add` ([conversational-agent/impl.md § Node JSON](../conversational-agent/impl.md#node-json)).
- **Do not write `{{input.<key>}}`, `inputSchema`, `contentTokens`, or flattened `__` keys** on the node — write `{{ $vars.… }}`; refresh derives the rest.
- **Do not leave `systemPrompt`, `userPrompt`, or `model` empty** to "let the folder supply them" — the `.flow` is the source; an empty prompt fails `flow validate`.
- **Do not put a `model` block on any inline-agent node instance** — the node inherits serviceType/version/context from `definitions[]`; identity lives at `inputs.source`.
- **Do not use `model.agentProjectId`, `inputs.agentProjectId`, or `model.source`** on the agent node or any resource node.
- **Do not create `entry-points.json` or `project.uiproj` inside the agent folder** — they belong only to standalone agent projects.
- **Do not skip refresh before `flow validate`, `pack`, `debug`, or `upload`** — packaging reads the generated folder, so a skipped refresh ships the previous agent.
