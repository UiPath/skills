# Built-In Tools Capability

Built-in tools are pre-built, self-contained agent tools with wire shape `$resourceType: "tool"`, `type: "internal"`, and a fixed input/output schema. They require no solution-level files or `uip solution resources refresh`.

For process tools (RPA / agent / API / agentic), see [../process/process.md](../process/process.md). For Integration Service tools, see [../integration-service/integration-service.md](../integration-service/integration-service.md).

## When to Use

- For runtime file-content analysis, pair a `job-attachment` input field with `analyze-attachments`.
- Use built-in tools for platform capabilities that ship pre-built and require no deployment.

## Critical Rules

1. Add each built-in tool as `resources/{Name}/resource.json` with `type: "internal"`; built-in tools are not implicit.
2. Set `properties.toolType` to the fixed, kebab-lowercase discriminator from the per-tool walkthrough; do not invent it.
3. Do not create solution-level files or run `uip solution resources refresh`. Validate the agent and bundle it.
4. Do not edit fixed input/output schemas; copy the canonical schemas from the tool walkthrough.
5. For a built-in tool on an *inline* agent embedded in a flow, also wire a `uipath.agent.resource.tool.builtin.<toolType>` flow node to the autonomous node's `tool` handle. Run `uip maestro flow registry get` to fetch the node manifest, then hand node and edge authoring to the `uipath-maestro-flow` skill (Critical Rule 16). A `resource.json` alone cannot make the tool reachable at runtime. See [../inline-in-flow/inline-in-flow.md](../inline-in-flow/inline-in-flow.md).

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
| `type` | Always `"internal"` for built-in tools. |
| `properties.toolType` | Fixed discriminator (e.g. `"analyze-attachments"`). |
| `inputSchema` / `outputSchema` | Fixed per tool; copy from the walkthrough. |
| `referenceKey` | Always `null` (no Orchestrator binding). |
| `guardrail.policies` | Always `[]` (required for backward compatibility). |
| `id` | Fresh UUID per resource; see [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) Anti-pattern 9. |

## Lifecycle

1. Author `resources/{ToolName}/resource.json` with the canonical shape from the per-tool walkthrough.
2. Run `uip agent refresh "<AGENT_NAME>" --output json` to regenerate `entry-points.json` and `bindings_v2.json`.
3. Run `uip agent validate "<AGENT_NAME>" --output json` for a read-only check.
4. Bundle and upload the solution. Do not run a solution-resource refresh.

## Tool Registry

| Tool | `toolType` | Walkthrough |
|---|---|---|
| Analyze Files | `analyze-attachments` | [analyze-attachments.md](analyze-attachments.md) |
| Deep RAG | `deep-rag` | [deeprag/impl-json.md](deeprag/impl-json.md) |
| Batch Transform | `batch-transform` | [batch-transform/impl-json.md](batch-transform/impl-json.md) |

## Gotchas

- See [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) Critical Rules 17–20 and Anti-patterns 20–21 for the canonical rule list.
- A `job-attachment` field renders metadata only in `{{input.<field>}}`; the agent reads file contents only by calling a file-handling built-in tool. See [../../agent-definition.md](../../agent-definition.md) § File Attachments.
- Built-in tools cannot be tested end-to-end through the `uip` CLI. Test from Studio Web or through Orchestrator job invocation.

## References

- [analyze-attachments.md](analyze-attachments.md) — Analyze Files walkthrough
- [../../agent-definition.md](../../agent-definition.md) § File Attachments — `job-attachment` schema
- [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) — canonical rules
