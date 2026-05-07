# DeepRAG in a Low-Code Agent — Implementation

`agent.json` agents enable DeepRAG via a built-in tool resource. Same `resource.json` shape for standalone and inline-in-flow.

## Resource Shape

`resources/<resource-name>/resource.json`:

```json
{
  "$resourceType": "tool",
  "id": "<UUID>",
  "type": "internal",
  "referenceKey": null,
  "isEnabled": true,
  "properties": {
    "toolType": "deep-rag"
  }
}
```

| Field | Constraint |
|---|---|
| `$resourceType` | `"tool"` |
| `id` | UUID-shaped string |
| `type` | `"internal"` (built-in tools) |
| `referenceKey` | `null` (non-null identifies an external tool) |
| `isEnabled` | truthy |
| `properties.toolType` | `"deep-rag"` (others: `analyze-attachments`, `load-attachments`, `batch-transform`) |

Resource directory name is free-form. Validator scans `<agent>/resources/**/resource.json`.

## Standalone vs Inline-in-Flow

**Standalone:**

```
<solution>/<AgentName>/
├── agent.json                # "type": "lowCode"
├── project.uiproj
└── resources/<any>/resource.json
```

Agent owns its tools directly. Runtime exposes `deep-rag` to the agent's tool-calling loop.

**Inline-in-flow:** flow has `uipath.agent.autonomous` and `uipath.agent.resource.tool.deep-rag` nodes, plus an edge from agent `tool` → tool node `input`.

```text
[uipath.agent.autonomous] --tool--> [uipath.agent.resource.tool.deep-rag]
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
| Resource shape | `python tests/tasks/uipath-agents/builtin_tool/check_builtin_tool.py` (or inline equivalent) |
| Solution validation | `uip solution project validate` |
| Smoke run | `uip solution upload`, invoke from Studio Web with a test PDF/TXT attachment |

## Pack and Publish

```bash
uip solution upload . --output json
```

## Resources

- Built-in tool registry / validator: `tests/tasks/uipath-agents/builtin_tool/`
- API endpoints (debug): [api-reference.md](api-reference.md)
