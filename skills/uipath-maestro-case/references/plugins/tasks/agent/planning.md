# agent task — Planning

An AI agent task. Invokes a UiPath Agent by entityKey for reasoning, classification, extraction, or generative work.

## When to Use

Pick this plugin when the sdd.md describes a task as `AGENT` — an AI agent that processes inputs and returns structured outputs. Use when the task requires reasoning or judgment rather than deterministic automation.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | Agent Reference "Name" | Shown in the UI |
| `name` | Agent Reference "Name" | CLI flag `--name` |
| `folder-path` | Agent Reference "Folder" | CLI flag `--folder-path` |
| `task-type-id` | Registry resolution (below) | CLI flag `--task-type-id`, enables enrichment |
| `element-id` | (optional) | Required only when the agent has multiple element bindings |
| `inputs` | sdd.md task data mapping | See [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | Discovered via `tasks describe` | For downstream cross-task references |
| `runOnlyOnce` | sdd.md (default `true`) | CLI flag `--should-run-only-once` |
| `isRequired` | sdd.md (default `true`) | CLI flag `--is-required` |

## Registry Resolution

1. **Primary cache file:** `agent-index.json`.
2. **Identifier field:** `entityKey`.
3. **Cross-type fallback.** Agents are occasionally registered in `processOrchestration-index.json` when wrapped in an agentic process — search both if the primary yields no match.
4. **Match priority:** exact name + exact folder > exact name only.
5. **Discover inputs/outputs** via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md). For agents with multiple elements, also pass `--element-id` when invoking describe (see [case-commands.md § uip maestro case tasks](../../../case-commands.md)).

## Unresolved Fallback

Mark `<UNRESOLVED: agent "<name>" in folder "<folder>" not found in registry>`. Omit `inputs:` and `outputs:`; capture intended wiring in a fenced ```` ```text ```` code block (not `#` prefixed — it renders as markdown H1). Execution creates a skeleton task — see [skeleton-tasks.md](../../../skeleton-tasks.md).

## tasks.md Entry Format

```markdown
## T<n>: Add agent task "<display-name>" to "<stage>"
- taskTypeId: <entityKey>
- folder-path: "<folder>"
- inputs:
  - <input_name> <- "<Stage>"."<Task>".<output>
- outputs: <out1>, <out2>
- runOnlyOnce: true
- isRequired: true
- order: after T<m>
- lane: <n>  # FE layout coordinate; increment per task within the stage
- verify: Confirm Result: Success, capture TaskId
```
