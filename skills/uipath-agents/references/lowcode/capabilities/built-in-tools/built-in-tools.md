# Built-In Tools Capability

Built-in tools are pre-built agent tools that ship with the platform. They share a wire shape (`$resourceType: "tool"`, `type: "internal"`) and a fixed input/output schema per tool. Unlike process or Integration Service tools, built-in tools are self-contained at the agent level — no solution-level files, no `uip solution resource refresh`.

For process tools (RPA / agent / API / agentic), see [../process/process.md](../process/process.md). For Integration Service tools, see [../integration-service/integration-service.md](../integration-service/integration-service.md).

## When to Use

- Agent needs file content analysis at runtime → pair a `job-attachment` input field with `analyze-attachments`
- Agent needs a platform capability that ships pre-built and does not require deployment

## Critical Rules

1. **Built-in tools are not implicit.** Add them as `resources/{Name}/resource.json` with `type: "internal"` to make them callable. Without the resource file, the tool is unavailable.
2. **`properties.toolType` is the discriminator** — fixed per built-in, kebab-lowercase. Copy from the per-tool walkthrough; do not invent.
3. **No solution-level files.** Built-in tools need no `uip solution resource refresh`. Validate the agent and bundle.
4. **Input/output schemas are fixed.** Do not edit them. Each tool's walkthrough lists the canonical schema.

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
  "inputSchema":  { /* fixed per tool */ },
  "outputSchema": { /* fixed per tool */ },
  "settings": {},
  "guardrail": { "policies": [] },
  "argumentProperties": {},
  "properties": {
    "toolType": "<kebab-lowercase-id>"
  }
}
```

| Field | Notes |
|---|---|
| `type` | Always `"internal"` for built-in tools |
| `properties.toolType` | Fixed discriminator (e.g. `"analyze-attachments"`) |
| `inputSchema` / `outputSchema` | Fixed per tool — copy from walkthrough |
| `referenceKey` | Always `null` (no Orchestrator binding) |
| `guardrail.policies` | Always `[]` — required for backward compatibility |
| `id` | Fresh UUID per resource — see [../../critical-rules.md](../../critical-rules.md) Anti-pattern 9 |

## Lifecycle

1. **Author** the agent-level `resources/{ToolName}/resource.json` with the canonical shape from the per-tool walkthrough.
2. **Validate** with `uip agent validate "<AGENT_NAME>" --output json`.
3. **Bundle and upload** the solution. No solution-resource refresh needed.

## Tool Registry

| Tool | `toolType` | Walkthrough |
|---|---|---|
| Analyze Files | `analyze-attachments` | [analyze-attachments.md](analyze-attachments.md) |

> Other built-in tools exist on the platform (e.g. Batch Transform, Deep RAG) but are out of scope for this reference. Add them as siblings here when in scope.

## Gotchas

- See [../../critical-rules.md](../../critical-rules.md) Critical Rules 18–21 and Anti-patterns 21–22 for the canonical rule list.
- Pairing with file inputs: a `job-attachment` field renders metadata only in `{{input.<field>}}`. The agent reads contents only by calling a file-handling built-in tool. See [../../agent-definition.md](../../agent-definition.md) § File Attachments.
- Runtime test path: built-in tools cannot be exercised end-to-end through the `uip` CLI. Test from Studio Web or via Orchestrator job invocation.

## References

- [analyze-attachments.md](analyze-attachments.md) — Analyze Files walkthrough
- [../../agent-definition.md](../../agent-definition.md) § File Attachments — `job-attachment` schema
- [../../critical-rules.md](../../critical-rules.md) — canonical rules
