# BatchTransform in a Low-Code Agent — Implementation

`agent.json` agents enable BatchTransform via a built-in tool resource. Same `resource.json` shape for standalone and inline-in-flow.

## Resource Shape

`resources/<resource-name>/resource.json` — the full shape `uip agent refresh`/`validate` accept:

```json
{
  "$resourceType": "tool",
  "id": "<FRESH_UUID>",
  "name": "BatchTransform",
  "description": "<what this batch transform does, e.g. add MCC Code and Confidence columns to each CSV row>",
  "type": "internal",
  "inputSchema":  { "type": "object", "properties": {} },
  "outputSchema": { "type": "object", "properties": {} },
  "settings": {},
  "isEnabled": true,
  "referenceKey": null,
  "guardrail": { "policies": [] },
  "argumentProperties": {},
  "properties": {
    "toolType": "batch-transform",
    "settings": {
      "contextType": "attachments",
      "query": { "variant": "dynamic" },
      "folderPathPrefix": { "variant": "static", "value": "<output-bucket-path>" },
      "outputColumns": [
        { "name": "MCC Code",   "description": "Return the 4-digit MCC code for this row. Output only the 4-digit string, e.g. 5411; output 0000 if undeterminable." },
        { "name": "Confidence", "description": "Confidence the MCC Code is correct. Output exactly one of: HIGH, MEDIUM, or LOW." }
      ],
      "webSearchGrounding": { "value": "Disabled" }
    }
  }
}
```

| Field | Constraint |
|---|---|
| `$resourceType` | `"tool"` |
| `id` | Fresh UUID-shaped string |
| `name` | Required — and the resource folder MUST be named exactly this (`resources[0].name: missing name` if absent; `folder must be named after the resource name` if the folder differs) |
| `description` | Free text |
| `type` | `"internal"` (built-in tools) |
| `inputSchema` / `outputSchema` | Empty object schema `{ "type": "object", "properties": {} }` — batch-transform declares no I/O schema; the CSV and columns flow through `properties.settings` |
| `settings`, `argumentProperties` | `{}` (backward-compat scaffolding) |
| `guardrail.policies` | `[]` |
| `referenceKey` | `null` (non-null identifies an external tool) |
| `isEnabled` | truthy |
| `properties.toolType` | `"batch-transform"` (others: `analyze-attachments`, `load-attachments`, `deep-rag`) |
| `properties.settings` | Tool config — see [Tool Configuration](#tool-configuration) |

Validator scans `<agent>/resources/**/resource.json`; each `resource.json`'s parent folder must equal its `name`.

> The repo's static checker asserts only `$resourceType`, `type`, `referenceKey`, `id`, `isEnabled`, and `properties.toolType`. The full shape above is what `uip agent refresh`/`validate` require — author it directly. Do not reduce it to that minimal field set, and do not treat a `refresh` schema rejection as a reason to reverse-engineer the CLI: fix the resource against this template.

## Tool Configuration

batch-transform's `inputSchema`/`outputSchema` are empty — the per-run config lives in `properties.settings`:

| Setting | Meaning |
|---|---|
| `contextType` | `"attachments"` — CSV arrives as a runtime attachment |
| `query.variant` | `"dynamic"` — per-row prompt derived at runtime |
| `folderPathPrefix` | Output destination: `{ "variant": "static", "value": "<bucket-path>" }`. Use a unique suffix per run to avoid overwrites |
| `outputColumns[]` | Per-column LLM instructions — `name` (1–500 chars, regex `^[\w\s\.,!?-]+$`) + `description` (1–20000 chars, the per-column instruction). See [Output Column Descriptions](#output-column-descriptions) |
| `webSearchGrounding.value` | `"Disabled"` by default; enable only when rows need fresh external data |

The `properties.settings` keys above are the Studio Web authoring shape. At runtime the platform receives a separate API body (e.g. `useWebSearchGrounding`, `targetFileGlobPattern`) whose names are SDK-version-specific — see `uipath/platform/context_grounding/_context_grounding_service.py` (`_batch_transform_*_creation_spec`). If `uip agent refresh` rejects a setting, verify the key against your CLI version.

## Standalone vs Inline-in-Flow

**Standalone:**

```
<solution>/<AgentName>/
├── agent.json                # "type": "lowCode"
├── project.uiproj
└── resources/<any>/resource.json
```

Agent owns its tools directly. Runtime exposes `batch-transform` to the agent's tool-calling loop.

**Inline-in-flow:** flow has a `uipath.agent.autonomous` node and a built-in tool node under the `uipath.agent.resource.tool.*` prefix (canonical: `uipath.agent.resource.tool.builtin`), plus an edge from agent `tool` → tool node `input`. The shared inline-builtin-tool checker (`tests/tasks/uipath-agents/inline_builtin_tool/`) validates by prefix; verify the exact node type at your CLI version with `uip maestro flow registry search "uipath.agent.resource.tool" --output json`.

```text
[uipath.agent.autonomous] --tool--> [uipath.agent.resource.tool.builtin]
```

## Output Column Descriptions

Each `description` is the per-column LLM instruction — prompt-fragment, not label.

| Bad | Better |
|---|---|
| `"category"` | `"Return the 4-digit MCC code, or UNKNOWN if uncertain. Output only the code."` |
| `"verified"` | `"YES if the address matches the master list (whitespace, abbreviations OK); NO if it does not; UNKNOWN if undeterminable. Output only YES, NO, or UNKNOWN."` |
| `"action"` | `"Recommend one of {CALL, EMAIL, ESCALATE, AUTO_APPROVE} from the order amount, status, and customer notes. Output only the chosen value."` |

## Attachment Ingress

Studio Web forwards the user's CSV upload to the tool — no schema wiring. Other channels (flow input, Action Center task): confirm the runtime forwards the file or the tool runs against an empty input set.

## Validation

| Check | How |
|---|---|
| Agent project shape (agent.json, resources, bindings) | `uip agent validate --output json` (canonical; run `uip agent refresh` first to regenerate `entry-points.json` and `bindings_v2.json`) |
| Smoke run | `uip solution upload . --output json`, invoke from Studio Web with a 10–20 row CSV before the full workload |

The repo's coder-eval suite uses a shared static checker at `tests/tasks/uipath-agents/builtin_tool/check_builtin_tool.py` covering all four `toolType` values (`analyze-attachments`, `load-attachments`, `deep-rag`, `batch-transform`). It is shared test tooling, not a runtime requirement for this skill.

## Pack and Publish

```bash
uip solution upload . --output json
```

## Resources

- Agent project validator: `uip agent validate --output json`
- API endpoints (debug): [api-reference.md](api-reference.md)
