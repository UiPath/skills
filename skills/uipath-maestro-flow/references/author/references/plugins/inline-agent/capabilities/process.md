# Process Tool Capability

Tools that call a runnable process — RPA workflows, agents, API workflows, or agentic processes (process orchestration). Each tool is a **node in the `.flow` file** wired to the agent node's `tool` handle; the full tool config lives in the tool node's `inputs`. No `resource.json` is authored — the sidecar artifact derives from the node ([impl.md § Derived Sidecar](../impl.md#10-derived-sidecar--reference)).

For IS connector tools and built-in tools (separate capabilities), see [impl.md § Resource Nodes](../impl.md#7-resource-nodes) — their capability docs land per roadmap milestone.

## When to Use

- Agent needs to invoke an RPA process, another agent, an API workflow, or an agentic process
- Target lives in the **same solution** (`Source: "Local"` from discovery) or is **already deployed in Orchestrator** (`Source: "Remote"`)

## Node Type and Subtypes

Node type pattern: `uipath.agent.resource.tool.<family>.<key>` — `<key>` is the target's resource key (a UUID). **Never construct the type string by hand — discover it** (§ Discovery); the registry mints one node type per callable target.

| `<family>` segment | Calls | Derived resource `type` | serviceType (from manifest `model`) |
|---|---|---|---|
| `process` | RPA process (XAML) | `process` | `Orchestrator.StartJob` |
| `agent` | Low-code / coded agent | `agent` | `Orchestrator.StartAgentJob` |
| `api` | API workflow | `api` | `Orchestrator.ExecuteApiWorkflowAsync` |
| `processorchestration` | Agentic process / process orchestration | `processOrchestration` | `Orchestrator.StartAgenticProcess` |

> Segment is all-lowercase (`processorchestration`); the derived resource `type` is camelCase (`processOrchestration`). There is no `rpa` segment on the registry — RPA processes surface as `process`.

**Local and external targets follow the same authoring flow.** Same node shape, same `definitions[]` requirement, same edge. Differences: which registry flag finds the node type (`--local` vs default), and the `properties.folderPath` value (`"solution_folder"` vs literal Orchestrator folder). The derived `location` field is projection-owned — never authored.

## Discovery

Three `uip` calls — identity from `resources list`, node type from `registry search`, manifest from `registry get`.

### 1. Find the process

**Local (in-solution):**

```bash
uip solution resources list --source local --output json
```

**Remote (Orchestrator / RCS):**

```bash
uip solution resources list --source remote --kind Process --search "<NAME>" --output json
```

> **`--kind` and `--search` only work with `--source remote`.** With `--source local` or `--source all` (default), omit both — list everything and filter `.Data[]` client-side by `Kind` and `Name`.

> **`--kind Process` covers all four families.** Agents, API workflows, and agentic processes list as `Kind: "Process"` too — the family is in the `Type` field, not `Kind`. `--kind Agent` returns an empty list.

Response wrapper: `{Result, Code: "ResourceList", Data: [...]}` — parse `.Data[]`. Per entry:

| Field | Use as |
|-------|--------|
| `Source` | `"Local"` → in-solution target; `"Remote"` → deployed target. Selects the registry flag in step 2 and the `folderPath` rule below. |
| `Key` | Resource key GUID — matches the node type's `<key>` suffix. |
| `Name` | Process display name → `properties.processName`. |
| `Type` | Lowercase family (`process` / `agent` / `api` / `processOrchestration`). |
| `Folder` | Literal folder path → `properties.folderPath`. Local resources typically return `"solution_folder"`; external resources return the literal Orchestrator folder (e.g., `"Shared/Sales"`). Disambiguates same-named processes. |
| `FolderKey` | Folder GUID. Not authored — binding resolution handles folders. |

When the same `Name` repeats in one folder, pick by `Key`.

### 2. Find the tool node type

```bash
# Remote (deployed in Orchestrator):
uip maestro flow registry search "<NAME>" --output json
# Local (in-solution; run from the flow project directory):
uip maestro flow registry search "<NAME>" --local --output json
```

Pick the `Data[]` entry whose `NodeType` starts with `uipath.agent.resource.tool.` and whose `DisplayName` matches (the same search also returns the standalone `uipath.core.*` node — that is the flow-level process node, NOT an agent tool). The local registry only sees projects registered in the parent solution.

### 3. Get the manifest

```bash
uip maestro flow registry get <NODE_TYPE> [--local] --output json
```

Everything the node needs is in the manifest:

| Manifest field | Use as |
|---|---|
| `nodeType` / `version` | Instance `type` / `typeVersion`; whole manifest → `definitions[]` verbatim ([impl.md § 3](../impl.md#3-manifest-and-definitions-contract)) |
| `inputDefaults.inputSchema` / `.outputSchema` | Node `inputs.inputSchema` / `inputs.outputSchema` |
| `inputDefinition.properties` | The tool's argument names (one per-argument `inputs.<arg>` entry each) |
| `model.bindings` | Top-level `bindings[]` rows (§ Bindings) |

Optional cross-check: `uip solution resources get <KEY> --output json` returns the solution-level declaration (`Data.spec` with `inputArgumentsSchemaV2` / `outputArgumentsSchemaV2`, or raw .NET arrays for RPA) — useful when validating schemas, not required for authoring.

## Tool Node Shape

Node `inputs` (authoring surface — everything else derives):

| Field | Required | Notes |
|---|---|---|
| `source` | Yes | Lowercase UUIDv4 **you mint** ([planning.md § Identity](../planning.md#identity--mint-the-uuids-yourself)). Becomes the derived `resources/<source>/resource.json` id. |
| `name` | Yes | Tool name the LLM selects by. Name authority: `inputs.name`, fallback `display.label`. |
| `description` | Yes | What the tool does — shown to the LLM for tool selection. |
| `inputs.<arg>` | Per argument | One ValueSourceField object per argument in the manifest's `inputDefinition.properties` (§ Per-Argument Value Sources). Omit an arg ⇒ LLM-fillable with no guidance. |
| `inputSchema` / `outputSchema` | Yes | Copy from the manifest's `inputDefaults`. |
| `properties` | Yes | `{"processName": "<Name>", "folderPath": "<Folder>"}` — both from discovery step 1. **Never leave `folderPath` empty**: local → `"solution_folder"` (literal string), external → the literal Orchestrator folder. |
| `isEnabled` | No | Default `true`. |

No instance `outputs`, no instance `model` block. Hydrated legacy nodes may additionally carry `inputs.referenceKey` — leave it; do not author it for new nodes.

Example (external RPA process, one argument):

```json
{
  "id": "fibTool",
  "type": "uipath.agent.resource.tool.process.f27d0f9b-6972-47d3-8874-ec8aed8e8e16",
  "typeVersion": "1.0.0",
  "display": { "label": "FibonacciRPA" },
  "inputs": {
    "source": "9c40fd2e-58f4-45a3-93bb-0dbe38a72e10",
    "name": "FibonacciRPA",
    "description": "Computes the Fibonacci number for a given index via the deployed RPA process.",
    "index": { "mode": "prompt", "textValue": "", "promptValue": "The index of the Fibonacci number to compute", "argumentPath": "" },
    "inputSchema": { "type": "object", "properties": { "index": { "type": "number" } } },
    "outputSchema": { "type": "object", "properties": { "value": { "type": "integer" } } },
    "properties": { "processName": "FibonacciRPA", "folderPath": "Shared/uipath-agents/FibonacciRPA" }
  }
}
```

Wire exactly ONE artifact edge — agent `tool` handle → tool node `input`:

```json
{ "id": "e_agent_tool", "sourceNodeId": "disputeAnalyst", "sourcePort": "tool", "targetNodeId": "fibTool", "targetPort": "input" }
```

No sequence edges to/from a tool node — it is not on the trigger→end path.

## Per-Argument Value Sources

Each argument named in the manifest's `inputDefinition.properties` gets one `inputs.<arg>` entry: `{"mode": "...", "textValue": "", "promptValue": "", "argumentPath": ""}` — fill the field the mode reads, keep the others empty strings.

| `mode` | Arg value comes from | Field read | Derived storage |
|---|---|---|---|
| `prompt` (default) | LLM decides at run time | `promptValue` — guidance text | `inputSchema.properties.<arg>.description`; arg omitted from `argumentProperties` |
| `variable` | Flow data | `argumentPath` — raw `$vars.<nodeId>.output.<field>` ref (no `{{ }}` braces) | `argumentProperties` entry `{variant: "argument"}` |
| `text-builder` | Static text | `textValue` | `argumentProperties` entry `{variant: "static"}` |

A `variable`-mode `argumentPath` is a real `$vars` reference: it is scanned into the derived `agentInputVariables` exactly like a prompt token, and the referenced trigger field needs its `variables.globals[]` declaration ([impl.md § 4](../impl.md#4-wire-flow-data-into-prompts)). An omitted/empty argument is treated as LLM-fillable with no guidance — prefer an explicit `prompt`-mode entry with a real `promptValue`.

## Bindings

Process-family tools require **top-level `bindings[]` rows** (root of the `.flow` document, sibling of `nodes[]`) mirroring the manifest's `model.bindings` — one row per `model.bindings.values[]` entry:

```json
"bindings": [
  { "id": "b1", "name": "name", "type": "string", "resource": "process", "resourceKey": "Shared/uipath-agents/FibonacciRPA.FibonacciRPA", "propertyAttribute": "name", "default": "FibonacciRPA" },
  { "id": "b2", "name": "folderPath", "type": "string", "resource": "process", "resourceKey": "Shared/uipath-agents/FibonacciRPA.FibonacciRPA", "propertyAttribute": "folderPath", "default": "Shared/uipath-agents/FibonacciRPA" }
]
```

Copy `resource`, `resourceKey`, `propertyAttribute`, `default` verbatim from the manifest (`resourceKey` is the in-solution resource key UUID for local targets, `<folderPath>.<name>` for remote); `id` is any unique string (`b1`, `b2`, …); `type` is `"string"`. The canvas prunes `bindings[]` to live references on save — rows for a deleted tool disappear on their own.

## Derived Fields — Never Author

Projection injects these into the derived `resource.json`; they are not node inputs:

- `type` (family mapping) and `location` (`"solution"` / `"external"`)
- `argumentProperties` (built from the per-argument modes)
- `guardrail.policies` (filtered from the **agent node's** `inputs.guardrails`)
- `$resourceType`, `canvasNodeId`, `iconUrl`, `settings` defaults, `isEnabled: true` default

## Walkthrough

```bash
# 1. Identity — find the process, note Source / Key / Name / Type / Folder
uip solution resources list --source remote --kind Process --search "<NAME>" --output json
# (local: uip solution resources list --source local --output json, filter client-side)

# 2. Node type — the tool variant for that target
uip maestro flow registry search "<NAME>" --output json          # remote
# uip maestro flow registry search "<NAME>" --local --output json  # in-solution

# 3. Manifest — definitions entry + schemas + bindings template
uip maestro flow registry get <NODE_TYPE> --output json
```

Then edit the `.flow` directly (`Edit` / `Write`):

4. Add the tool node per § Tool Node Shape (mint `inputs.source`; `typeVersion` = manifest `version`).
5. Copy the manifest **verbatim** into `definitions[]`.
6. Wire the artifact edge: agent `tool` → tool `input`.
7. Add the `bindings[]` rows per § Bindings.
8. Update the agent's system prompt: name the tool, give per-tool call/stop criteria ([prompting guide](../prompting/autonomous-agent-prompting-guide.md)).

```bash
# 9. Validate
uip maestro flow format "<FILE>.flow"
uip maestro flow validate "<FILE>.flow" --output json
```

## In-Solution (Local) Targets

- The target project must already be registered in the parent solution — adding a tool never scaffolds or re-creates the target project, and never re-initializes the solution. Registration mechanics are the flow skill's solution guidance, not this capability.
- Run `registry search/get --local` from **inside the flow project directory** (the local registry scans the parent solution).
- Local manifests carry `model.projectId`; on canvas save these in-solution `definitions[]` entries keep their file-provided `inputDefinition`/`outputDefinition`/`form` while everything else is rebuilt from the live registry.
- **`inputs.properties.folderPath` is ALWAYS the literal string `"solution_folder"` for a local target — never `""`.** Do not copy the local manifest's binding `default` (often `""`) into `properties.folderPath`; the two are different fields. The `bindings[]` rows are the only place the manifest's defaults are copied verbatim (empty included).

## Gotchas

1. **Definitions-or-nothing law** ([impl.md § 3](../impl.md#3-manifest-and-definitions-contract)): a tool node without its `(type, typeVersion)`-matched `definitions[]` entry fails validate and silently vanishes from the derived agent and the package.
2. **`properties.processName` is the real process `Name`, `properties.folderPath` the real `Folder`** — both from discovery, never guessed, never empty. The display label is NOT the process name.
3. **Do not compute in the agent what the tool provides** — the system prompt must direct the agent to call the tool and use its result.
4. **The prompt names the tool by `inputs.name`** — renaming the tool means updating the prompt (and any `guardrails[].selector.matchNames` on the agent node).
5. **Tool nodes carry no prompts** — a `systemPrompt` on a resource node is meaningless; prompts live on the agent node only.
6. **Never wire a conversational agent as a tool** — conversational agents run through the UiPath Conversational Service per exchange with a threaded `messages` input; they do not match the input→output contract agent-tools require. Only autonomous agents can be tool targets (`agent` family). Applies to both in-solution and deployed targets.

## References

- [impl.md § Resource Nodes](../impl.md#7-resource-nodes) — universal recipe + kind matrix
- [impl.md § Worked Example](../impl.md#8-worked-example--trigger--agent--end--rpa-tool) — full flow with an RPA tool
- [critical-rules.md](../critical-rules.md) — mandatory constraints
- [prompting guide](../prompting/autonomous-agent-prompting-guide.md) — per-tool call/stop criteria
