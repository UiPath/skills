# Built-In Tools Capability

Built-in tools are pre-built agent tools that ship with the platform. They share a wire shape (`$resourceType: "tool"`, `type: "internal"`) and a fixed input/output schema per tool. Unlike process or Integration Service tools, built-in tools are self-contained at the agent level — no solution-level files, no `uip solution resources refresh`.

For process tools (RPA / agent / API / agentic), see [../process/process.md](../process/process.md). For Integration Service tools, see [../integration-service/integration-service.md](../integration-service/integration-service.md).

## When to Use

- Agent must research answers across long or multiple documents it receives at run time, with citations (questionnaires, policies, reports) → pair a `job-attachment` array input with `deep-rag` ([deeprag/planning.md](deeprag/planning.md))
- Agent needs a one-shot summary, classification or extraction from a short file at run time → pair a `job-attachment` input field with `analyze-attachments`
- Inline agent in a Flow needs to call a public web API with no connection → `http-request` (inline agents only — never on a standalone agent)
- Agent needs a platform capability that ships pre-built and does not require deployment

When the documents are long, numerous, or the answers must cite where they came from, use `deep-rag`, not `analyze-attachments`: it handles larger files and returns citations, while `analyze-attachments` is a single synthesis pass with lower page limits. Enable only one of the two for the same documents.

## Critical Rules

1. **Built-in tools are not implicit.** Add them as `resources/{Name}/resource.json` with `type: "internal"` to make them callable. Without the resource file, the tool is unavailable.
2. **`properties.toolType` is the discriminator** — fixed per built-in, kebab-lowercase. Copy from the per-tool walkthrough; do not invent.
3. **No solution-level files.** Built-in tools need no `uip solution resources refresh`. Validate the agent and bundle.
4. **Input/output schemas are canonical.** Copy them from the tool's walkthrough and change only what that walkthrough allows.
5. **Inline agents need the flow node too.** When the built-in tool is on an *inline* agent (embedded in a flow), authoring the `resource.json` is **not enough** — also wire the tool's flow node (`uipath.agent.resource.tool.builtin.<name>`, exact type in [§ Tool Registry](#tool-registry) — the suffix is not the `toolType`) to the autonomous node's `tool` handle. Fetch the node manifest with `uip maestro flow registry get` and hand the node + edge authoring to the `uipath-maestro-flow` skill ([Critical Rule 15](../../critical-rules/critical-rules.md)). Without the flow node the tool is never reachable at runtime. HTTP Request in a Builder-SDK Flow project (`.flow.ts`) is declared in the flow source, not authored here — [http-request.md § Authoring](http-request.md#authoring). See [../inline-in-flow/inline-in-flow.md](../inline-in-flow/inline-in-flow.md).

## Resource Shape

```jsonc
{
  "$resourceType": "tool",
  "id": "<UUID>",
  "referenceKey": null,
  "name": "<DisplayName>",
  "type": "internal",
  "description": "<TOOL_DESCRIPTION>",
  "isEnabled": true,
  "inputSchema":  { /* canonical per tool */ },
  "outputSchema": { /* canonical per tool */ },
  "settings": {},
  "guardrail": { "policies": [] },
  "argumentProperties": {},     // see § Argument Sources
  "properties": {
    "toolType": "<kebab-lowercase-id>"
  }
}
```

| Field | Notes |
|---|---|
| `type` | Always `"internal"` for built-in tools |
| `properties.toolType` | Fixed discriminator (e.g. `"analyze-attachments"`) |
| `inputSchema` / `outputSchema` | Canonical per tool — copy from walkthrough |
| `argumentProperties` | `{}` unless an argument is pinned — [§ Argument Sources](#argument-sources-argumentproperties) |
| `referenceKey` | Always `null` (no Orchestrator binding) |
| `guardrail.policies` | Always `[]` — required for backward compatibility |
| `id` | Fresh UUID per resource — see [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) Anti-pattern 9 |

## Argument Sources (`argumentProperties`)

The model fills every tool argument unless `argumentProperties` pins it. Keys are JSONPath into the tool input: `$['<ARGUMENT>']`.

| `variant` | Entry | Effect |
|---|---|---|
| *(no entry)* | — | Model fills the argument on each call, guided by its `description` in `inputSchema` |
| `static` | `{ "variant": "static", "value": <VALUE>, "isSensitive": false }` | Fixed value. `<VALUE>` has the argument's JSON type (string, number, array, object) |
| `argument` | `{ "variant": "argument", "argumentPath": "$['<AGENT_INPUT_FIELD>']", "isSensitive": false }` | Value read from the agent's input at run time. The field must exist in `agent.json` → `inputSchema` |

1. **`isSensitive` is required** on `static` and `argument` entries. `uip agent validate` does not check it; an entry without it stops the agent from loading at run time.
2. **`isSensitive: true` only hides a pinned value from the model.** The value is still plain text in `resource.json` — never pin a secret.
3. **`uip agent validate` does not check keys or paths.** A misspelled key pins nothing; an `argument` entry whose agent input is absent at run time leaves the argument to the model.

Worked example: [http-request.md § Pin Arguments](http-request.md#pin-arguments).

## Lifecycle

1. **Author** the agent-level `resources/{ToolName}/resource.json` with the canonical shape from the per-tool walkthrough.
2. **Refresh** with `uip agent refresh "<AGENT_NAME>" --output json` — regenerates `entry-points.json` and `bindings_v2.json`.
3. **Validate** with `uip agent validate "<AGENT_NAME>" --output json` (read-only check).
4. **Bundle and upload** the solution. No solution-resource refresh needed.

## Tool Registry

| Tool | `toolType` | Flow node (inline agents) | Walkthrough |
|---|---|---|---|
| Analyze Files | `analyze-attachments` | `uipath.agent.resource.tool.builtin.analyzefiles` | [analyze-attachments.md](analyze-attachments.md) |
| Create File | `create-file` | `uipath.agent.resource.tool.builtin.createfile` | [create-file.md](create-file.md) |
| Deep RAG | `deep-rag` | `uipath.agent.resource.tool.builtin.summarize` | [deeprag/impl-json.md](deeprag/impl-json.md) |
| Batch Transform | `batch-transform` | `uipath.agent.resource.tool.builtin.batchtransform` | [batch-transform/impl-json.md](batch-transform/impl-json.md) |
| HTTP Request — inline agents only | `http-request` | `uipath.agent.resource.tool.builtin.httprequest` | [http-request.md](http-request.md) |

## Gotchas

- See [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) Critical Rules 17–20 and Anti-pattern 20 for the canonical rule list.
- Pairing with file inputs: a `job-attachment` field renders metadata only in `{{input.<field>}}`. The agent reads contents only by calling a file-handling built-in tool. See [../../agent-definition.md](../../agent-definition.md) § File Attachments.

## References

- [analyze-attachments.md](analyze-attachments.md) — Analyze Files walkthrough
- [create-file.md](create-file.md) — Create File walkthrough
- [http-request.md](http-request.md) — HTTP Request walkthrough
- [../../agent-definition.md](../../agent-definition.md) § File Attachments — `job-attachment` schema
- [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) — canonical rules
