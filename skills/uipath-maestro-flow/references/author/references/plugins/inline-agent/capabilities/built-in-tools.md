# Built-In Tools Capability

Pre-built agent tools that ship with the platform — file analysis, document synthesis, CSV transform. Each is a **node in the `.flow` file** wired to the agent node's `tool` handle; the full tool config lives in the tool node's `inputs`. No `resource.json` is authored — the sidecar artifact derives from the node ([impl.md § Derived Sidecar](../impl.md#10-derived-sidecar--reference)). Unlike process-family and connector tools, built-ins reference no external target: **no `bindings[]` rows, no solution-resource discovery**.

For process-family tools, see [process.md](process.md). For other kinds, [impl.md § Resource Nodes](../impl.md#7-resource-nodes).

## When to Use

- Agent must read file/attachment contents at runtime (file inputs surface metadata only) → Analyze Files
- Agent must synthesize an answer across many documents with citations → Summarize
- Agent must add LLM-computed columns to a CSV → Batch Transform

## Node Types

Fixed static types — one per tool, **no per-target key suffix** (contrast process tools):

| Node type | Display name | Does | Derived `properties.toolType` |
|---|---|---|---|
| `uipath.agent.resource.tool.builtin.analyzefiles` | Analyze Files | Extract/analyze content from files with an LLM | `analyze-attachments` |
| `uipath.agent.resource.tool.builtin.summarize` | Summarize | Synthesis across up to 1,000 pages with citations | `deep-rag` |
| `uipath.agent.resource.tool.builtin.batchtransform` | Batch transform | Process and transform CSV files | `batch-transform` |

> **Naming reconciliation.** The flow node suffix is the canvas surface; the derived sidecar's `properties.toolType` is the runtime discriminator — the mapping is asymmetric on purpose (`summarize` ⇒ `deep-rag`, the DeepRAG service). Author the node suffix; never write the kebab-case toolType anywhere in the `.flow`.

Confirm availability and get manifests:

```bash
uip maestro flow registry search "uipath.agent.resource.tool.builtin" --output json
uip maestro flow registry get uipath.agent.resource.tool.builtin.<suffix> --output json
```

Copy the manifest **verbatim** into `definitions[]` ([impl.md § 3](../impl.md#3-manifest-and-definitions-contract)); instance `typeVersion` = manifest `version`.

## Identity — Two Patterns

| Tool | Manifest `model` | Identity field | Enforcement |
|---|---|---|---|
| Analyze Files | `{"source": true}` | `inputs.source` — mint a lowercase UUIDv4 | `flow validate` REQUIRES it (actionable error) |
| Summarize / Batch transform | absent | `inputs.id` — mint a lowercase UUIDv4 | Not validator-enforced; without it the derived resource id falls back to the canvas node id — always mint |

On Summarize / Batch transform, `inputs.source` is **NOT identity** — it is the optional file reference (§ per-tool tables): `""`, or a `$vars` file expression like `{{ $vars.start.output.docFile }}`. Do not put a UUID there.

## Shared Node Shape

Common `inputs` on every built-in tool node:

| Field | Required | Notes |
|---|---|---|
| identity (`source` or `id`) | Yes | § Identity above |
| `name` | Yes | Tool name the LLM selects by. Name authority: `inputs.name`, fallback `display.label`. |
| `description` | Yes | What the tool does — shown to the LLM for tool selection. Manifest `inputDefaults.description` is a usable base; sharpen to the use case. |
| `isEnabled` | No | Default `true`. |

Wire exactly ONE artifact edge — agent `tool` → tool node `input`:

```json
{ "id": "e_tool", "sourceNodeId": "docAgent", "sourcePort": "tool", "targetNodeId": "analyzeFiles", "targetPort": "input" }
```

No sequence edges to/from a tool node. No instance `outputs`, no instance `model` block, no `bindings[]`.

`query` fields below are ValueSourceField objects `{"mode": "...", "textValue": "", "promptValue": "", "argumentPath": ""}` — same contract as process-tool arguments ([process.md § Per-Argument Value Sources](process.md#per-argument-value-sources)): `prompt` mode fills `promptValue` (LLM decides at run time), `variable` fills `argumentPath` (raw `$vars.*` ref), `text-builder` fills `textValue`.

## Analyze Files (`…builtin.analyzefiles`)

The only way an agent reads attachment contents at runtime — pair with a file-typed flow input; reference the file in the user prompt for metadata, and the agent calls the tool to read contents.

| `inputs` field | Notes |
|---|---|
| `source` | Identity UUID (validator-required). |
| `attachmentsDescription` | Description of the attachments array the LLM fills at call time. Default: manifest `inputDefaults`. |
| `itemsDescription` | Pre-wired file references: `[]` (LLM passes attachments per call — the common case), or entries `{"label": "<name>", "value": "<$vars file ref>"}` binding specific flow files. |
| `analysisTaskDescription` | Guidance for the per-call task/question the LLM supplies. |
| `exampleCalls` | `[]` — simulation-only; populate only for Studio Web simulation testing. |

```json
{
  "id": "analyzeFiles",
  "type": "uipath.agent.resource.tool.builtin.analyzefiles",
  "typeVersion": "1.1",
  "display": { "label": "AnalyzeUploadedFiles" },
  "inputs": {
    "source": "3f2a9c1e-7b4d-4e8a-9c5f-1d2e3a4b5c6d",
    "name": "AnalyzeUploadedFiles",
    "description": "Analyze one or more files with an LLM to extract, synthesize, or answer queries about their content.",
    "attachmentsDescription": "Array of files, documents, images, or other attachments to process",
    "itemsDescription": [],
    "analysisTaskDescription": "The task, question, or instruction for processing the files (e.g., 'summarize this document', 'extract key points')",
    "exampleCalls": []
  }
}
```

## Summarize (`…builtin.summarize`)

DeepRAG: comprehensive synthesis across up to 1,000 pages with citations. Heavier than Analyze Files — use for research across a document set, not single-file Q&A.

| `inputs` field | Notes |
|---|---|
| `id` | Identity UUID (mint). |
| `source` | File reference: `""` or `{{ $vars.<nodeId>.output.<fileField> }}`. |
| `query` | ValueSourceField — the research task. Typical: `mode: "prompt"` with a real `promptValue` ("what to research, what to synthesize, how to cite"). |
| `fileExtension` | `{"value": "pdf"}` or `{"value": "txt"}`. |
| `citationMode` | `{"value": "inline"}` (citations on) or `{"value": "skip"}`. Applies to pdf. |

```json
{
  "id": "researchDocs",
  "type": "uipath.agent.resource.tool.builtin.summarize",
  "typeVersion": "1.1",
  "display": { "label": "ResearchDocuments" },
  "inputs": {
    "id": "8e1b2d3c-4a5f-4b6e-8d7c-9a0b1c2d3e4f",
    "name": "ResearchDocuments",
    "description": "Synthesize an answer across the uploaded documents, with inline citations.",
    "source": "",
    "query": { "mode": "prompt", "textValue": "", "promptValue": "The research question to answer across the documents; cite sources.", "argumentPath": "" },
    "fileExtension": { "value": "pdf" },
    "citationMode": { "value": "inline" }
  }
}
```

## Batch Transform (`…builtin.batchtransform`)

Per-row LLM transform over a CSV: adds the declared output columns to every row.

| `inputs` field | Notes |
|---|---|
| `id` | Identity UUID (mint). |
| `source` | CSV file reference: `""` or a `$vars` file expression. |
| `query` | ValueSourceField — the per-row task. |
| `outputColumns` | `[{"name", "description"}]`, **min 1 — validator-enforced** (`SCHEMA_ERROR` on `[]`), max 10. `description` is the per-column LLM instruction — a prompt fragment, not a label (§ Output Column Descriptions). |
| `webSearchGrounding` | `{"value": "enabled"}` or `{"value": "disabled"}`. Disable unless rows need fresh external data. |

```json
{
  "id": "enrichCsv",
  "type": "uipath.agent.resource.tool.builtin.batchtransform",
  "typeVersion": "1.1",
  "display": { "label": "EnrichCsv" },
  "inputs": {
    "id": "5c6d7e8f-9a0b-4c1d-8e2f-3a4b5c6d7e8f",
    "name": "EnrichCsv",
    "description": "Add the MCC Code and Confidence columns to each row of the expense CSV.",
    "source": "",
    "query": { "mode": "prompt", "textValue": "", "promptValue": "For each row, populate the output columns from the row data.", "argumentPath": "" },
    "outputColumns": [
      { "name": "MCC Code", "description": "Return the 4-digit MCC code for this row. Output only the 4-digit string, e.g. 5411; output 0000 if undeterminable." },
      { "name": "Confidence", "description": "Confidence the MCC Code is correct. Output exactly one of: HIGH, MEDIUM, or LOW." }
    ],
    "webSearchGrounding": { "value": "disabled" }
  }
}
```

### Output Column Descriptions

Each `description` is the per-column LLM instruction.

| Bad | Better |
|---|---|
| `"category"` | `"Return the 4-digit MCC code, or UNKNOWN if uncertain. Output only the code."` |
| `"verified"` | `"YES if the address matches the master list (whitespace, abbreviations OK); NO if it does not; UNKNOWN if undeterminable. Output only YES, NO, or UNKNOWN."` |

## Derived Fields — Never Author

Projection injects these into the derived `resource.json`; they are not node inputs:

- `type: "internal"`, `location: "solution"`, `$resourceType: "tool"`
- `properties.toolType` (node-suffix → runtime discriminator mapping above) and `properties.settings` (per-tool wire restructure: `contextType`, `folderPathPrefix`, wire-form `query`)
- `argumentProperties` (built from a `$vars` file expression in `source`)
- `guardrail.policies` (filtered from the **agent node's** `inputs.guardrails`), `referenceKey`, `iconUrl`, `canvasNodeId`

## Walkthrough

```bash
# 1. Node type + availability (no solution-resource discovery — builtins are not solution resources)
uip maestro flow registry search "uipath.agent.resource.tool.builtin" --output json

# 2. Manifest — definitions entry + inputDefaults
uip maestro flow registry get uipath.agent.resource.tool.builtin.<suffix> --output json
```

Then edit the `.flow` directly (`Edit` / `Write`):

3. Add the tool node per the tool's section above (mint the identity UUID; `typeVersion` = manifest `version`).
4. Copy the manifest **verbatim** into `definitions[]`.
5. Wire the artifact edge: agent `tool` → tool `input`.
6. Update the agent's system prompt: name the tool, give call/stop criteria ([prompting guide](../prompting/autonomous-agent-prompting-guide.md)) — without explicit guidance the agent under-uses the tool or calls it for tasks that don't need it.

```bash
# 7. Validate
uip maestro flow format "<FILE>.flow"
uip maestro flow validate "<FILE>.flow" --output json
```

## Gotchas

1. **Definitions-or-nothing law** ([impl.md § 3](../impl.md#3-manifest-and-definitions-contract)): a tool node without its `(type, typeVersion)`-matched `definitions[]` entry fails validate and silently vanishes from the derived agent and the package.
2. **Identity asymmetry** (§ Identity): `source` UUID on Analyze Files; `id` UUID on Summarize / Batch transform, whose `source` is a file reference. Putting the UUID in the wrong field breaks derived identity.
3. **File inputs surface metadata only.** A file-typed flow input referenced in a prompt gives the agent name/type metadata — contents are readable only through Analyze Files. Without the tool node, the agent cannot read any file.
4. **No `bindings[]`, no `uip solution resources` discovery** — built-ins are platform capabilities, not deployed targets. Do not copy the process-tool recipe's binding steps.
5. **The prompt names the tool by `inputs.name`** — renaming the tool means updating the prompt (and any `guardrails[].selector.matchNames` on the agent node).
6. **Runtime test path**: built-in tools cannot be exercised through `uip maestro flow debug` on a flow-only agent (roadmap M0 CLI gap) nor supplied attachments via CLI — test from Studio Web.

## References

- [impl.md § Resource Nodes](../impl.md#7-resource-nodes) — universal recipe + kind matrix
- [process.md](process.md) — process-family tools (per-argument ValueSourceField contract)
- [critical-rules.md](../critical-rules.md) — mandatory constraints
- [prompting guide](../prompting/autonomous-agent-prompting-guide.md) — per-tool call/stop criteria
