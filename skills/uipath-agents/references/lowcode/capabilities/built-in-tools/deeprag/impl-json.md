# DeepRAG in a Low-Code Agent — Implementation

`agent.json` agents enable DeepRAG via a built-in tool resource. Same `resource.json` shape for standalone and inline-in-flow.

## Resource Shape

`resources/<ResourceName>/resource.json` — the full shape `uip agent refresh`/`validate` accept. **The folder name must exactly match the `name` field** (case- and whitespace-sensitive) or the validator fails with `folder must be named after the resource name`:

```json
{
  "$resourceType": "tool",
  "id": "<FRESH_UUID>",
  "name": "DeepRag",
  "description": "<what this deep research pass does, e.g. synthesize an answer across uploaded PDFs with citations>",
  "type": "internal",
  "inputSchema":  { "type": "object", "properties": {} },
  "outputSchema": { "type": "object", "properties": {} },
  "settings": {},
  "isEnabled": true,
  "referenceKey": null,
  "guardrail": { "policies": [] },
  "argumentProperties": {},
  "properties": {
    "toolType": "deep-rag",
    "settings": {
      "contextType": "attachments",
      "query": { "variant": "dynamic" },
      "folderPathPrefix": { "variant": "static" }
    }
  }
}
```

| Field | Constraint |
|---|---|
| `$resourceType` | `"tool"` |
| `id` | Fresh UUID-shaped string |
| `name` | Required — and the resource folder MUST be named exactly this (`missing name` if absent; `folder must be named after the resource name` if the folder differs) |
| `description` | Free text |
| `type` | `"internal"` (built-in tools) |
| `inputSchema` / `outputSchema` | Empty object schema `{ "type": "object", "properties": {} }` — deep-rag declares no I/O schema; attachments flow through at runtime |
| `settings`, `argumentProperties` | `{}` (backward-compat scaffolding) |
| `guardrail.policies` | `[]` |
| `referenceKey` | `null` (non-null identifies an external tool) |
| `isEnabled` | truthy |
| `properties.toolType` | `"deep-rag"` (others: `analyze-attachments`, `load-attachments`, `batch-transform`) |
| `properties.settings` | Tool config — see [Tool Configuration](#tool-configuration) |

Validator scans `<agent>/resources/**/resource.json`; each `resource.json`'s parent folder must equal its `name`.

> The repo's static checker asserts only `$resourceType`, `type`, `referenceKey`, `id`, `isEnabled`, and `properties.toolType`. The full shape above is what `uip agent refresh`/`validate` require — author it directly. Do not reduce it to that minimal field set, and do not treat a `refresh` schema rejection as a reason to reverse-engineer the CLI: fix the resource against this template.

## Tool Configuration

deep-rag's `inputSchema`/`outputSchema` are empty — the config lives in `properties.settings`:

| Setting | Meaning |
|---|---|
| `contextType` | `"attachments"` — documents arrive as runtime attachments |
| `query.variant` | `"dynamic"` — the research prompt is derived at runtime |
| `folderPathPrefix` | `{ "variant": "static" }` — folder scoping for the ephemeral index |

Unlike `batch-transform`, deep-rag carries no `outputColumns` and no `webSearchGrounding`. The context-index form of DeepRAG (not this tool form) instead takes `citationMode` (`"Inline"`/`"Skip"`) — see [planning.md](planning.md) § Tool resource vs context-index resource. The `properties.settings` keys are the Studio Web authoring shape; if `uip agent refresh` rejects one, verify it against your CLI version.

## Standalone vs Inline-in-Flow

**Standalone:**

```
<solution>/<AgentName>/
├── agent.json                # "type": "lowCode"
├── project.uiproj
└── resources/<any>/resource.json
```

Agent owns its tools directly. Runtime exposes `deep-rag` to the agent's tool-calling loop.

**Inline-in-flow:** flow has a `uipath.agent.autonomous` node and a built-in tool node under the `uipath.agent.resource.tool.*` prefix (canonical: `uipath.agent.resource.tool.builtin`), plus an edge from agent `tool` → tool node `input`. The shared inline-builtin-tool checker (`tests/tasks/uipath-agents/inline_builtin_tool/`) validates by prefix; verify the exact node type at your CLI version with `uip maestro flow registry search "uipath.agent.resource.tool" --output json`.

```text
[uipath.agent.autonomous] --tool--> [uipath.agent.resource.tool.builtin]
```

## Authoring the System Prompt

The agent's instructions determine effectiveness. Cover:

- When to call `deep-rag` (e.g., "When the user asks to summarize or research uploaded documents")
- What to pass as `prompt` (e.g., "Pass the user's question verbatim; ask for citations when sources matter")
- How to combine results (e.g., "Treat tool output as ground truth; do not paraphrase citations")

Without explicit guidance, the agent under-uses DeepRAG or invokes it for tasks that don't need it.

## Attachment Ingress

Studio Web forwards conversation attachments to the tool — no schema wiring. Other channels (flow input, Action Center task): confirm the runtime forwards attachments or the tool runs against an empty set.

## Validation

| Check | How |
|---|---|
| Agent project shape (agent.json, resources, bindings) | `uip agent validate --output json` (canonical; run `uip agent refresh` first to regenerate `entry-points.json` and `bindings_v2.json`) |
| Smoke run | `uip solution upload . --output json`, invoke from Studio Web with a test PDF/TXT attachment |

The repo's coder-eval suite uses a shared static checker at `tests/tasks/uipath-agents/builtin_tool/check_builtin_tool.py` covering all four `toolType` values (`analyze-attachments`, `load-attachments`, `deep-rag`, `batch-transform`). It is shared test tooling, not a runtime requirement for this skill.

## Pack and Publish

```bash
uip solution upload . --output json
```

## Resources

- Agent project validator: `uip agent validate --output json`
- API endpoints (debug): [api-reference.md](api-reference.md)
