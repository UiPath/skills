# Context Index Capability (Context Grounding RAG)

Context resources feed retrievable knowledge into the agent at runtime — the agent issues queries against an ECS Context Grounding index and gets back relevant chunks (RAG). The context is a **node in the `.flow` file** wired to the agent node's `context` handle; the full config lives in the context node's `inputs`. No `resource.json` is authored — the sidecar artifact derives from the node ([impl.md § Derived Sidecar](../impl.md#10-derived-sidecar--reference)).

This capability covers the **index** context variant — the only context kind the flow registry mints node types for. Other standalone-agent context variants (runtime attachments, Data Fabric entity sets) have no inline node type.

> **File-as-input ≠ context.** Agent should read a file passed as flow data (no semantic retrieval) → use the Analyze Files built-in tool ([built-in-tools.md](built-in-tools.md)), not a context index.

## When to Use

- Agent needs to retrieve from a knowledge base of indexed documents (RAG / semantic search)
- The index **already exists** in Context Grounding — indexes always live in the tenant, external to the solution. Creating or managing indexes is outside this capability (Orchestrator / Context Grounding administration).

## Node Type

Node type pattern: `uipath.agent.resource.context.index.<name>.<id>` — `<name>` is a slug of the index display name, `<id>` the ECS index GUID. **Never construct the type string by hand — discover it** (§ Discovery); the registry mints one node type per index in the tenant.

## Discovery

Two `uip` calls — node type from `registry search`, manifest (identity + defaults + definition) from `registry get`.

### 1. Find the context node type

```bash
uip maestro flow registry search "<INDEX_NAME>" --output json
```

Pick the `Data[]` entry whose `NodeType` starts with `uipath.agent.resource.context.index.` and whose `DisplayName` matches. Optional identity cross-check (index GUID = the node type's `<id>` suffix; `Folder` = the manifest's `folderPath`):

```bash
uip solution resources list --kind Index --source remote --search "<INDEX_NAME>" --output json
```

### 2. Get the manifest

```bash
uip maestro flow registry get <NODE_TYPE> --output json
```

Everything the node needs is in the manifest:

| Manifest field | Use as |
|---|---|
| `nodeType` / `version` | Instance `type` / `typeVersion`; whole manifest → `definitions[]` verbatim ([impl.md § 3](../impl.md#3-manifest-and-definitions-contract)) |
| `inputDefaults` | The starting `inputs` — **tenant identity baked in** (`indexId`, `indexName`, `folderKey`, `folderPath`) plus default settings. Copy into the node, then override settings (§ Context Node Shape). |
| `model` | `{"source": true}` — mint `inputs.source` (validator-required) |

## Context Node Shape

Node `inputs` (authoring surface — everything else derives). Start from `inputDefaults`, add identity + overrides:

| Field | Required | Notes |
|---|---|---|
| `source` | Yes | Lowercase UUIDv4 **you mint** ([planning.md § Identity](../planning.md#identity--mint-the-uuids-yourself)). Validator-enforced. Becomes the derived `resources/<source>/resource.json` id. |
| `name` | Yes | Context name the prompt refers to. **Name authority: `inputs.name` only** — projection ignores `display.label` for the derived resource name. |
| `description` | No | What the knowledge base covers. |
| `indexId` / `indexName` / `folderKey` / `folderPath` | Yes | Copy **verbatim** from `inputDefaults` — the tenant identity of the index. |
| `retrievalMode` | Yes | `semantic` (default) \| `structured` \| `deeprag` \| `batchtransform` — **all-lowercase** (§ Gotchas). |
| `query` | Yes | ValueSourceField `{"mode": "prompt"\|"text-builder"\|"variable", "textValue": "", "promptValue": "", "argumentPath": ""}` — fill the field the mode reads. `prompt` = LLM writes the query at run time (guidance in `promptValue`); `variable` = raw `$vars.<path>` ref in `argumentPath` (scanned like a prompt token — trigger-globals prerequisite applies, [impl.md § 4](../impl.md#4-wire-flow-data-into-prompts)); `text-builder` = static text in `textValue`. Validator rejects an empty value for the active mode. |
| `folderPathPrefix` | No | Same ValueSourceField shape — scope retrieval to a bucket subfolder. Default `text-builder` with empty `textValue` = no prefix. |
| `threshold` | No | Number 0–1 (validator-enforced range). Default 0. |
| `resultCount` | No | Number 1–40 (validator-enforced range). Default 3. |
| `fileExtension` | No | Plain **string** (`"All"`, `"pdf"`, `"csv"`, …) — NOT the `{value}` object built-in tools use. Per-mode legal values below. |
| `citations` | No | **String** `"enabled"` \| `"disabled"` — not a boolean. |
| `outputColumns` | `batchtransform` only | `[{"name", "description"}]` — min 1, both fields required per column (validator-enforced). Author `[]` for other modes. |
| `webSearchGrounding` | No | Object `{"value": "enabled"\|"disabled"}` — `batchtransform` web augmentation. |

No instance `outputs`, no instance `model` block, **no top-level `bindings[]` rows** (contexts bind through the definition, unlike process/connector tools).

### Per-mode requirements

| `retrievalMode` | Legal `fileExtension` | Validator additionally requires |
|---|---|---|
| `semantic` | `All`, `pdf`, `csv`, `json`, `docx`, `xlsx`, `txt` | `query` value for the active mode |
| `structured` | `csv` | `query` value |
| `deeprag` | `pdf`, `txt` | `query` value ("DeepRAG task") |
| `batchtransform` | `csv` | `query` value ("Batch transform task") + `outputColumns` min 1 |

Example (semantic retrieval over an existing tenant index):

```json
{
  "id": "productKnowledge",
  "type": "uipath.agent.resource.context.index.uipathagentsproductknowledge.de5819d5-a687-4059-988e-08dee2ae3999",
  "typeVersion": "1.0.0",
  "display": { "label": "UiPathAgentsProductKnowledge", "shape": "circle", "icon": "file-text" },
  "inputs": {
    "source": "8d1e4f6a-2b3c-4e5d-9a7f-1c0b9e8d7f6a",
    "name": "ProductKnowledge",
    "description": "Semantic retrieval over the UiPathAgentsProductKnowledge index",
    "indexId": "de5819d5-a687-4059-988e-08dee2ae3999",
    "indexName": "UiPathAgentsProductKnowledge",
    "folderKey": "040287b3-85b2-4052-a4e1-b2c14bd0c49b",
    "folderPath": "Shared/uipath-agents",
    "retrievalMode": "semantic",
    "query": { "mode": "prompt", "textValue": "", "promptValue": "The query for the Semantic strategy", "argumentPath": "" },
    "threshold": 0,
    "resultCount": 3,
    "fileExtension": "All",
    "folderPathPrefix": { "mode": "text-builder", "textValue": "", "promptValue": "", "argumentPath": "" },
    "citations": "enabled",
    "outputColumns": [],
    "webSearchGrounding": { "value": "enabled" }
  }
}
```

Wire exactly ONE artifact edge — agent `context` handle → context node `input`:

```json
{ "id": "e_agent_ctx", "sourceNodeId": "kbAgent", "sourcePort": "context", "targetNodeId": "productKnowledge", "targetPort": "input" }
```

No sequence edges to/from a context node — it is not on the trigger→end path.

## Derived Fields — Never Author

Projection restructures the flat node `inputs` into the derived `resource.json`; these are not node inputs:

- `settings` — the flat fields (`retrievalMode`, `query`, `threshold`, …) collapse into a `settings` union discriminated on `retrievalMode`
- `$resourceType: "context"`, `contextType: "index"`, `referenceKey`, `canvasNodeId`, `iconUrl`

## Walkthrough

```bash
# 1. Node type — one registry entry per tenant index
uip maestro flow registry search "<INDEX_NAME>" --output json

# 2. Manifest — identity, defaults, definitions entry
uip maestro flow registry get <NODE_TYPE> --output json
```

Then edit the `.flow` directly (`Edit` / `Write`):

3. Add the context node per § Context Node Shape (mint `inputs.source`; copy identity + defaults from the manifest's `inputDefaults`; `typeVersion` = manifest `version`).
4. Copy the manifest **verbatim** into `definitions[]`.
5. Wire the artifact edge: agent `context` → context `input`.
6. Update the agent's system prompt: name the context by `inputs.name`, ground answers in it, cap retrievals with a decide-anyway fallback ([impl.md § 2](../impl.md#2-agent-node-inputs-spec) quality obligation 2).

```bash
# 7. Validate
uip maestro flow format "<FILE>.flow"
uip maestro flow validate "<FILE>.flow" --output json
```

## Gotchas

1. **Definitions-or-nothing law** ([impl.md § 3](../impl.md#3-manifest-and-definitions-contract)): a context node without its `(type, typeVersion)`-matched `definitions[]` entry fails validate and silently vanishes from the derived agent and the package.
2. **`retrievalMode` values are all-lowercase — and the validator does NOT catch casing drift.** A camelCase `"deepRAG"` / `"batchTransform"` matches none of the schema's lowercase conditionals, silently falls into the semantic branch, and **passes validate** while misconfiguring retrieval. Same for `contextType`-style casing habits from sidecar-era docs.
3. **Copy the identity from `inputDefaults`, don't re-type it.** A bare node with only `inputs.source` passes validate (defaults fill in from the manifest) — but author the full `inputs` so the flow is self-describing and settings survive definition refreshes.
4. **Cap retrievals in the system prompt.** Wiring the index is not enough: "ground your answer" with no call limit makes the agent re-query until the runtime terminates it (`AGENT_RUNTIME.TERMINATION_MAX_ITERATIONS`, surfaced as incident `170002`). Raising `maxIterations` only moves the failure. State a cap + decide-anyway fallback ([impl.md § 2](../impl.md#2-agent-node-inputs-spec)).
5. **The prompt names the context by `inputs.name`** — renaming it means updating the prompt.
6. **Context nodes carry no prompts** — retrieval guidance lives in `query.promptValue` and the agent node's system prompt.

## References

- [impl.md § Resource Nodes](../impl.md#7-resource-nodes) — universal recipe + kind matrix
- [impl.md § Worked Example](../impl.md#8-worked-example--trigger--agent--end--rpa-tool--context) — full flow with an RPA tool + context index
- [critical-rules.md](../critical-rules.md) — mandatory constraints
- [prompting guide](../prompting/autonomous-agent-prompting-guide.md) — grounding + call/stop criteria
