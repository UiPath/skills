# BatchTransform in a Low-Code Agent — Implementation

`agent.json` agents enable BatchTransform via a built-in tool resource. Same `resource.json` shape for standalone and inline-in-flow.

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
    "toolType": "batch-transform"
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
| `properties.toolType` | `"batch-transform"` (others: `analyze-attachments`, `load-attachments`, `deep-rag`) |

Resource directory name is free-form. Validator scans `<agent>/resources/**/resource.json`.

## Tool Configuration

`resource.json` only registers the tool's existence — it does NOT carry per-call inputs (prompt, output columns, destination, web grounding). Those are derived at runtime from the agent's instructions and tool-call output.

What the agent must produce at invocation time (the runtime forwards these to the underlying API):

- A non-empty top-level prompt
- A list of `BatchTransformOutputColumn` entries (`name` 1–500 chars, regex `^[\w\s\.,!?-]+$`; `description` 1–20000 chars, the per-column LLM instruction)
- An output destination
- Whether to enable web grounding

The exact JSON field names the runtime sends to the platform (e.g., `useWebSearchGrounding`, `targetFileGlobPattern`) are SDK-version-specific — see the SDK source `uipath/platform/context_grounding/_context_grounding_service.py` (`_batch_transform_*_creation_spec` methods) for the body shape your version emits. Authoring the agent's system prompt (next section) is what shapes the runtime call, not editing `resource.json`.

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
| Agent project shape (agent.json, resources, bindings) | `uip agent validate --output json` (canonical; auto-runs migrations + writes `.agent-builder/`) |
| Smoke run | `uip solution upload . --output json`, invoke from Studio Web with a 10–20 row CSV before the full workload |

The repo's coder-eval suite uses a shared static checker at `tests/tasks/uipath-agents/builtin_tool/check_builtin_tool.py` covering all four `toolType` values (`analyze-attachments`, `load-attachments`, `deep-rag`, `batch-transform`). It is shared test tooling, not a runtime requirement for this skill.

## Pack and Publish

```bash
uip solution upload . --output json
```

## Resources

- Agent project validator: `uip agent validate --output json`
- API endpoints (debug): [api-reference.md](api-reference.md)
